"""Hardware information utilities."""
import platform
import sys
import psutil
try:
    import cpuinfo
    import GPUtil
except ImportError:
    cpuinfo = None
    GPUtil = None

def get_system_info() -> str:
    """Get detailed system information.
    
    Returns:
        str: Formatted string containing system information
    """
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
