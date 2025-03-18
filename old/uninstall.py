import sys
import subprocess
import winreg

# Dictionary for additional uninstall parameters for specific software
EXTRA_UNINSTALL_PARAMS = {
    "firefox": "-ms",
    "mozilla ftp": "-y",
    "putty": "/quiet"
}

def find_software(target_software):
    """Search for a software by name and return DisplayName, UninstallString, and QuietUninstallString."""
    uninstall_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"

    for hive, hive_name in [(winreg.HKEY_LOCAL_MACHINE, "HKLM"), (winreg.HKEY_CURRENT_USER, "HKCU")]:
        try:
            with winreg.OpenKey(hive, uninstall_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):  # Iterate through all subkeys
                    try:
                        subkey_name = winreg.EnumKey(key, i)  # Subkey name (GUID or software name)
                        with winreg.OpenKey(hive, f"{uninstall_path}\\{subkey_name}") as subkey:
                            display_name = None
                            uninstall_cmd = None
                            quiet_uninstall_cmd = None

                            # Read all values within the subkey
                            for j in range(winreg.QueryInfoKey(subkey)[1]):
                                try:
                                    value_name, value_data, _ = winreg.EnumValue(subkey, j)

                                    if value_name == "DisplayName":
                                        display_name = value_data

                                    if value_name == "UninstallString":
                                        uninstall_cmd = value_data

                                    if value_name == "QuietUninstallString":
                                        quiet_uninstall_cmd = value_data

                                except OSError:
                                    continue  # Ignore errors

                            if display_name and target_software.lower() in display_name.lower():
                                chosen_cmd = quiet_uninstall_cmd if quiet_uninstall_cmd else uninstall_cmd

                                # Fix incorrect MSI command (if found with /I, replace with /X)
                                if chosen_cmd and "msiexec" in chosen_cmd.lower() and "/I" in chosen_cmd:
                                    chosen_cmd = chosen_cmd.replace("/I", "/X")

                                # Check for additional uninstall parameters
                                additional_params = ""
                                for key in EXTRA_UNINSTALL_PARAMS:
                                    if key.lower() in display_name.lower():
                                        additional_params = EXTRA_UNINSTALL_PARAMS[key]
                                        break  # If a match is found, apply it and exit loop

                                print(f"\nSoftware Found: {display_name}")
                                print(f"   Key: {subkey_name}")
                                print(f"   Base Command: {chosen_cmd}")
                                print(f"   Extra Parameters: {additional_params if additional_params else 'None'}")

                                return display_name, chosen_cmd, additional_params  # Return software details

                    except OSError:
                        continue  # Ignore inaccessible subkeys
        except FileNotFoundError:
            continue

    print(f"\nNo software found matching '{target_software}'.")
    return None, None, None

def run_uninstall(display_name, command, extra_params):
    """Execute the uninstallation command, including extra parameters if available."""
    if not command:
        print("No valid uninstallation command found.")
        return False

    try:
        if "msiexec" in command.lower():
            command = f"cmd /c {command} /qn /norestart"  # Run MSI silently
        else:
            command = f"{command} {extra_params}" if extra_params else command  # Append extra parameters

        print(f"\nExecuting: {command}")
        subprocess.run(command, shell=True, check=True)
        print("\nUninstallation completed successfully.")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\nError during uninstallation: {e}")
        return False

def uninstall_via_wmi(display_name):
    """Failsafe: Try to remove the software via WMI if normal uninstallation fails."""
    print(f"\nAttempting to remove {display_name} via WMI...")
    try:
        wmi_command = f'wmic product where name="{display_name}" call uninstall /nointeractive'
        subprocess.run(wmi_command, shell=True, check=True)
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

    if uninstall_command:
        success = run_uninstall(display_name, uninstall_command, extra_params)
        if not success:  # If uninstallation fails, try WMI as a failsafe
            uninstall_via_wmi(display_name)
