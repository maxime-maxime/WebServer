import ctypes
from utils import tracer

@tracer
def start_mysql():
    cmd = r'cmd.exe /c "net start MySQL80"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f'/c "{cmd}"', None, 1)

@tracer
def stop_mysql():
    cmd = r'cmd.exe /c "net stop MySQL80"'
    ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", f'/c "{cmd}"', None, 1)