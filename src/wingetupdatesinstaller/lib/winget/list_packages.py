"""
Module for listing installed packages using winget.
"""
import subprocess
import logging
from typing import List, Dict, Any
from .utils import clean_text, parse_fixed_width_line, Package, WingetError

logger = logging.getLogger(__name__)

def list_packages() -> List[Package]:
    """List installed packages using winget.
    
    Returns:
        List of Package objects representing installed packages.
        
    Raises:
        WingetError: If there's an error running the winget command
    """
    try:
        result = subprocess.run(
            ["winget", "list"], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            check=True
        )
        
        lines = result.stdout.split('\n')
        packages = []
        
        # Find the header line
        header_index = -1
        for i, line in enumerate(lines):
            if "Name" in line and "Id" in line and "Version" in line:
                header_index = i
                break
                
        if header_index == -1:
            raise WingetError("Could not find header line")
            
        # Get column positions
        header = lines[header_index]
        positions = [0]  # Start of Name column
        positions.append(header.index("Id"))  # Start of Id column
        positions.append(header.index("Version"))  # Start of Version column
        positions.append(header.index("Source") if "Source" in header else len(header))  # Start of Source column or end of line
        
        # Skip the separator line
        start_index = header_index + 2
        for line in lines[header_index + 2:]:  # Skip header and separator
            if not line.strip():  # Skip empty lines
                continue
                
            try:
                values = parse_fixed_width_line(line, positions)
                if len(values) >= 3:  # Must have at least Name, ID, and Version
                    package = Package(
                        name=values[0],
                        id=values[1],
                        version=values[2],
                        source=values[3] if len(values) > 3 else ""
                    )
                    # Skip empty packages
                    if any([package.name, package.id, package.version]):
                        packages.append(package)
            except Exception as e:
                logger.error(f"Error processing line '{line}': {e}")
                continue
                
        return packages
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error listing packages: {e}")
        logger.error(f"stderr: {e.stderr}")
        raise WingetError(f"Failed to list packages: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error listing packages: {str(e)}")
        raise WingetError(f"Failed to list packages: {str(e)}")
