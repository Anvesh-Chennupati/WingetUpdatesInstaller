import gradio as gr
import logging
from typing import Dict, List, Tuple, Any
import subprocess
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
                        type="array"
                    )
                    
                    # Unavailable Packages Section
                    gr.Markdown("#### Not Available in Winget")
                    unavailable_packages = gr.DataFrame(
                        headers=["Name", "ID", "Version", "Source"],
                        datatype=["str", "str", "str", "str"],
                        label="System Packages",
                        type="array"
                    )
                    
                    # Status for updates
                    update_status = gr.Textbox(
                        label="Update Status",
                        interactive=False,
                        visible=False
                    )

                    # Updates Section
                    gr.Markdown("### Available Updates")
                    with gr.Row():
                        check_updates_button = gr.Button("🔄 Check for Updates", variant="primary")
                        apply_updates_button = gr.Button("✨ Apply Selected Updates", variant="primary", visible=False)
                    
                    # Status for updates
                    update_status = gr.Textbox(
                        label="Update Status",
                        interactive=False,
                        visible=False
                    )

                    # Regular updates section
                    gr.Markdown("#### Standard Updates")
                    regular_updates_table = gr.DataFrame(
                        headers=["Name", "ID", "Current Version", "Available Version", "Source", "Update"],
                        datatype=["str", "str", "str", "str", "str", "bool"],
                        label="Regular Updates",
                        type="array",
                        interactive=True  # Allow interaction but we'll control the checkbox state
                    )
                    
                    # Explicit updates section
                    gr.Markdown("#### Updates Requiring Explicit Targeting")
                    gr.Text("These packages require manual confirmation using the --id flag during update", show_label=False)
                    explicit_updates_table = gr.DataFrame(
                        headers=["Name", "ID", "Current Version", "Available Version", "Source", "Update"],
                        datatype=["str", "str", "str", "str", "str", "bool"],
                        label="Explicit Updates",
                        type="array",
                        interactive=True
                    )
                    
                    # Unknown version updates section
                    gr.Markdown("#### Updates with Unknown Versions")
                    gr.Text("These packages have versions that cannot be determined automatically", show_label=False)
                    unknown_updates_table = gr.DataFrame(
                        headers=["Name", "ID", "Current Version", "Available Version", "Source", "Update"],
                        datatype=["str", "str", "str", "str", "str", "bool"],
                        label="Unknown Version Updates",
                        type="array",
                        interactive=True
                    )

                    def format_updates_for_display(updates: List[PackageUpdate]) -> List[List]:
                        """Format package updates for display in tables with checkboxes disabled by default."""
                        formatted = []
                        for pkg in updates:
                            try:
                                entry = [
                                    pkg.name,
                                    pkg.id,
                                    pkg.version,
                                    pkg.available_version,
                                    pkg.source or "winget",
                                    False  # Default to NOT selected for update
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
                            
                            # Format each type of update for display with checkboxes disabled
                            regular_data = format_updates_for_display(regular)
                            explicit_data = format_updates_for_display(explicit)
                            unknown_data = format_updates_for_display(unknown)
                            
                            logger.info(f"Found {len(regular)} regular, {len(explicit)} explicit, and {len(unknown)} unknown version updates")
                            
                            # Show apply updates button if there are updates
                            show_button = bool(regular_data or explicit_data or unknown_data)
                            status_text = "Updates found. Select packages to update and click 'Apply Selected Updates'." if show_button else "No updates available"
                            
                            return [
                                regular_data,
                                explicit_data,
                                unknown_data,
                                gr.update(visible=show_button),
                                gr.update(value=status_text, visible=True)
                            ]
                            
                        except WingetError as e:
                            gr.Warning(str(e))
                            return [
                                [], [], [],
                                gr.update(visible=False),
                                gr.update(value=str(e), visible=True)
                            ]
                        except Exception as e:
                            logger.error(f"Error checking for updates: {e}")
                            gr.Error("An unexpected error occurred while checking for updates")
                            return [
                                [], [], [],
                                gr.update(visible=False),
                                gr.update(value=f"Error: {str(e)}", visible=True)
                            ]

                    def handle_apply_updates(regular_data: List[List], explicit_data: List[List], unknown_data: List[List]) -> Dict:
                        """Apply selected updates with clean, real-time output."""
                        try:
                            updates_to_install = []
                            
                            # Collect selected updates
                            for row in regular_data:
                                if row[5]: updates_to_install.append(create_package_from_row(row))
                            for row in explicit_data:
                                if row[5]: updates_to_install.append(create_package_from_row(row, is_explicit=True))
                            for row in unknown_data:
                                if row[5]: updates_to_install.append(create_package_from_row(row, is_unknown=True))
                            
                            if not updates_to_install:
                                return gr.update(value="No updates selected", visible=True)
                                
                            output_lines = [f"Starting installation of {len(updates_to_install)} updates...\n"]
                            yield gr.update(value="\n".join(output_lines), visible=True)
                            
                            success_count = 0
                            failed_packages = []
                            
                            for pkg in updates_to_install:
                                try:
                                    # Build command
                                    cmd = ["winget", "upgrade", "--id", pkg.id]
                                    if not pkg.is_unknown_version and pkg.available_version:
                                        cmd.extend(["--version", pkg.available_version])
                                    
                                    output_lines.append(f"\n🔄 Installing {pkg.name}...")
                                    yield gr.update(value="\n".join(output_lines), visible=True)
                                    
                                    process = subprocess.Popen(
                                        cmd,
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE,
                                        text=True,
                                        encoding='utf-8',
                                        bufsize=1
                                    )
                                    
                                    # Process output with cleaner formatting
                                    last_progress = ""
                                    while True:
                                        output = process.stdout.readline()
                                        if output == '' and process.poll() is not None:
                                            break
                                        if output:
                                            # Clean up spinner animations and progress bars
                                            clean_line = output.strip()
                                            if any(c in clean_line for c in ["-", "\\", "|", "/", "▒", "█"]):
                                                if "MB /" in clean_line:  # Keep progress bars
                                                    if clean_line != last_progress:
                                                        output_lines[-1] = clean_line
                                                        last_progress = clean_line
                                                        yield gr.update(value="\n".join(output_lines), visible=True)
                                                continue
                                            if not clean_line or clean_line.startswith("Found") or "Microsoft is not responsible" in clean_line:
                                                continue
                                            output_lines.append(clean_line)
                                            yield gr.update(value="\n".join(output_lines), visible=True)
                                    
                                    # Check result
                                    if process.poll() == 0:
                                        success_count += 1
                                        output_lines.append(f"✅ Successfully installed {pkg.name}\n")
                                    else:
                                        error_msg = process.stderr.read().strip() or "Unknown error"
                                        output_lines.append(f"❌ Failed to install {pkg.name}: {error_msg}\n")
                                        failed_packages.append(pkg.name)
                                    
                                    yield gr.update(value="\n".join(output_lines), visible=True)
                                    
                                except Exception as e:
                                    error_msg = str(e)
                                    output_lines.append(f"❌ Error installing {pkg.name}: {error_msg}\n")
                                    failed_packages.append(pkg.name)
                                    yield gr.update(value="\n".join(output_lines), visible=True)
                            
                            # Final summary
                            if success_count == len(updates_to_install):
                                output_lines.append(f"\n🎉 All {success_count} updates installed successfully!")
                            elif success_count > 0:
                                output_lines.append(f"\n⚠️ Completed with {success_count} successes and {len(failed_packages)} failures")
                            else:
                                output_lines.append("\n❌ All updates failed")
                            
                            if failed_packages:
                                output_lines.append("\nFailed packages: " + ", ".join(failed_packages))
                            
                            return gr.update(value="\n".join(output_lines), visible=True)
                            
                        except Exception as e:
                            return gr.update(value=f"❌ Critical error: {str(e)}", visible=True)
                    # Connect button events
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
                logger.debug(f"Non-winget packages: {non_winget_data}")
                
                return winget_data, non_winget_data
            except Exception as e:
                logger.error(f"Error in update_package_tables: {e}")
                return [], []

        list_packages_button.click(
            fn=update_package_tables,
            outputs=[packages_table, unavailable_packages],
            api_name="list_packages"
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