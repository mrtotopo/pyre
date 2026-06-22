import glob
import os

import readline


def get_system_commands(prefix: str) -> list[str]:
    """
    Search directories in the system PATH for executables that start with the given prefix.
    """
    commands: set = set()
    path_env: str = os.environ.get("PATH", "") # Get PATH environment variable
    directories: list[str] = path_env.split(os.pathsep) # Get directories in PATH

    for directory in directories:
        if os.path.isdir(directory): # Check if is a directory
            try:
                for file in os.listdir(directory): # Get files in the directory
                    if file.startswith(prefix):
                        full_path: str = os.path.join(directory, file) # Get the fullpath of the file
                        if os.access(full_path, os.X_OK): # If the file has execute permissions
                            commands.add(file) # It's added to the list of commands
            except PermissionError:
                continue

    return list(commands)


def smart_completer(text: str, state: int) -> str | None:
    """
    A custom completer function that provides autocompletion for commands and paths based on the current input.
    """
    buffer: str = readline.get_line_buffer() # Get written text in the current line

    if " " not in buffer.lstrip():
        matches: list[str] = get_system_commands(text)  # Search for commands in PATH
        matches.extend(glob.glob(text + '*'))  # Add local files
        matches: list[str] = sorted(list(set(matches)))  # Remove duplicates and sort
    else:
        matches: list[str] = glob.glob(text + '*')  # Search local files or directories

    if state < len(matches):
        return matches[state]
    else:
        return None
