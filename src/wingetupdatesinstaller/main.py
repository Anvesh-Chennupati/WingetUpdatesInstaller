import gradio as gr
import logging
import platform
import sys
import psutil
import subprocess
from datetime import datetime
try:
    import cpuinfo
    import GPUtil
except ImportError:
    cpuinfo = None
    GPUtil = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_system_info():
    """Get detailed system information."""
    system_info = []
    
    # OS Information
    system_info.append(f"Operating System: {platform.system()} {platform.release()} {platform.version()}")
    system_info.append(f"Python Version: {sys.version.split()[0]}")
    
    # CPU Information
    if cpuinfo:
        cpu_info = cpuinfo.get_cpu_info()
        system_info.append(f"CPU: {cpu_info['brand_raw']}")
        system_info.append(f"CPU Cores: {psutil.cpu_count(logical=False)} (Physical), {psutil.cpu_count()} (Logical)")
    else:
        system_info.append("CPU info not available (cpuinfo module not installed)")
    
    # Memory Information
    memory = psutil.virtual_memory()
    system_info.append(f"Total RAM: {memory.total / (1024**3):.2f} GB")
    system_info.append(f"Available RAM: {memory.available / (1024**3):.2f} GB")
    system_info.append(f"RAM Usage: {memory.percent}%")
    
    # GPU Information
    if GPUtil:
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                system_info.append(f"GPU {i+1}: {gpu.name}")
                system_info.append(f"GPU Memory Total: {gpu.memoryTotal} MB")
                system_info.append(f"GPU Memory Used: {gpu.memoryUsed} MB")
        except Exception as e:
            system_info.append(f"GPU info error: {str(e)}")
    else:
        system_info.append("GPU info not available (GPUtil module not installed)")
    
    # Disk Information
    disk = psutil.disk_usage('/')
    system_info.append(f"Disk Total: {disk.total / (1024**3):.2f} GB")
    system_info.append(f"Disk Free: {disk.free / (1024**3):.2f} GB")
    system_info.append(f"Disk Usage: {disk.percent}%")
    
    return "\n".join(system_info)

def check_winget():
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

def create_app():
    logger.info("Creating Gradio application")
    with gr.Blocks(title="WingetUpdatesInstaller") as app:
        with gr.Row():
            with gr.Column():
                gr.Markdown("## Welcome to WingetUpdatesInstaller")
                gr.Markdown("### System Information and Winget Status")
                
                # System Info Button and Output
                system_info_button = gr.Button("📊 Check System Details", variant="primary")
                system_info_output = gr.Textbox(
                    label="System Information",
                    lines=15,
                    max_lines=20
                )
                
                # Winget Status Button and Output
                winget_status_button = gr.Button("🔍 Check Winget Status", variant="secondary")
                winget_status_output = gr.Textbox(
                    label="Winget Status",
                    lines=3
                )
                
                # Connect buttons to their functions
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
