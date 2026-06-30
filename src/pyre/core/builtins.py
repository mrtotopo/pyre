import os
import shlex
from collections.abc import Callable
from typing import Final, MutableMapping

from pyre.core.config import shell_config
from pyre.utils.history import display_history

type BuiltinFunction = Callable[[list[str]], bool]  # Type alias for built-in command functions


def builtin_exit(args: list[str]) -> bool:
    """
    Exit the shell.
    """
    return False  # Return False to indicate that the shell should exit


def builtin_history(args: list[str]) -> bool:
    """
    Display the command history.
    """
    display_history()
    return True  # Return True to indicate successful execution


def builtin_cd(args: list[str]) -> bool:
    """
    Change the current working directory.
    """
    try:
        # If no argument is provided, change to the home directory
        path = os.path.expanduser("~") if len(args) == 1 else args[1]
        os.chdir(path)  # Change the current working directory to the specified path
    except FileNotFoundError:
        print(f"pyre: cd: {args[1]}: No such file or directory")
    except NotADirectoryError:
        print(f"pyre: cd: {args[1]}: Not a directory")
    return True  # Return True to indicate successful execution


def builtin_source(args: list[str]) -> bool:
    """
    Execute commands from a file in the current shell environment.
    """
    if len(args) < 2:  # If no filename argument is provided print an error message
        print("pyre: source: filename argument required")
        return True

    # Expand the filename argument to an absolute path, handling user home directory and environment variables
    target_path = os.path.expanduser(os.path.expandvars(args[1]))

    if not os.path.exists(target_path):  # If the specified file does not exist, print an error message
        print(f"pyre: {args[0]}: {args[1]}: No such file or directory")
        return True

    # Local import to avoid circular import issues
    from pyre.core.executor import execute_command

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()  # Remove leading and trailing whitespace from the line

                if not line or line.startswith("#"):
                    continue  # Skip empty lines and comments

                # Create a lexer for parsing the line from the file, treating special characters as punctuation
                lexer = shlex.shlex(line, posix=True, punctuation_chars="<>|&")
                lexer.whitespace_split = True

                line_args = list(lexer)  # Convert the lexer output to a list of arguments

                if not line_args:  # If the line is empty after parsing, skip to the next line
                    continue

                execute_command(line_args)  # Execute the command represented by the parsed arguments

    except Exception as e:
        print(f"pyre: {args[0]}: error executing {args[1]}: {e}")

    return True  # Return True to indicate successful execution


def _handle_assignment_builtin(args: list[str], target_dict: MutableMapping[str, str]) -> bool:
    """
    Handle assignment for built-in commands alias and export.
    """
    if len(args) == 1:
        for key, val in target_dict.items():  # Print the current assignments in the target dictionary
            print(f"{key}='{val}'")
        return True

    # Join the arguments after the command name to form the full assignment string
    full_assignment: str = " ".join(args[1:])

    if "=" in full_assignment:
        # Split the assignment string into key and value at the first '=' character
        key, value = full_assignment.split("=", 1)

        # Expand environment variables in the value and strip any surrounding quotes
        expanded_value: str = os.path.expandvars(value.strip().strip("'\""))

        # Update the target dictionary with the new assignment
        target_dict[key.strip()] = expanded_value

    return True


def builtin_alias(args: list[str]) -> bool:
    """
    Create and read aliases for commands.
    """
    return _handle_assignment_builtin(args, shell_config.aliases)


def builtin_export(args: list[str]) -> bool:
    """
    Create and read exports for environment variables.
    """
    return _handle_assignment_builtin(args, os.environ)


# Built-in commands mapping: command name to function
BUILTIN_COMMANDS: Final[dict[str, BuiltinFunction]] = {
    "exit": builtin_exit,
    "history": builtin_history,
    "cd": builtin_cd,
    "alias": builtin_alias,
    "export": builtin_export,
    "source": builtin_source,
    ".": builtin_source,  # POSIX support to use '.' as an alias for 'source'
}
