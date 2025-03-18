import sys
import subprocess
import winreg

EXTRA_UNINSTALL_PARAMS = {
    "firefox": "-ms",
    "mozilla ftp": "-y",
    "putty": "/quiet"
}

def find_software(target_software):
    """Search for software by name and return its details."""
    uninstall_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
    for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            with winreg.OpenKey(hive, uninstall_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        with winreg.OpenKey(hive, f"{uninstall_path}\\{winreg.EnumKey(key, i)}") as subkey:
                            values = {winreg.EnumValue(subkey, j)[0]: winreg.EnumValue(subkey, j)[1]
                                      for j in range(winreg.QueryInfoKey(subkey)[1])}
                            display_name = values.get("DisplayName")
                            uninstall_cmd = values.get("QuietUninstallString") or values.get("UninstallString")
                            if display_name and target_software.lower() in display_name.lower():
                                if "msiexec" in (uninstall_cmd or "").lower() and "/I" in uninstall_cmd:
                                    uninstall_cmd = uninstall_cmd.replace("/I", "/X")
                                extra_params = next((EXTRA_UNINSTALL_PARAMS[key] for key in EXTRA_UNINSTALL_PARAMS
                                                     if key.lower() in display_name.lower()), "")
                                print(f"\nSoftware Found: {display_name}")
                                print(f"   Command: {uninstall_cmd}")
                                print(f"   Extra Parameters: {extra_params or 'None'}")
                                return display_name, uninstall_cmd, extra_params
                    except OSError:
                        continue
        except FileNotFoundError:
            continue
    print(f"\nNo software found matching '{target_software}'.")
    return None, None, None

def run_uninstall(command, extra_params):
    """Execute the uninstallation command."""
    if not command:
        print("No valid uninstallation command found.")
        return False
    try:
        command = f"cmd /c {command} /qn /norestart" if "msiexec" in command.lower() else f"{command} {extra_params}"
        print(f"\nExecuting: {command}")
        subprocess.run(command, shell=True, check=True)
        print("\nUninstallation completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError during uninstallation: {e}")
        return False

def uninstall_via_wmi(display_name):
    """Attempt to remove software via WMI."""
    print(f"\nAttempting to remove {display_name} via WMI...")
    try:
        subprocess.run(f'wmic product where name="{display_name}" call uninstall /nointeractive',
                       shell=True, check=True)
        print("\nWMI uninstallation requested successfully.")
    except subprocess.CalledProcessError as e:
        print(f"\nError during WMI uninstallation: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: py uninstall.py \"software_name\"")
        sys.exit(1)

    target_software = sys.argv[1]
    print(f"\nSearching for software '{target_software}' to remove...\n")
    display_name, uninstall_command, extra_params = find_software(target_software)
    if uninstall_command and not run_uninstall(uninstall_command, extra_params):
        uninstall_via_wmi(display_name)