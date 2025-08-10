"""
Module for installing package updates using winget.
"""
import subprocess
import logging
from typing import List, Optional
from .utils import PackageUpdate, WingetError

logger = logging.getLogger(__name__)

def install_updates(packages: List[PackageUpdate], silent: bool = False) -> None:
    """Install updates for the specified packages.
    
    Args:
        packages: List of PackageUpdate objects to install
        silent: If True, use --silent flag for non-interactive installation
        
    Raises:
        WingetError: If there's an error installing updates
    """
    if not packages:
        logger.info("No packages to update")
        return
        
    try:
        # Build command
        cmd = ["winget", "upgrade"]
        
        # Add packages
        for pkg in packages:
            # For explicit upgrades or when version is specified, use --version
            if pkg.requires_explicit_upgrade or not pkg.is_unknown_version:
                cmd.extend(["--id", pkg.id, "--version", pkg.available_version])
            else:
                cmd.extend(["--id", pkg.id])
                
        # Add silent flag if requested
        if silent:
            cmd.append("--silent")
            
        logger.info(f"Running update command: {' '.join(cmd)}")
        
        # Run command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            check=True
        )
        
        logger.info("Updates installed successfully")
        if result.stdout:
            logger.debug(f"Update output: {result.stdout}")
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing updates: {e}")
        logger.error(f"stderr: {e.stderr}")
        raise WingetError(f"Failed to install updates: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error installing updates: {str(e)}")
        raise WingetError(f"Failed to install updates: {str(e)}")

def install_single_update(package: PackageUpdate, silent: bool = False) -> None:
    """Install update for a single package.
    
    Args:
        package: PackageUpdate object to install
        silent: If True, use --silent flag for non-interactive installation
        
    Raises:
        WingetError: If there's an error installing the update
    """
    install_updates([package], silent)
