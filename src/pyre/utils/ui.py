import getpass
import os
import socket
import sys

GREEN: str = "\033[32m"
BLUE: str = "\033[34m"
RESET: str = "\033[0m"  # Return to default color
BOLD: str = "\033[1m"

RL_RESET: str = "\x01\033[0m\x02"
RL_BOLD: str = "\x01\033[1m\x02"


def print_prompt_header() -> None:
    """
    Print the prompt header with the current user, hostname, and working directory.
    """
    current_path: str = os.getcwd()  # Get the current working directory
    home_dir: str = os.path.expanduser("~")  # Get the home directory path

    if current_path.startswith(home_dir):
        current_path: str = current_path.replace(home_dir, "~", 1)  # Replace the home directory with ~

    username: str = getpass.getuser()  # Get the username
    hostname: str = socket.gethostname()  # Get the hostname

    brackets_start: str = f"{BOLD}[{RESET}"
    brackets_end: str = f"{BOLD}]{RESET}"

    user_host: str = f"{BOLD}{GREEN}{username}@{hostname}{RESET}"
    path: str = f"{BOLD}{BLUE}{current_path}{RESET}"

    print(f"\n{user_host} {brackets_start}{path}{brackets_end}")  # username@hostname [path]


def get_input_prompt() -> str:
    """
    Return the input prompt string
    """
    return f"{RL_BOLD}❯{RL_RESET} "


def redraw_input_line(user_text: str) -> None:
    """
    Redraw the input line with the current prompt and user input.
    """
    print_prompt_header()

    # Clean the prompt string by removing the readline escape sequences
    clean_prompt: str = get_input_prompt().replace("\x01", "").replace("\x02", "")

    sys.stdout.write(clean_prompt + user_text)  # Write the prompt and user input to stdout
    sys.stdout.flush()  # Show the prompt and user input immediately
