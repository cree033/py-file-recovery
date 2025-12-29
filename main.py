"""
File Recovery System
Main entry point
"""

import sys
from ui.cli import CLI


def main():
    """Main function - allows choosing between CLI and GUI"""
    
    # Check command line arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode in ['--gui', '-g', 'gui']:
            launch_gui()
            return
        elif mode in ['--cli', '-c', 'cli']:
            launch_cli()
            return
        elif mode in ['--help', '-h', 'help']:
            show_help()
            return
    
    # If no arguments, show menu to choose
    print("\n===== FILE RECOVERY SYSTEM =====\n")
    print("Select interface:")
    print("1. Command Line Interface (CLI)")
    print("2. Graphical User Interface (GUI)")
    print("3. Exit\n")
    
    choice = input("Select option (1-3): ").strip()
    
    if choice == "1":
        launch_cli()
    elif choice == "2":
        launch_gui()
    elif choice == "3":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid option. Launching CLI by default...")
        launch_cli()


def launch_cli():
    """Launches the Command Line Interface"""
    cli = CLI()
    cli.run()


def launch_gui():
    """Launches the Graphical User Interface"""
    try:
        from ui.gui import GUI
        gui = GUI()
        gui.run()
    except ImportError:
        print("\n❌ GUI not available")
        print("GUI module (ui/gui.py) not found.")
        print("Falling back to CLI...\n")
        launch_cli()
    except Exception as e:
        print(f"\n❌ Error launching GUI: {e}")
        print("Falling back to CLI...\n")
        launch_cli()


def show_help():
    """Shows help information"""
    print("""
File Recovery System - Help

Usage:
    python main.py [option]

Options:
    --cli, -c, cli      Launch Command Line Interface
    --gui, -g, gui      Launch Graphical User Interface
    --help, -h, help    Show this help message

If no option is provided, a menu will be shown to choose the interface.

Examples:
    python main.py              # Shows menu to choose
    python main.py --cli         # Launches CLI directly
    python main.py --gui         # Launches GUI directly
    python main.py --help        # Shows this help
    """)


if __name__ == "__main__":
    main()
