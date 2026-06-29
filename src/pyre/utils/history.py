import atexit
import os.path

try:
    import gnureadline as readline
except ImportError:
    import readline


def setup_history() -> None:
    """
    Setup history file
    """
    history_file: str = os.path.join(os.path.expanduser("~"), ".pyre_history")  # Path to the history file

    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass  # If the history file doesn't exist, ignore the error

    readline.set_history_length(1000)  # Set the maximum number of lines to save in the history file

    # Register the function to write the history file on exit
    atexit.register(readline.write_history_file, history_file)


def display_history() -> None:
    """
    Display the command history
    """
    length: int = readline.get_current_history_length()  # Get the number of commands in the history

    for i in range(1, length + 1):
        item: str = readline.get_history_item(i)  # Get the command at the given index in the history
        if item:
            print(f"{i:>5}  {item}")
