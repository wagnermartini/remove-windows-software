# remove-windows-software

## Windows Uninstaller Script  
### Automated Software Removal for Windows  

📌 *This script was developed with the assistance of AI, combining automation techniques with system management best practices.*  

This **Python script** automates the uninstallation of software on Windows, supporting different uninstall methods such as:  
- **Standard Uninstallers** (retrieved from Windows Registry)  
- **MSI-based Installations** (silent uninstallation using `msiexec`)  
- **WMI-based Uninstall** (if the standard method fails)  
- **Appx Package Removal** (for UWP apps via PowerShell)  
- **DISM Feature Removal** (for built-in Windows features)  

## 🔹 Features  
✅ Searches for installed applications using the **Windows Registry**  
✅ Executes the appropriate **uninstall command** automatically  
✅ Supports **silent uninstallation** for supported programs (e.g., MSI)  
✅ Removes **Appx packages** using PowerShell  
✅ Uses **DISM** to disable Windows features  
✅ Generates **logs** (`uninstall.log`) for tracking all actions  

## 🚀 How to Use  
1. Open **Command Prompt** or **PowerShell**.  
2. Run the script with the name of the software to uninstall:  
   ```bash
   python uninstall.py "firefox"


## 🔄 Script Execution Flow  
The script will:  
- 🔍 Search for the software in the **Windows Registry**  
- 🛠️ Execute the **uninstall command** if available  
- ⚙️ If the standard method fails, try **WMI-based removal**  
- 📦 If the software is an **Appx package**, attempt removal via **PowerShell**  
- 🖥️ If it's a **Windows feature**, disable it using **DISM**  

## 🔧 Requirements  
- 🖥️ **Windows 10 or later** (Administrator privileges required)  
- 🐍 **Python 3.x installed**  
- 🔑 **Run as Administrator** for full functionality  

## 📝 Notes  
- 🎯 **Silent uninstall parameters** are included for some software (e.g., **Firefox, PuTTY**)  
- 📜 **Logs** are stored in `uninstall.log`  
- 🔍 If the software is **not found** in the registry, the script will attempt **WMI, Appx, or DISM removal**  

 
