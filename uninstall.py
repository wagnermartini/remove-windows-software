import sys
import subprocess
import winreg
import os
import logging

# Configure logging
logging.basicConfig(filename="uninstall.log", level=logging.INFO, format="%(asctime)s - %(message)s")

# Variable to define the software name to remove (overrides command-line argument if set)
PREDEFINED_SOFTWARE_NAME = ""  # Example: "firefox"

# Dictionary for additional uninstall parameters for specific software
EXTRA_UNINSTALL_PARAMS = {
    "firefox": "-ms",
    "mozilla ftp": "-y",
    "putty": "/quiet"
}

# Dictionary mapping for Appx package search terms.
APPX_SEARCH_MAP = {
    "paint": "Microsoft.Windows.MSPaint"
}

def log_action(action):
    """Log actions to a file."""
    logging.info(action)

def find_software(target_software):
    """
    Search the registry for software matching target_software.
    Returns (DisplayName, uninstall command, extra parameters) if found.
    """
    uninstall_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"

    for hive in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
        try:
            with winreg.OpenKey(hive, uninstall_path) as key:
                for i in range(winreg.QueryInfoKey(key)[0]):
                    try:
                        subkey_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(hive, f"{uninstall_path}\\{subkey_name}") as subkey:
                            # Create a dictionary of all values in the subkey.
                            values = {winreg.EnumValue(subkey, j)[0]: winreg.EnumValue(subkey, j)[1]
                                      for j in range(winreg.QueryInfoKey(subkey)[1])}
                            display_name = values.get("DisplayName")
                            uninstall_cmd = values.get("QuietUninstallString") or values.get("UninstallString")
                            if display_name and target_software.lower() in display_name.lower():
                                # Correct MSI command: replace /I with /X.
                                if uninstall_cmd and "msiexec" in uninstall_cmd.lower() and "/I" in uninstall_cmd:
                                    uninstall_cmd = uninstall_cmd.replace("/I", "/X")
                                # Check for extra uninstall parameters.
                                extra_params = ""
                                for key_param in EXTRA_UNINSTALL_PARAMS:
                                    if key_param.lower() in display_name.lower():
                                        extra_params = EXTRA_UNINSTALL_PARAMS[key_param]
                                        break
                                print(f"\nSoftware Found: {display_name}")
                                print(f"   Key: {subkey_name}")
                                print(f"   Base Command: {uninstall_cmd}")
                                print(f"   Extra Parameters: {extra_params if extra_params else 'None'}")
                                log_action(f"Software found: {display_name}, Command: {uninstall_cmd}")
                                return display_name, uninstall_cmd, extra_params
                    except OSError:
                        continue
        except FileNotFoundError:
            continue

    print(f"\nNo software found matching '{target_software}'.")
    log_action(f"No software found matching '{target_software}'.")
    return None, None, None

def run_uninstall(display_name, command, extra_params):
    """
    Execute the uninstall command.
    For MSI commands, run silently; otherwise, append extra parameters if available.
    """
    if not command:
        print("No valid uninstall command found.")
        log_action("No valid uninstall command found.")
        return False
    try:
        if "msiexec" in command.lower():
            command = f"cmd /c {command} /qn /norestart"
        else:
            command = f"{command} {extra_params}" if extra_params else command
        print(f"\nExecuting: {command}")
        log_action(f"Executing uninstall command: {command}")
        subprocess.run(command, shell=True, check=True)
        print("\nUninstallation completed successfully.")
        log_action(f"Uninstallation completed successfully for {display_name}.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError during uninstallation: {e}")
        log_action(f"Error during uninstallation: {e}")
        return False

def uninstall_via_wmi(display_name):
    """
    Attempt to remove the software via WMI.
    """
    print(f"\nAttempting to remove '{display_name}' via WMI...")
    log_action(f"Attempting to remove '{display_name}' via WMI...")
    try:
        wmi_command = f'wmic product where name="{display_name}" call uninstall /nointeractive'
        subprocess.run(wmi_command, shell=True, check=True)
        print("\nWMI uninstallation requested successfully.")
        log_action(f"WMI uninstallation requested successfully for {display_name}.")
    except subprocess.CalledProcessError as e:
        print(f"\nError during WMI uninstallation: {e}")
        log_action(f"Error during WMI uninstallation: {e}")

