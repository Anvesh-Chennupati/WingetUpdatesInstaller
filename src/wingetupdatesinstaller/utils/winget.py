"""Winget related utilities."""
import platform
import subprocess
from typing import Tuple, List, Dict
import re
import logging

logger = logging.getLogger(__name__)

class WingetPackage:
    def __init__(self, name: str, id: str, version: str, source: str):
        self.name = name
        self.id = id
        self.version = version
        self.source = source

    @staticmethod
    def from_list_output(line: str) -> 'WingetPackage':
        """Parse a line from winget list output into a WingetPackage object."""
        # Split by at least 2 spaces to handle names with single spaces
        parts = re.split(r'\s{2,}', line.strip())
        if len(parts) >= 4:
            return WingetPackage(
                name=parts[0],
                id=parts[1],
                version=parts[2],
                source=parts[3]
            )
        elif len(parts) == 3:
            return WingetPackage(
                name=parts[0],
                id=parts[1],
                version=parts[2],
                source=""
            )
        else:
            return None

    def to_dict(self) -> Dict:
        """Convert package to dictionary for Gradio table."""
        return {
            "Name": self.name,
            "ID": self.id,
            "Version": self.version,
            "Source": self.source
        }

def check_winget() -> str:
    """Check if winget is installed and working."""
    if platform.system().lower() != "windows":
        return "Error: Winget is only available on Windows systems."
    
    try:
        result = subprocess.run(
            ["winget", "--version"], 
            capture_output=True, 
            text=True,
            check=True
        )
        return f"✅ Winget is installed and ready!\nVersion: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"❌ Error running winget: {e.stderr}"
    except FileNotFoundError:
        return "❌ Winget is not installed or not in PATH"

def get_installed_packages() -> List[Dict]:
    """Get list of installed packages.
    
    Returns:
        List[Dict]: List of packages with their details
    """
    try:
        result = subprocess.run(
            ["winget", "list"], 
            capture_output=True, 
            text=True,
            check=True
        )
        
        packages = []
        lines = result.stdout.split('\n')
        
        # Find the header line and separator line
        header_index = next((i for i, line in enumerate(lines) if "Name" in line and "Id" in line), -1)
        if header_index == -1:
            return []
            
        # Skip header and separator lines
        for line in lines[header_index + 2:]:
            if line.strip():
                package = WingetPackage.from_list_output(line)
                if package:
                    packages.append(package.to_dict())
        
        return packages
    except subprocess.CalledProcessError as e:
        logger.error(f"Error getting installed packages: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error getting installed packages: {e}")
        return []

def check_updates() -> List[Dict]:
    """Check for available updates.
    
    Returns:
        List[Dict]: List of packages with available updates
    """
    try:
        result = subprocess.run(
            ["winget", "upgrade"], 
            capture_output=True, 
            text=True,
            check=True
        )
        
        updates = []
        lines = result.stdout.split('\n')
        
        # Find the header line
        header_index = next((i for i, line in enumerate(lines) if "Name" in line and "Id" in line), -1)
        if header_index == -1:
            return []
            
        # Skip header and separator lines
        for line in lines[header_index + 2:]:
            if line.strip():
                parts = re.split(r'\s{2,}', line.strip())
                if len(parts) >= 4:
                    updates.append({
                        "Name": parts[0],
                        "ID": parts[1],
                        "Current Version": parts[2],
                        "Available Version": parts[3],
                        "Update": True  # Checkbox state
                    })
        
        return updates
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking for updates: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error checking for updates: {e}")
        return []
