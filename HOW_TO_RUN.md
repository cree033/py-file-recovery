# How to Run the File Recovery System

## Quick Start

### Windows

1. **Open Command Prompt or PowerShell as Administrator**
   - Right-click on Command Prompt/PowerShell
   - Select "Run as administrator"

2. **Navigate to the project directory**
   ```cmd
   cd D:\recovery
   ```

3. **Run the program**
   ```cmd
   python main.py
   ```
   
   This will show a menu to choose between CLI and GUI.

### Launch Options

**Option 1: Interactive Menu (Default)**
```cmd
python main.py
```
Shows a menu to choose between CLI and GUI.

**Option 2: Direct CLI Launch**
```cmd
python main.py --cli
```
or
```cmd
python main.py -c
```
Launches Command Line Interface directly.

**Option 3: Direct GUI Launch**
```cmd
python main.py --gui
```
or
```cmd
python main.py -g
```
Launches Graphical User Interface directly.

**Option 4: Help**
```cmd
python main.py --help
```
Shows help information.

### Alternative: Double-click

If Python is properly configured, you can also:
- Double-click `main.py` in Windows Explorer
- **Note**: You may need administrator privileges

## Requirements

- Python 3.6 or higher
- Windows operating system
- Administrator privileges (for physical drive access)

## Usage Example

1. Run: `python main.py`

2. Select option:
   - `1` for logical drive (C:, D:, etc.)
   - `2` for physical drive (PhysicalDrive0, etc.)

3. Choose the drive from the list

4. Enter output path (where to save recovered files)
   - Example: `D:\recovered_files`

5. Configure file types (optional):
   - Press Enter for ALL types
   - Or specify: `txt,pdf,doc`

6. Enter search pattern (optional):
   - Press Enter for ALL files
   - Or use wildcards: `*pass*.txt` or `%wall%`

7. Filter system files:
   - `Y` (default) to filter system files
   - `n` to include system files

## Wildcards

- `*` = any sequence of characters
  - Example: `*pass*.txt` finds `passwords.txt`, `my_passwords.txt`
- `%` = single character
  - Example: `%wall%` finds `wall.txt`, `wallpaper.jpg`

## Important Notes

⚠️ **Administrator Rights Required**
- Physical drive scanning requires administrator privileges
- Run Command Prompt/PowerShell as administrator

⚠️ **Data Safety**
- The program only reads from disks (does not modify)
- Recovered files are saved to the specified output directory

## Troubleshooting

**Permission Denied Error**
- Run as administrator
- Or use WinPE / Hiren's Boot CD

**No drives detected**
- Check if drives are accessible
- Ensure you have proper permissions

**Python not found**
- Install Python from python.org
- Add Python to PATH during installation