def uninstall_appx_package(package_search_term):
    """
    Attempt to remove an Appx package using the given search term.
    """
    print(f"\nAttempting to remove Appx package matching '{package_search_term}'...")
    log_action(f"Attempting to remove Appx package matching '{package_search_term}'...")
    try:
        ps_command = (
            "try { $pkg = Get-AppxPackage | Where-Object { $_.Name -like '*" + package_search_term + "*' } | "
            "Select-Object -ExpandProperty PackageFullName -ErrorAction SilentlyContinue; "
            "if ($pkg) { Write-Output $pkg } else { Write-Output '' } } catch { Write-Output '' }"
        )
        full_command = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "{ps_command}"'
        result = subprocess.run(full_command, shell=True, check=False, capture_output=True, text=True)
        full_package_name = result.stdout.strip()
        if full_package_name:
            print(f"\nFull package name found: {full_package_name}")
            log_action(f"Full package name found: {full_package_name}")
            remove_command = f'powershell -NoProfile -ExecutionPolicy Bypass -Command "Remove-AppxPackage {full_package_name}"'
            subprocess.run(remove_command, shell=True, check=True)
            print("\nAppx package uninstallation requested successfully.")
            log_action(f"Appx package uninstallation requested successfully for {full_package_name}.")
        else:
            print(f"\nNo Appx package found matching '{package_search_term}'.")
            log_action(f"No Appx package found matching '{package_search_term}'.")
    except subprocess.CalledProcessError as e:
        print(f"\nError during Appx package uninstallation: {e}")
        log_action(f"Error during Appx package uninstallation: {e}")

def uninstall_via_dism_auto(target_keyword):
    """
    Attempt to disable a Windows feature by first listing features via DISM,
    then searching for one whose name contains target_keyword (case-insensitive),
    and finally running DISM to disable that feature.
    """
    print(f"\nAttempting to disable a Windows feature matching '{target_keyword}' via DISM...")
    log_action(f"Attempting to disable a Windows feature matching '{target_keyword}' via DISM...")
    try:
        dism_list_cmd = "DISM /Online /Get-Features /Format:Table"
        result = subprocess.run(dism_list_cmd, shell=True, check=True, capture_output=True, text=True)
        output = result.stdout
        feature_found = None
        for line in output.splitlines():
            if "|" in line:
                parts = line.split("|")
                feature_name = parts[0].strip()
                if target_keyword.lower() in feature_name.lower():
                    feature_found = feature_name
                    break
        if feature_found:
            print(f"\nFeature found: {feature_found}")
            log_action(f"Feature found: {feature_found}")
            disable_cmd = f"DISM /Online /Disable-Feature /FeatureName:{feature_found} /NoRestart"
            subprocess.run(disable_cmd, shell=True, check=True)
            print("\nDISM command executed successfully. The feature should be disabled.")
            log_action(f"DISM command executed successfully for feature: {feature_found}.")
        else:
            print(f"\nNo DISM feature matching '{target_keyword}' was found.")
            log_action(f"No DISM feature matching '{target_keyword}' was found.")
    except subprocess.CalledProcessError as e:
        print(f"\nError during DISM execution: {e}")
        log_action(f"Error during DISM execution: {e}")

if __name__ == "__main__":
    # Check if the predefined software name is set
    if PREDEFINED_SOFTWARE_NAME:
        target_software = PREDEFINED_SOFTWARE_NAME.strip()
        print(f"Using predefined software name: '{target_software}'")
        log_action(f"Using predefined software name: '{target_software}'")
    else:
        if len(sys.argv) < 2:
            print("Usage: py uninstall.py \"software_name\"")
            print("Examples:")
            print("  py uninstall.py firefox")
            print("  py uninstall.py paint")
            sys.exit(1)

        target_software = sys.argv[1].strip()
        if not target_software:
            print("Error: Software name cannot be empty.")
            sys.exit(1)

    print(f"\nSearching for software '{target_software}' to remove...\n")
    log_action(f"Searching for software '{target_software}' to remove...")

    display_name, uninstall_command, extra_params = find_software(target_software)

    if uninstall_command:
        success = run_uninstall(display_name, uninstall_command, extra_params)
        if not success:
            uninstall_via_wmi(display_name if display_name else target_software)
    else:
        uninstall_via_wmi(target_software)
        appx_search_term = APPX_SEARCH_MAP.get(target_software.lower(), target_software)
        uninstall_appx_package(appx_search_term)
        uninstall_via_dism_auto(target_software)
