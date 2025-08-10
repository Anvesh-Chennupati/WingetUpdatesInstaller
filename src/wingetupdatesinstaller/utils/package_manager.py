"""Package management utilities for WingetUpdatesInstaller."""
import json
import logging
import subprocess
import tempfile
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

def clean_text(text: str) -> str:
    """Clean text by removing special characters and normalizing spaces."""
    text = text.replace('«', '')
    text = text.replace('à', '')
    text = text.replace('...', '')
    text = text.replace('…', '')
    return ' '.join(text.split()).strip()

def parse_fixed_width_line(line: str, positions: List[int]) -> List[str]:
    """Parse a fixed width line using column positions."""
    values = []
    for i in range(len(positions)):
        start = positions[i]
        end = positions[i + 1] if i < len(positions) - 1 else len(line)
        value = clean_text(line[start:end])
        values.append(value)
    return values

def export_winget_packages() -> str:
    """Export installed packages to a JSON file using winget export.
    
    Returns:
        str: Path to the exported JSON file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = Path(tempfile.gettempdir()) / f"winget_export_{timestamp}.json"
    
    try:
        subprocess.run(
            ["winget", "export", "-o", str(export_path), "--include-versions"],
            capture_output=True,
            text=True,
            check=True
        )
        return str(export_path)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error exporting winget packages: {e.stderr}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during winget export: {str(e)}")
        return None

def parse_winget_export(export_path: str) -> Tuple[List[Dict], List[str]]:
    """Parse winget export file to get available and unavailable packages.
    
    Args:
        export_path (str): Path to the winget export JSON file
        
    Returns:
        Tuple[List[Dict], List[str]]: Tuple containing:
            1. List of available packages with their details
            2. List of package names that are not available in winget
    """
    available_packages = []
    unavailable_packages = []
    
    try:
        # Read the export file
        with open(export_path, 'r', encoding='utf-8') as f:
            export_data = json.load(f)
        
        # Extract available packages from the export
        if export_data.get("Sources"):
            for source in export_data["Sources"]:
                if source.get("Packages"):
                    for package in source["Packages"]:
                        available_packages.append({
                            "Name": package["PackageIdentifier"],
                            "ID": package["PackageIdentifier"],
                            "Version": package.get("Version", "Unknown"),
                            "Source": "winget"
                        })
        
        # Get the list of unavailable packages from winget export errors
        try:
            result = subprocess.run(
                ["winget", "export", "-o", export_path, "--include-versions"],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse stderr for unavailable package messages
            error_lines = result.stderr.split('\n') if result.stderr else []
            for line in error_lines:
                if "Installed package is not available from any source:" in line:
                    package_name = line.split(":", 1)[1].strip()
                    unavailable_packages.append(package_name)
        except Exception as e:
            logger.error(f"Error getting unavailable packages: {str(e)}")
            
        return available_packages, unavailable_packages
    except Exception as e:
        logger.error(f"Error parsing winget export: {str(e)}")
        return [], []

def parse_winget_list() -> List[Dict[str, str]]:
    """Parse winget list output with improved robustness."""
    try:
        logger.info("Running winget list command...")
        result = subprocess.run(
            ["winget", "list"], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            check=True
        )
        
        lines = [line for line in result.stdout.split('\n') if line.strip()]
        header_index = next((i for i, line in enumerate(lines) 
                           if "Name" in line and "Id" in line and "Version" in line), -1)
        
        if header_index == -1:
            logger.error("Could not find header line")
            return []
            
        # Get column positions from header line
        header = lines[header_index]
        positions = [0]  # Start of Name column
        positions.append(header.index("Id"))  # Start of Id column
        positions.append(header.index("Version"))  # Start of Version column
        positions.append(header.index("Source") if "Source" in header else len(header))
        
        logger.debug(f"Column positions: {positions}")
        
        packages = []
        for line in lines[header_index + 2:]:
            if not line.strip() or line.startswith('-'):
                continue
                
            try:
                values = parse_fixed_width_line(line, positions)
                if len(values) >= 3 and values[0] and values[1]:
                    package = {
                        "Name": values[0],
                        "ID": values[1],
                        "Version": values[2] if len(values) > 2 else "",
                        "Source": values[3] if len(values) > 3 else ""
                    }
                    packages.append(package)
            except Exception as e:
                logger.error(f"Error processing line '{line}': {e}")
                continue
        
        return packages
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running winget list: {e}")
        logger.error(f"stderr: {e.stderr}")
        return []

def get_all_packages() -> Tuple[List[Dict], List[Dict]]:
    """Get all installed packages, separating winget and non-winget packages.
    
    Returns:
        Tuple[List[Dict], List[Dict]]: Tuple containing:
            1. List of packages available in winget
            2. List of packages not available in winget
    """
    try:
        # Get packages from winget list
        all_packages = parse_winget_list()
        logger.debug(f"Got {len(all_packages)} total packages")
        
        # Separate packages based on source
        winget_packages = []
        non_winget_packages = []
        
        for pkg in all_packages:
            logger.debug(f"Processing package: {json.dumps(pkg, indent=2)}")
            if pkg.get("Source", "").lower() == "winget":
                winget_packages.append(pkg)
            else:
                non_winget_packages.append(pkg)
        
        logger.debug(f"Separated into {len(winget_packages)} winget packages and {len(non_winget_packages)} non-winget packages")
        logger.debug(f"Sample winget package: {json.dumps(winget_packages[0] if winget_packages else {}, indent=2)}")
        logger.debug(f"Sample non-winget package: {json.dumps(non_winget_packages[0] if non_winget_packages else {}, indent=2)}")
        
        # Export to JSON for backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_path = Path(tempfile.gettempdir()) / f"winget_export_{timestamp}.json"
        
        try:
            result = subprocess.run(
                ["winget", "export", "-o", str(export_path), "--include-versions"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Created winget export backup at {export_path}")
            
            # Read and log the export file contents
            with open(export_path, 'r', encoding='utf-8') as f:
                export_data = json.load(f)
                logger.debug(f"Export file contains {len(export_data.get('Sources', [{}])[0].get('Packages', []))} packages")
                
        except Exception as e:
            logger.warning(f"Failed to create winget export backup: {e}")
        
        return winget_packages, non_winget_packages
    except Exception as e:
        logger.error(f"Error getting all packages: {str(e)}")
        return [], []
