import glob
import os
import sys
import tty
from typing import Final, Sequence, Any

import readline
import termios

from pyre.core.builtins import BUILTIN_COMMANDS
from pyre.core.config import shell_config
from pyre.utils.ui import redraw_input_line


def get_system_commands(prefix: str) -> list[str]:
    """
    Search directories in the system PATH for executables that start with the given prefix.
    """
    commands: set = set()
    path_env: str = os.environ.get("PATH", "")  # Get PATH environment variable
    directories: list[str] = path_env.split(os.pathsep)  # Get directories in PATH

    for directory in directories:
        if os.path.isdir(directory):  # Check if is a directory
            try:
                for file in os.listdir(directory):  # Get files in the directory
                    if file.startswith(prefix):
                        full_path: str = os.path.join(directory, file)  # Get the fullpath of the file
                        if os.access(full_path, os.X_OK):  # If the file has execute permissions
                            commands.add(file)  # It's added to the list of commands
            except PermissionError:
                continue

    return list(commands)


def smart_completer(text: str, state: int) -> str | None:
    """
    A custom completer function that provides autocompletion for commands and paths based on the current input.
    """
    buffer: str = readline.get_line_buffer()  # Get written text in the current line

    if " " not in buffer.lstrip():
        matches: list[str] = get_system_commands(text)  # Search for commands in PATH

        # Filter built-in commands and aliases that start with the current text
        filtered_builtins: list[str] = [cmd for cmd in BUILTIN_COMMANDS.keys() if cmd.startswith(text)]
        filtered_aliases: list[str] = [alias for alias in shell_config.aliases.keys() if alias.startswith(text)]

        matches.extend(filtered_builtins)  # Add built-in commands
        matches.extend(filtered_aliases)  # Add aliases

        expanded_text: str = os.path.expanduser(text)  # Expand ~ to the user's home directory

        matches.extend(glob.glob(expanded_text + '*'))  # Add local files or directories that match the current text
        matches = sorted(list(set(matches)))  # Remove duplicates and sort the matches
    else:
        uses_tilde = text.startswith("~")  # Check if the text starts with ~

        expanded_text: str = os.path.expanduser(text)  # Expand ~ to the user's home directory
        raw_matches: list[str] = glob.glob(expanded_text + '*')  # Search local files or directories

        matches: list[str] = []  # Initialize an empty list to store matches

        for match in raw_matches:
            if uses_tilde:
                home_dir = os.path.expanduser("~")  # Get the user's home directory

                # Replace the home directory path with ~ for display purposes
                match = match.replace(home_dir, "~", 1)

            matches.append(match)  # Add the match to the list of matches

    if state < len(matches):
        return matches[state]  # Return the match corresponding to the current state (index)
    else:
        return None  # Return None if there are no more matches for the current state (index)


def custom_display_matches(_substitution: str, matches: Sequence[str], longest_match_length: int) -> None:
    """
    Custom display function to show autocompletion matches with a limit and prompt for user confirmation if exceeded.
    """
    LIMIT: Final[int] = 30  # Limit for the number of matches to display

    if len(matches) > LIMIT:
        print(f"\nDisplay all {len(matches)} possibilities? (y or n) ", end="")
        sys.stdout.flush()  # Show the prompt immediately

        fd: int = sys.stdin.fileno()  # Get file descriptor for standard input
        old_settings: list[Any] = termios.tcgetattr(fd)  # Save current terminal settings

        try:
            tty.setraw(fd)  # Set terminal to raw mode to read single character input
            ch: str = sys.stdin.read(1)  # Read a single character from standard input (y or n)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)  # Restore terminal settings

        print()  # Print a newline after user input

        if ch.lower() != "y":
            current_buffer: str = readline.get_line_buffer()  # Get the current user input line
            redraw_input_line(current_buffer)  # Redraw the input line to restore the prompt and user input
            return  # Exit the function without displaying matches

    # If the number of matches is within the limit or user confirmed, display the matches

    print()  # Print a newline before displaying matches

    try:
        term_width: int = os.get_terminal_size().columns  # Get the terminal width to format the output
    except OSError:
        term_width: int = 80  # If unable to get terminal size, default to 80 columns

    # Calculate the width of each column based on the longest match length and 2 spaces for margin
    column_width: int = longest_match_length + 2

    # Calculate the number of columns that can fit in the terminal width
    num_columns: int = max(1, term_width // column_width)

    for i, match in enumerate(matches):
        print(f"{match:<{column_width}}", end="")  # Print each match left-aligned with the calculated column width
        if (i + 1) % num_columns == 0:  # If the current match is the last in the row, print a newline
            print()

    print()  # Print a newline after displaying all matches

    current_buffer: str = readline.get_line_buffer()  # Get the current user input line
    redraw_input_line(current_buffer)  # Redraw the input line to restore the prompt and user input
