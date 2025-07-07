import argparse
import json
import os
import sys
import glob
import shutil
import requests

if os.name == 'nt':
    import msvcrt
else:
    import termios
    import tty
    import shutil

MEMORY_FILE = "memory.json"
memory = {str(i): 0 for i in range(1024)}
registers = {}
debug_view_mode = 'step'

# MAIN MENU VARIABLES
File = "none"
DebugMode = False
SaveMainMenu = True

# Updating
LOCAL_VERSION_FILE = "version.txt"
REMOTE_VERSION_URL = "https://raw.githubusercontent.com/the-real-N0NAME/SCAI/main/release/version.txt"

def CheckForUpdate():
    global LOCAL_VERSION_FILE, REMOTE_VERSION_URL
    if not os.path.exists(LOCAL_VERSION_FILE):
        return "update available unknown --> unknown"

    with open(LOCAL_VERSION_FILE, "r") as f:
        v_local = f.read().strip()

    try:
        r = requests.get(REMOTE_VERSION_URL)
        r.raise_for_status()
        v_remote = r.text.strip()
    except Exception as e:
        print(f"Failed to check remote version: {e}")
        return None

    if v_local != v_remote:
        return f"update available {v_local} --> {v_remote}"

    return None

# Main functions

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            memory.update(json.load(f))

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

def get_key():
    if os.name == 'nt':
        key = msvcrt.getch()
        if key == b'\xe0' or key == b'\x00':
            return msvcrt.getch()
        return key
    else:
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def clear_screen():
    # Use ANSI escape codes to clear screen and move cursor to home position
    print("\033[2J\033[H", end='')

def colorize(text, bg="red"):
    colors = {"red": "41", "green": "42", "blue": "44", "default": "49"}
    code = colors.get(bg, "49")
    return f"\033[{code}m{text}\033[0m"

def debug_prompt(line_num, instructions):
    global debug_view_mode
    while True:
        clear_screen()
        width = shutil.get_terminal_size().columns
        print("DEBUG MODE [STEP VIEW]".center(width, "=") + "\n")
        if debug_view_mode == 'step':
            for i, line in enumerate(instructions):
                line_str = f"{i+1:03}: {line.strip()}"
                if i == line_num:
                    print(colorize(line_str, bg="red"))
                else:
                    print(line_str)
            print("\n(Arrow/Space = next | ESC = overview)")
        elif debug_view_mode == 'state':
            print(f"Instruction [{line_num+1:03}]: {instructions[line_num].strip()}\n")
            print("=== Registers ===")
            print(json.dumps(registers, indent=2))
            print("\n=== Memory (non-zero only) ===")
            mem_view = {k: v for k, v in memory.items() if int(v) != 0}
            print(json.dumps(mem_view, indent=2))
            print("\n(ESC = step view | Enter = quit)")

        key = get_key()
        if key in (b'\x1b', '\x1b'):
            debug_view_mode = 'state' if debug_view_mode == 'step' else 'step'
        elif debug_view_mode == 'state' and key in (b'\r', b'\n', '\r', '\n'):
            sys.exit("Exited from debug overview.")
        elif key in (b'M', b' ', b'\r', b'\n', 'M', ' ', '\r', '\n'):
            break

def parse_instruction(line):
    return line.strip().replace(",", "").split()

def execute(instructions, debug=False):
    changed_memory = {}
    pc = 0
    while pc < len(instructions):
        tokens = parse_instruction(instructions[pc])
        if not tokens:
            pc += 1
            continue
        if debug:
            debug_prompt(pc, instructions)

        op = tokens[0]
        advance = True

        try:
            if op == "Load":
                reg, addr = tokens[1], tokens[2].strip("[]")
                registers[reg] = int(memory[addr])
            elif op == "Store":
                reg, addr = tokens[1], tokens[2].strip("[]")
                memory[addr] = registers.get(reg, 0)
                changed_memory[addr] = memory[addr]
            elif op == "Set":
                reg, val = tokens[1], int(tokens[3])
                registers[reg] = val
            elif op == "Add":
                r1, r2, r3 = tokens[1], tokens[2], tokens[3]
                registers[r3] = registers.get(r1, 0) + registers.get(r2, 0)
            elif op == "Neg":
                reg = tokens[1]
                registers[reg] = -registers.get(reg, 0)
            elif op == "Jump":
                pc = int(tokens[1].strip("#")) - 1
                advance = False
            elif op == "JP":
                reg, target = tokens[1], int(tokens[2].strip("#"))
                if registers.get(reg, 0) > 0:
                    pc = target - 1
                    advance = False
            else:
                print(f"Unknown instruction: {instructions[pc]}")
        except Exception as e:
            print(f"Error at line {pc+1}: {instructions[pc]} -> {e}")

        if advance:
            pc += 1

    save_memory()
    print("\n=== EXECUTION COMPLETE ===")
    if len(changed_memory) > 0:
        print("\nChanged Memory Values:")
        for addr in sorted(changed_memory, key=int):
            print(f"[{addr}] = {changed_memory[addr]}")
    else:
        print("\nNo memory values changed.")
    input("\nPress Enter to continue...")

