# SCAI - Simple Custom Assembly Interpreter

**SCAI** is a Python-powered interpreter for a custom assembly-like language with support for debugging, memory management, live register setting, auto-updating via GitHub, and a user-friendly TUI.

---

## Features

* Custom instruction parsing and execution
* Persistent memory across sessions (`memory.json`)
* Registers reset every run
* Debug mode with interactive step/state view
* Live mode for manually setting registers and memory
* Main menu with file selection, settings, and auto-save
* Auto-Updating from GitHub `/release` folder

---

## Getting Started

### Run the script:

```bash
python SCAI.py            # Opens the main menu
python SCAI.py -f file.txt  # Runs a specific file
python SCAI.py -d -f file.txt  # Runs with debug mode
python SCAI.py -s         # Enters live set mode
```

### Optional flags:

* `-f, --file <file>`: Run a specific assembly file
* `-d, --debug`: Enable step-by-step debug mode
* `-s, --set`: Live mode to assign values manually

---

## Instruction Set

| Command | Syntax           | Description                                     |
| ------- | ---------------- | ----------------------------------------------- |
| `Load`  | `Load R1 [40]`   | Loads memory address `40` into register `R1`    |
| `Store` | `Store R1 [40]`  | Stores value from `R1` into memory address `40` |
| `Set`   | `Set R1 = 5`     | Sets register `R1` to the value 5               |
| `Add`   | `Add R1, R2, R3` | `R3 = R1 + R2`                                  |
| `Neg`   | `Neg R1`         | Negates the value in register `R1`              |
| `Jump`  | `Jump #5`        | Jumps to line number 5                          |
| `JP`    | `JP R1, #5`      | Jumps to line 5 if value in `R1` > 0            |

---

## Debug Mode

* View entire code with line numbers
* Current line highlighted with a red background
* Press **Right Arrow / Space** to execute
* Press **ESC** to view memory/register state
* Press **Enter** while in overview to quit

---

## Live Mode

Enter `set` mode with `-s`. Type:

* `R1 = 5` to set a register
* `40 = 123` to set a memory address
* `exit` to leave

Changes are saved automatically to `memory.json`.

---

## Updating

* Checks for a new version in GitHub `/release/version.txt`
* Downloads new `SCAI.exe` if available
* Launches an updater batch script
* Replaces old executable and cleans up automatically

---

## File Selection Menu

If no file is provided via `-f`, you will see a menu listing `.txt` files.

* Navigate with **Arrow keys**
* Select with **Enter**

---

## Example Script

```asm
Load R1 [41]
Load R4 [40]
Set R2 = 2
Neg R2
Add R1, R2, R1
JP R1, #5
Set R3 = 1
Add R1, R3, R1
JP R1, #11
Jump #13
Add R4, R3, R4
Store R4 [40]
```

---

## Notes

* Executables are expected to be named `SCAI.exe`
* `version.txt` must be included alongside the `.exe` to allow version checking
* This project is Windows-first, but compatible with Unix if modified slightly
* The interpreter loads code line-by-line and supports both keyboard and command-line use

---

## Credits

Developed by [the-real-N0NAME](https://github.com/the-real-N0NAME/).
