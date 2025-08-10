"""
Module for checking available updates using winget.
"""
import subprocess
import logging
from typing import List, Dict, Tuple
from .utils import clean_text, parse_fixed_width_line, PackageUpdate, WingetError

logger = logging.getLogger(__name__)

def check_updates() -> Tuple[List[PackageUpdate], List[PackageUpdate], List[PackageUpdate]]:
    """Check for available winget package updates.
    
    Returns:
        Tuple containing:
        1. List of regular upgrades
        2. List of upgrades requiring explicit targeting
        3. List of packages with unknown versions
        
    Raises:
        WingetError: If there's an error running the winget command
    """
    try:
        logger.info("Running winget upgrade check command...")
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
        
        # Find main header
        main_header_index = -1
        for i, line in enumerate(lines):
            if "Name" in line and "Id" in line and "Version" in line and "Available" in line:
                main_header_index = i
                break
                
        if main_header_index == -1:
            raise WingetError("Could not find main header line")
            
        # Get column positions from header line
        header = lines[main_header_index]
        positions = [0]  # Start of Name column
        positions.append(header.index("Id"))  # Start of Id column
        positions.append(header.index("Version"))  # Start of Version column
        positions.append(header.index("Available"))  # Start of Available column
        if "Source" in header:
            positions.append(header.index("Source"))  # Start of Source column
        
        logger.debug(f"Column positions: {positions}")
        
        def parse_section(lines: List[str], start_index: int, positions: List[int]) -> List[Dict]:
            """Parse a section of upgrade entries."""
            results = []
            for line in lines[start_index + 2:]:  # Skip header and separator
                if not line.strip() or line.startswith('-') or "require explicit targeting" in line:
                    break
                    
                try:
                    values = parse_fixed_width_line(line, positions)
                    if len(values) >= 4:  # Must have at least Name, ID, Version, Available
                        # Skip summary lines
                        if "upgrades available" in values[0]:
                            continue
                            
                        package = PackageUpdate(
                            name=values[0],
                            id=values[1],
                            version=values[2],
                            available_version=values[3],
                            source=values[4] if len(values) > 4 else "",
                            is_unknown_version='<' in values[2] or 'Unknown' in values[2],
                            requires_explicit_upgrade=False
                        )
                        
                        # Skip empty packages
                        if not any([package.name, package.id, package.version, package.available_version]):
                            continue
                            
                        results.append(package)
                        logger.debug(f"Added package: {package}")
                except Exception as e:
                    logger.error(f"Error processing line '{line}': {e}")
                    continue
                    
            return results
        
        # Find the end of regular upgrades section
        regular_end = None
        for i in range(main_header_index + 2, len(lines)):  # Skip header and separator
            if not lines[i].strip() or "require explicit targeting" in lines[i]:
                regular_end = i
                break
                
        # Parse regular upgrades using only the relevant lines
        regular_section = lines[main_header_index:regular_end] if regular_end else lines[main_header_index:]
        all_upgrades = parse_section(regular_section, 0, positions)
        
        # Move packages with unknown versions to their own list
        unknown_versions = [pkg for pkg in all_upgrades if pkg.is_unknown_version]
        regular_upgrades = [pkg for pkg in all_upgrades if not pkg.is_unknown_version]
        
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
                            package = PackageUpdate(
                                name=values[0],
                                id=values[1],
                                version=values[2],
                                available_version=values[3],
                                source=values[4] if len(values) > 4 else "",
                                is_unknown_version=False,
                                requires_explicit_upgrade=True
                            )
                            if any([package.name, package.id, package.version, package.available_version]):  # Skip empty packages
                                explicit_data.append(package)
                                logger.debug(f"Added explicit package: {package}")
                    except Exception as e:
                        logger.error(f"Error processing explicit line '{line}': {e}")
                        
            explicit_upgrades = explicit_data
        
        # Log summary
        logger.info(f"Found {len(regular_upgrades)} regular upgrades")
        logger.info(f"Found {len(explicit_upgrades)} explicit upgrades")
        logger.info(f"Found {len(unknown_versions)} packages with unknown versions")
        
        return regular_upgrades, explicit_upgrades, unknown_versions
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running winget upgrade check: {e}")
        logger.error(f"stderr: {e.stderr}")
        raise WingetError(f"Failed to check updates: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error checking updates: {str(e)}")
        raise WingetError(f"Failed to check updates: {str(e)}")
