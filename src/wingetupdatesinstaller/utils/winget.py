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

def clean_text(text: str) -> str:
    """Clean text by removing special characters and normalizing spaces."""
    # Replace special characters
    text = text.replace('…', '...')  # Replace ellipsis
    text = text.replace('«', '')
    text = text.replace('à', '')
    text = text.replace('\u200b', '')  # Remove zero-width space
    # Normalize spaces and remove leading/trailing whitespace
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

def check_updates() -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Check for available updates.
    
    Returns:
        Tuple containing:
        1. List[Dict]: Regular upgrades
        2. List[Dict]: Upgrades requiring explicit targeting
        3. List[Dict]: Packages with unknown versions
    """
    try:
        result = subprocess.run(
            ["winget", "list", "--upgrade-available"], 
            capture_output=True, 
            text=True,
            encoding='utf-8',
            check=True
        )
        
        lines = result.stdout.split('\n')
        regular_upgrades = []
        explicit_upgrades = []
        unknown_versions = []
        
        # Process main upgrades section
        main_header_index = -1
        for i, line in enumerate(lines):
            if "Name" in line and "Id" in line and "Version" in line and "Available" in line:
                main_header_index = i
                break
        
        if main_header_index == -1:
            logger.error("Could not find main header line")
            return [], [], []
            
        # Get column positions from header line
        header = lines[main_header_index]
        positions = [0]  # Start of Name column
        positions.append(header.index("Id"))  # Start of Id column
        positions.append(header.index("Version"))  # Start of Version column
        positions.append(header.index("Available"))  # Start of Available column
        if "Source" in header:
            positions.append(header.index("Source"))  # Start of Source column
        
        def parse_section(lines: List[str], start_index: int, positions: List[int]) -> List[Dict]:
            """Parse a section of upgrade entries."""
            results = []
            for line in lines[start_index + 2:]:  # Skip header and separator
                if not line.strip() or line.startswith('-') or "require explicit targeting" in line:
                    break
                
                try:
                    values = parse_fixed_width_line(line, positions)
                    if len(values) >= 4:  # Must have at least Name, ID, Version, Available
                        # Skip summary lines that contain "upgrades available"
                        if "upgrades available" in values[0]:
                            continue
                            
                        package = {
                            "Name": values[0],
                            "ID": values[1],
                            "Version": values[2],
                            "Available": values[3],
                            "Source": values[4] if len(values) > 4 else "winget",
                            "Update": True  # Default to selected for update
                        }
                        
                        # Skip empty packages (where all fields are empty)
                        if not any(package.values()):
                            continue
                            
                        results.append(package)
                except Exception as e:
                    logger.error(f"Error processing line '{line}': {e}")
                    continue
            return results
            
        # Find the end of regular upgrades section
        regular_end = None
        for i in range(main_header_index + 2, len(lines)):  # Skip header and separator
            if not lines[i].strip() or "require explicit targeting" in line:
                regular_end = i
                break
                
        # Parse regular upgrades using only the relevant lines
        regular_section = lines[main_header_index:regular_end] if regular_end else lines[main_header_index:]
        all_upgrades = parse_section(regular_section, 0, positions)
        
        # Move packages with unknown versions to their own list
        unknown_versions = [pkg for pkg in all_upgrades if '<' in pkg['Version'] or 'Unknown' in pkg['Version']]
        regular_upgrades = [pkg for pkg in all_upgrades if pkg not in unknown_versions]
        
        # Find and parse explicit upgrades section
        explicit_start = None
        explicit_data = []
        in_explicit = False
        after_header = False
        explicit_positions = None
        
        # First find the start of explicit section
        for i, line in enumerate(lines):
            if "require explicit targeting" in line:
                explicit_start = i
                break
                
        if explicit_start:
            # Now collect explicit upgrades data
            for line in lines[explicit_start:]:
                if not line.strip():  # Skip empty lines
                    continue
                    
                if "Name" in line and "Id" in line and "Version" in line:
                    # Found the header, get positions and start collecting
                    explicit_positions = [0]  # Start of Name column
                    explicit_positions.append(line.index("Id"))
                    explicit_positions.append(line.index("Version"))
                    explicit_positions.append(line.index("Available"))
                    if "Source" in line:
                        explicit_positions.append(line.index("Source"))
                    in_explicit = True
                    continue
                
                if in_explicit and line.startswith('-'):  # Skip separator line
                    after_header = True
                    continue
                    
                if after_header:
                    if not line.strip() or "version numbers that cannot be determined" in line:
                        # End of explicit section
                        break
                        
                    try:
                        values = parse_fixed_width_line(line, explicit_positions)
                        if len(values) >= 4 and values[1]:  # Must have at least Name, ID, Version, Available
                            package = {
                                "Name": values[0],
                                "ID": values[1],
                                "Version": values[2],
                                "Available": values[3],
                                "Source": values[4] if len(values) > 4 else "winget",
                                "Update": False  # Default to not selected for explicit upgrades
                            }
                            if any(package.values()):  # Skip empty packages
                                explicit_data.append(package)
                    except Exception as e:
                        logger.error(f"Error processing explicit line '{line}': {e}")
                        
            explicit_upgrades = explicit_data
            
        # Log summary info
        logger.info(f"Found {len(regular_upgrades)} regular upgrades")
        logger.info(f"Found {len(explicit_upgrades)} explicit upgrades")
        logger.info(f"Found {len(unknown_versions)} packages with unknown versions")
        
        return regular_upgrades, explicit_upgrades, unknown_versions
        
        return updates
    except subprocess.CalledProcessError as e:
        logger.error(f"Error checking for updates: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error checking for updates: {e}")
        return []
