import subprocess

def shell_command(command: str) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(command,
                                shell=True,
                                capture_output=True,
                                text=True)
        return result
    except Exception as exc:
        return exc