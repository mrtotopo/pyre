import os
import sys
import tty
from typing import Final, Sequence, Any

try:
    import gnureadline as readline
except ImportError:
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

    lower_prefix: str = prefix.lower()  # Convert the prefix to lowercase for case-insensitive matching

    for directory in directories:
        if os.path.isdir(directory):  # Check if is a directory
            try:
                for file in os.listdir(directory):  # Get files in the directory
                    if file.lower().startswith(lower_prefix):
                        full_path: str = os.path.join(directory, file)  # Get the fullpath of the file
                        if os.access(full_path, os.X_OK):  # If the file has execute permissions
                            commands.add(file)  # It's added to the list of commands
            except PermissionError:
                continue

    return list(commands)


def _get_local_files_case_insensitive(expanded_text: str) -> list[str]:
    """
    Replace glob.glob with a case-insensitive search for local files and directories that match the given expanded text.
    """
    directory: str = os.path.dirname(expanded_text)  # Get the directory part of the expanded text
    prefix: str = os.path.basename(expanded_text)  # Get the filename part of the expanded text
    search_dir: str = directory if directory else "."  # Use current directory if no directory is specified

    matches: list[str] = []  # Initialize an empty list to store matching files and directories
    lower_prefix: str = prefix.lower()  # Convert the prefix to lowercase for case-insensitive matching

    try:
        if os.path.exists(search_dir) and os.path.isdir(search_dir):
            for filename in os.listdir(search_dir):
                if filename.lower().startswith(lower_prefix):

                    # Skip hidden files if the prefix does not start with a dot
                    if filename.startswith(".") and not prefix.startswith("."):
                        continue

                    if directory:
                        # If a directory is specified, join it with the filename to get the full path
                        matches.append(os.path.join(directory, filename))

                    else:
                        # If no directory is specified, just add the filename to the matches
                        matches.append(filename)

    except PermissionError:
        pass  # Ignore directories that cannot be accessed due to permission errors

    return matches

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

        # Use case-insensitive search for local files and directories that match the expanded text
        matches.extend(_get_local_files_case_insensitive(expanded_text))

        matches: list[str] = sorted(list(set(matches)))  # Remove duplicates and sort the matches
    else:
        uses_tilde = text.startswith("~")  # Check if the text starts with ~

        expanded_text: str = os.path.expanduser(text)  # Expand ~ to the user's home directory

        # Use case-insensitive search for local files and directories that match the expanded text
        raw_matches: list[str] = _get_local_files_case_insensitive(expanded_text)

        matches: list[str] = []  # Initialize an empty list to store matches

        for match in raw_matches:
            if uses_tilde:
                home_dir = os.path.expanduser("~")  # Get the user's home directory

                # Replace the home directory path with ~ for display purposes
                match = match.replace(home_dir, "~", 1)

            matches.append(match)  # Add the match to the list of matches

        matches = sorted(matches)  # Sort the matches alphabetically

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

    # Create a list of display names for matches, stripping trailing slashes and using the base name for directories
    display_names: list[str] = [os.path.basename(match.rstrip("/")) for match in matches]

    # Calculate the longest display name length for formatting purposes
    display_longest_length: int = max((len(name) for name in display_names), default=0)

    # Calculate the width of each column based on the longest match length and 2 spaces for margin
    column_width: int = display_longest_length + 2

    # Calculate the number of columns that can fit in the terminal width
    num_columns: int = max(1, term_width // column_width)

    for i, match in enumerate(display_names):
        print(f"{match:<{column_width}}", end="")  # Print each match left-aligned with the calculated column width
        if (i + 1) % num_columns == 0:  # If the current match is the last in the row, print a newline
            print()

    print()  # Print a newline after displaying all matches

    current_buffer: str = readline.get_line_buffer()  # Get the current user input line
    redraw_input_line(current_buffer)  # Redraw the input line to restore the prompt and user input
