import gradio as gr
import logging
from typing import Dict, List, Tuple, Any
from wingetupdatesinstaller.utils import get_system_info, check_winget
from wingetupdatesinstaller.lib.winget import (
    list_packages,
    check_updates,
    install_updates,
    PackageUpdate,
    WingetError
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_package_tables():
    """Get and display installed packages."""
    logger.info("Starting package table update")
    try:
        packages = list_packages()
        logger.debug(f"Retrieved {len(packages)} packages")
        
        # Format packages for display
        winget_data = []
        non_winget_data = []
        
        for pkg in packages:
            try:
                entry = [
                    pkg.name,
                    pkg.id,
                    pkg.version,
                    pkg.source or "winget"
                ]
                
                # Add to appropriate list based on source
                if pkg.source and pkg.source.lower() != "winget":
                    non_winget_data.append(entry)
                    logger.debug(f"Added non-winget package: {entry}")
                else:
                    winget_data.append(entry)
                    logger.debug(f"Added winget package: {entry}")
                    
            except Exception as e:
                logger.error(f"Error formatting package {pkg}: {e}")
                
        return winget_data, non_winget_data
    except Exception as e:
        logger.error(f"Error updating package tables: {e}")
        gr.Error("An unexpected error occurred while updating package tables")
        return [], []

def create_app():
    """Create the Gradio application with sidebar navigation."""
    logger.info("Creating Gradio application")
    
    with gr.Blocks(title="WingetUpdatesInstaller", theme=gr.themes.Soft()) as app:
        # Create the sidebar for navigation
        with gr.Row():
            # Sidebar
            with gr.Column(scale=1):
                gr.Markdown("### Navigation")
                with gr.Row():
                    hardware_tab_btn = gr.Button("🖥️ Hardware Info", variant="primary")
                    winget_tab_btn = gr.Button("📦 Winget", variant="primary")
                
            # Main content area
            with gr.Column(scale=4):
                # Hardware Info Tab
                with gr.Tab("Hardware Info") as hardware_tab:
                    gr.Markdown("## System Information")
                    system_info_button = gr.Button("📊 Check System Details", variant="primary")
                    system_info_output = gr.Textbox(
                        label="System Information",
                        lines=15,
                        max_lines=20
                    )
                
                # Winget Tab
                with gr.Tab("Winget Manager") as winget_tab:
                    gr.Markdown("## Winget Package Manager")
                    
                    # Winget Status Section
                    with gr.Row():
                        winget_status_button = gr.Button("🔍 Check Winget Status", variant="secondary")
                        winget_status_output = gr.Textbox(
                            label="Winget Status",
                            lines=2
                        )
                    
                    # Package List Section
                    gr.Markdown("### Installed Packages")
                    with gr.Row():
                        list_packages_button = gr.Button("📋 List All Installed Packages", variant="primary")
                    
                    # Available Packages Section
                    gr.Markdown("#### Available in Winget")
                    packages_table = gr.DataFrame(
                        headers=["Name", "ID", "Version", "Source"],
                        datatype=["str", "str", "str", "str"],
                        label="Available Packages",
                        type="array"  # Explicitly set type to array
                    )
                    
                    # Unavailable Packages Section
                    gr.Markdown("#### Not Available in Winget")
                    unavailable_packages = gr.DataFrame(
                        headers=["Name", "ID", "Version", "Source"],
                        datatype=["str", "str", "str", "str"],
                        label="System Packages",
                        type="array"  # Explicitly set type to array
                    )
                    
                    # Status for updates
                    update_status = gr.Text(
                        label="Update Status",
                        show_label=True,
                        visible=False
                    )

                    # Updates Section
                    gr.Markdown("### Available Updates")
                    with gr.Row():
                        check_updates_button = gr.Button("🔄 Check for Updates", variant="primary")
                        apply_updates_button = gr.Button("✨ Apply Selected Updates", variant="secondary", visible=False)
                    
                    # Regular updates section
                    gr.Markdown("#### Standard Updates")
                    regular_updates_table = gr.DataFrame(
                        headers=["Name", "ID", "Current Version", "Available Version", "Source", "Update"],
                        datatype=["str", "str", "str", "str", "str", "bool"],
                        label="Regular Updates",
                        type="array"
                    )
                    
                    # Explicit updates section
                    gr.Markdown("#### Updates Requiring Explicit Targeting")
                    gr.Text("These packages require manual confirmation using the --id flag during update", show_label=False)
                    explicit_updates_table = gr.DataFrame(
                        headers=["Name", "ID", "Current Version", "Available Version", "Source", "Update"],
                        datatype=["str", "str", "str", "str", "str", "bool"],
                        label="Explicit Updates",
                        type="array"
                    )
                    
                    # Unknown version updates section
                    gr.Markdown("#### Updates with Unknown Versions")
                    gr.Text("These packages have versions that cannot be determined automatically", show_label=False)
                    unknown_updates_table = gr.DataFrame(
                        headers=["Name", "ID", "Current Version", "Available Version", "Source", "Update"],
                        datatype=["str", "str", "str", "str", "str", "bool"],
                        label="Unknown Version Updates",
                        type="array"
                    )
                    
                    # Define event handlers within create_app scope
                    def handle_check_updates():
                        """Handler for check updates button click."""
                        try:
                            regular, explicit, unknown = check_updates()
                            
                            # Format each type of update for display
                            regular_data = format_updates_for_display(regular)
                            explicit_data = format_updates_for_display(explicit)
                            unknown_data = format_updates_for_display(unknown)
                            
                            logger.info(f"Found {len(regular)} regular, {len(explicit)} explicit, and {len(unknown)} unknown version updates")
                            
                            # Show apply updates button if there are updates
                            if regular_data or explicit_data or unknown_data:
                                return regular_data, explicit_data, unknown_data, {"visible": True}, {"visible": True, "value": "Ready to install updates"}
                            else:
                                return [], [], [], {"visible": False}, {"visible": True, "value": "No updates available"}
                            
                        except WingetError as e:
                            gr.Warning(str(e))
                            return [], [], [], {"visible": False}, {"visible": True, "value": str(e)}
                        except Exception as e:
                            logger.error(f"Error checking for updates: {e}")
                            gr.Error("An unexpected error occurred while checking for updates")
                            return [], [], [], {"visible": False}, {"visible": True, "value": f"Error: {str(e)}"}

                    def handle_apply_updates(regular_data: List[List], explicit_data: List[List], unknown_data: List[List]) -> str:
                        """Apply selected updates from all tables."""
                        try:
                            updates_to_install = []
                            
                            # Collect selected updates from each table
                            for row in regular_data:
                                if row[5]:  # If selected
                                    updates_to_install.append(create_package_from_row(row))
                                    
                            for row in explicit_data:
                                if row[5]:  # If selected
                                    updates_to_install.append(create_package_from_row(row, is_explicit=True))
                                    
                            for row in unknown_data:
                                if row[5]:  # If selected
                                    updates_to_install.append(create_package_from_row(row, is_unknown=True))
                            
                            if not updates_to_install:
                                return "No updates selected for installation"
                                
                            # Install updates
                            logger.info(f"Installing {len(updates_to_install)} updates...")
                            install_updates(updates_to_install)
                            
                            return f"Successfully installed {len(updates_to_install)} updates"
                            
                        except WingetError as e:
                            gr.Warning(str(e))
                            return f"Error installing updates: {str(e)}"
                        except Exception as e:
                            logger.error(f"Error applying updates: {e}")
                            gr.Error("An unexpected error occurred while installing updates")
                            return f"Error installing updates: {str(e)}"

                    # Connect button events after defining handlers
                    check_updates_button.click(
                        fn=handle_check_updates,
                        outputs=[regular_updates_table, explicit_updates_table, unknown_updates_table, apply_updates_button, update_status],
                        api_name="check_updates"
                    )
                    
                    # Connect apply updates button click event
                    apply_updates_button.click(
                        fn=handle_apply_updates,
                        inputs=[regular_updates_table, explicit_updates_table, unknown_updates_table],
                        outputs=[update_status],
                        api_name="apply_updates"
                    )

        
        # Event handlers for navigation
        def set_tab(tab_name):
            return tab_name
            
        hardware_tab_btn.click(
            fn=lambda: "Hardware Info",
            outputs=hardware_tab,
            api_name="set_hardware_tab"
        )
        winget_tab_btn.click(
            fn=lambda: "Winget Manager",
            outputs=winget_tab,
            api_name="set_winget_tab"
        )
        
        # Connect functionality
        system_info_button.click(
            fn=get_system_info,
            outputs=system_info_output,
            api_name="get_system_info"
        )
        
        winget_status_button.click(
            fn=check_winget,
            outputs=winget_status_output,
            api_name="check_winget"
        )
        
        def update_package_tables():
            """Get and display installed packages."""
            logger.info("Starting package table update")
            try:
                packages = list_packages()
                logger.debug(f"Retrieved {len(packages)} packages")
                
                # Format packages for display
                winget_data = []
                non_winget_data = []
                
                for pkg in packages:
                    try:
                        entry = [
                            pkg.name,
                            pkg.id,
                            pkg.version,
                            pkg.source or "winget"
                        ]
                        
                        # Add to appropriate list based on source
                        if pkg.source and pkg.source.lower() != "winget":
                            non_winget_data.append(entry)
                            logger.debug(f"Added non-winget package: {entry}")
                        else:
                            winget_data.append(entry)
                            logger.debug(f"Added winget package: {entry}")
                            
                    except Exception as e:
                        logger.error(f"Error formatting package {pkg}: {e}")
                
                logger.debug(f"Final data sizes - Winget: {len(winget_data)}, Non-winget: {len(non_winget_data)}")
                
                return winget_data, non_winget_data
            except Exception as e:
                logger.error(f"Error in update_package_tables: {e}")
                return [], []

        list_packages_button.click(
            fn=update_package_tables,
            outputs=[packages_table, unavailable_packages],
            api_name="list_packages"
        )
        
        def format_updates_for_display(updates: List[PackageUpdate]) -> List[List]:
            """Format package updates for display in tables."""
            formatted = []
            for pkg in updates:
                try:
                    entry = [
                        pkg.name,
                        pkg.id,
                        pkg.version,
                        pkg.available_version,
                        pkg.source or "winget",
                        True  # Default to selected for update
                    ]
                    formatted.append(entry)
                except Exception as e:
                    logger.error(f"Error formatting update {pkg}: {e}")
            return formatted

        def create_package_from_row(row: List[Any], is_explicit: bool = False, is_unknown: bool = False) -> PackageUpdate:
            """Create a PackageUpdate object from a table row."""
            return PackageUpdate(
                name=str(row[0]),
                id=str(row[1]),
                version=str(row[2]),
                available_version=str(row[3]),
                source=str(row[4]),
                is_unknown_version=is_unknown,
                requires_explicit_upgrade=is_explicit
            )

        def handle_check_updates():
            """Handler for check updates button click."""
            try:
                regular, explicit, unknown = check_updates()
                
                # Format each type of update for display
                regular_data = format_updates_for_display(regular)
                explicit_data = format_updates_for_display(explicit)
                unknown_data = format_updates_for_display(unknown)
                
                logger.info(f"Found {len(regular)} regular, {len(explicit)} explicit, and {len(unknown)} unknown version updates")
                
                # Show apply updates button if there are updates
                if regular_data or explicit_data or unknown_data:
                    apply_updates_button.visible = True
                else:
                    apply_updates_button.visible = False
                
                update_status.visible = True
                update_status.value = "Found updates. Select packages to update and click 'Apply Selected Updates'."
                # Use dictionary for component updates in Gradio 3.x
                return regular_data, explicit_data, unknown_data, {"visible": True}, {"visible": True, "value": "Ready to install updates"}
                
            except WingetError as e:
                gr.Warning(str(e))
                return [], [], [], {"visible": False}, {"visible": True, "value": str(e)}
            except Exception as e:
                logger.error(f"Error checking for updates: {e}")
                gr.Error("An unexpected error occurred while checking for updates")
                return [], [], [], {"visible": False}, {"visible": True, "value": f"Error: {str(e)}"}
                
        def handle_apply_updates(regular_data: List[List], explicit_data: List[List], unknown_data: List[List]) -> str:
            """Apply selected updates from all tables."""
            try:
                updates_to_install = []
                
                # Collect selected updates from each table
                for row in regular_data:
                    if row[5]:  # If selected
                        updates_to_install.append(create_package_from_row(row))
                        
                for row in explicit_data:
                    if row[5]:  # If selected
                        updates_to_install.append(create_package_from_row(row, is_explicit=True))
                        
                for row in unknown_data:
                    if row[5]:  # If selected
                        updates_to_install.append(create_package_from_row(row, is_unknown=True))
                
                if not updates_to_install:
                    return "No updates selected for installation"
                    
                # Install updates
                logger.info(f"Installing {len(updates_to_install)} updates...")
                install_updates(updates_to_install)
                
                return f"Successfully installed {len(updates_to_install)} updates"
                
            except WingetError as e:
                gr.Warning(str(e))
                return f"Error installing updates: {str(e)}"
            except Exception as e:
                logger.error(f"Error applying updates: {e}")
                gr.Error("An unexpected error occurred while installing updates")
                return f"Error installing updates: {str(e)}"
        
        check_updates_button.click(
            fn=handle_check_updates,
            outputs=[
                regular_updates_table,
                explicit_updates_table,
                unknown_updates_table,
                apply_updates_button,
                update_status
            ],
            api_name="check_updates"
        )
        
        # Connect apply updates button
        apply_updates_button.click(
            fn=handle_apply_updates,
            inputs=[
                regular_updates_table,
                explicit_updates_table,
                unknown_updates_table
            ],
            outputs=[update_status],
            api_name="apply_updates"
        )
    
    return app

def main():
    logger.info("Starting WingetUpdatesInstaller GUI...")
    app = create_app()
    logger.info("Launching server on http://localhost:10001")
    app.launch(
        server_port=10001,
        server_name="0.0.0.0",
        quiet=False,  # Enable Gradio server logs
    )

if __name__ == "__main__":
    main()