def set_mode():
    load_memory()
    print("Live SET mode. Type `exit` to quit.")
    while True:
        cmd = input("set> ").strip()
        if cmd.lower() == "exit":
            break
        try:
            if "=" in cmd:
                left, right = cmd.split("=")
                left, right = left.strip(), int(right.strip())
                if left.upper().startswith("R"):
                    registers[left.upper()] = right
                    print(f"{left.upper()} set to {right}")
                else:
                    memory[left] = right
                    print(f"memory[{left}] = {right}")
        except Exception as e:
            print(f"Invalid input. Use format: R1 = 5 or 42 = 99")
    save_memory()

def quit():
    global SaveMainMenu, File, DebugMode
    if SaveMainMenu:
        with open("menu.json", "w") as f:
            json.dump({
                "file": File,
                "debug": DebugMode,
                "save": SaveMainMenu
            }, f, indent=2)
    sys.exit(0) 


def MainMenu():
    global File, SaveMainMenu, DebugMode
    index = 0
    options = [
        ("Run", main),
        ("Select File", file_selection_menu),
        ("Settings", settings),
        ("Exit", quit)
    ]

    UpdateAV = CheckForUpdate()
    if UpdateAV:
        options.append(("Update", lambda: print(UpdateAV)))

    if SaveMainMenu and os.path.exists("menu.json"):
        with open("menu.json", "r") as f:
            saved_menu = json.load(f)
            File = saved_menu["file"]
            DebugMode = saved_menu["debug"]
            SaveMainMenu = saved_menu["save"]


    while True:
        clear_screen()
        print("=== Assembly Interpreter ===")
        if UpdateAV:
            print(UpdateAV)
        print(f"File to execute: {File}, Debug Mode: {'ON' if DebugMode else 'OFF'}")
        for i, (name, _) in enumerate(options):
            prefix = "> " if i == index else "  "
            print(prefix + name)

        key = get_key()
        if key in (b'H', 'H') and index > 0:
            index -= 1
        elif key in (b'P', 'P') and index < len(options) - 1:
            index += 1
        elif key in (b'\r', b'\n', '\r', '\n'):
            clear_screen()
            options[index][1]()


def settings():
    global DebugMode, SaveMainMenu
    index = 0

    def toggle_debug():
        global DebugMode
        DebugMode = not DebugMode

    def toggle_save():
        global SaveMainMenu
        SaveMainMenu = not SaveMainMenu

    options = [
        ("Debug Mode", lambda: toggle_debug()),
        ("Save Main Menu", lambda: toggle_save()),
        ("Back to Main Menu", lambda: None)
    ]

    while True:
        clear_screen()
        print("=== Settings ===")
        print("Use arrow keys to navigate and toggle settings, Enter to select")
        for i, (label, _) in enumerate(options):
            if label == "Debug Mode":
                status = "ON " if DebugMode else "OFF"
            elif label == "Save Main Menu":
                status = "ON " if SaveMainMenu else "OFF"
            else:
                status = "   "
            prefix = "<> " if i == index else "   "
            print(f"[ {status} ] {prefix}{label}")

        key = get_key()
        if key in (b'H', 'H') and index > 0:
            index -= 1
        elif key in (b'P', 'P') and index < len(options) - 1:
            index += 1
        elif key in (b'K', 'K'):
            if index < 2:
                options[index][1]()
        elif key in (b'M', 'M'):
            if index < 2:
                options[index][1]()
        elif key in (b'\r', b'\n', '\r', '\n'):
            if index == 2:
                return


def file_selection_menu():
    global File
    files = [f for f in glob.glob("*.txt")]
    if not files:
        print("No .txt files found.")
        sys.exit(1)

    index = 0
    while True:
        clear_screen()
        print("\nSelect a file using arrow keys and press Enter:\n")
        for i, f in enumerate(files):
            prefix = "> " if i == index else "  "
            print(prefix + f)

        key = get_key()
        if key in (b'H', 'H') and index > 0:
            index -= 1
        elif key in (b'P', 'P') and index < len(files) - 1:
            index += 1
        elif key in (b'\r', b'\n', '\r', '\n'):
            File = files[index]
            return

def main():
    global File, DebugMode
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--file", help="Assembly file to interpret")
    parser.add_argument("-d", "--debug", action="store_true", help="Debug mode")
    parser.add_argument("-s", "--set", action="store_true", help="Live mode for setting values")
    args = parser.parse_args()

    if args.set:
        set_mode()
        return

    filename = args.file
    if not filename and File == "none":
        MainMenu()

    if File == "none":
        if not os.path.exists(filename):
            print("Assembly file missing or invalid.")
            return
    else:
        if not os.path.exists(File):
            print("Assembly file missing or invalid.")
            return
        else:
            filename = File

    UpdateAV = CheckForUpdate()
    if UpdateAV:
        print(UpdateAV)
        update_choice = input("Do you want to update? (y/n): ").strip().lower()
        if update_choice == 'y':
            pass
        else:
            print("Continuing without update...")

    clear_screen()
    load_memory()
    with open(filename, "r") as f:
        instructions = f.readlines()
    execute(instructions, debug=args.debug if args.debug else DebugMode)

if __name__ == "__main__":
    main()