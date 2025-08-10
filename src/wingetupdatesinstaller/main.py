import gradio as gr
import logging
from wingetupdatesinstaller.utils import get_system_info, check_winget, get_installed_packages, check_updates
from wingetupdatesinstaller.utils.package_manager import get_all_packages

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
                    
                    # Updates Section
                    gr.Markdown("### Available Updates")
                    with gr.Row():
                        check_updates_button = gr.Button("🔄 Check for Updates", variant="primary")
                        updates_table = gr.Dataframe(
                            headers=["Name", "ID", "Current Version", "Available Version", "Update"],
                            datatype=["str", "str", "str", "str", "bool"],
                            label="Available Updates"
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
            """Get and display both available and unavailable packages."""
            logger.info("Starting package table update")
            winget_pkgs, non_winget_pkgs = get_all_packages()
            logger.debug(f"Retrieved {len(winget_pkgs)} winget packages and {len(non_winget_pkgs)} non-winget packages")
            
            try:
                # Format packages for display
                winget_data = []
                for pkg in winget_pkgs:
                    try:
                        entry = [
                            str(pkg.get("Name", "")),
                            str(pkg.get("ID", "")),
                            str(pkg.get("Version", "")),
                            "winget"
                        ]
                        winget_data.append(entry)
                        logger.debug(f"Added winget package: {entry}")
                    except Exception as e:
                        logger.error(f"Error formatting winget package {pkg}: {e}")
                
                non_winget_data = []
                for pkg in non_winget_pkgs:
                    try:
                        entry = [
                            str(pkg.get("Name", "")),
                            str(pkg.get("ID", "")),
                            str(pkg.get("Version", "")),
                            str(pkg.get("Source", "System"))
                        ]
                        non_winget_data.append(entry)
                        logger.debug(f"Added non-winget package: {entry}")
                    except Exception as e:
                        logger.error(f"Error formatting non-winget package {pkg}: {e}")
                
                logger.debug(f"Final data sizes - Winget: {len(winget_data)}, Non-winget: {len(non_winget_data)}")
                logger.debug(f"Sample winget entry: {winget_data[0] if winget_data else []}")
                logger.debug(f"Sample non-winget entry: {non_winget_data[0] if non_winget_data else []}")
                
                return winget_data, non_winget_data
            except Exception as e:
                logger.error(f"Error in update_package_tables: {e}")
                return [], []

        list_packages_button.click(
            fn=update_package_tables,
            outputs=[packages_table, unavailable_packages],
            api_name="list_packages"
        )
        
        check_updates_button.click(
            fn=check_updates,
            outputs=updates_table,
            api_name="check_updates"
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
