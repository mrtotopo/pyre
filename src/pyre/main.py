import os
import shlex
import signal

try:
    import gnureadline as readline
except ImportError:
    import readline

from pyre.core.config import shell_config
from pyre.core.executor import execute_command
from pyre.utils.autocompletions import smart_completer, custom_display_matches
from pyre.utils.history import setup_history
from pyre.utils.ui import print_prompt_header, get_input_prompt


def clean_zombie_children(signum, frame):
    """
    Signal handler to clean up zombie child processes.
    This function is called when a SIGCHLD signal is received, indicating that a child process has terminated.
    It uses os.waitpid to reap any terminated child processes without blocking the main process.
    """
    try:
        while True:
            # Use os.waitpid with the WNOHANG option to check for terminated child processes without blocking
            # -1 means to wait for any child process, and WNOHANG allows the function to return immediately
            # if no child has exited
            pid, status = os.waitpid(-1, os.WNOHANG)

            if pid == 0 or pid == -1:
                break

    except ChildProcessError:
        # If there are no child processes to wait for, a ChildProcessError is raised.
        pass

def main():
    # Set up the signal handler for SIGCHLD to clean up zombie child processes
    signal.signal(signal.SIGCHLD, clean_zombie_children)

    setup_history()  # Initialize the command history

    shell_config.ensure_rc_file_exists()  # Ensure that the .pyrerc file exists in the user's home directory
    rc_path = shell_config.get_rc_path()  # Get the path to the .pyrerc file in the user's home directory
    execute_command(["source", rc_path])  # Execute the commands from the .pyrerc file to set up the shell environment

    readline.set_completer(smart_completer)  # Set the custom completer function for autocompletion

    # Set the delimiters for autocompletion to include whitespace and special characters
    readline.set_completer_delims(" \t\n<>|;&")

    # Enable case-insensitive autocompletion
    readline.parse_and_bind("set completion-ignore-case on")

    if getattr(readline, "backend", "") == "editline" or "libedit" in getattr(readline, "__doc__", ""):
        readline.parse_and_bind("bind ^I rl_complete")  # Set Tab key to trigger autocompletion for libedit
    else:
        readline.parse_and_bind("tab: complete")  # Set Tab key to trigger autocompletion for GNU

    # Set the custom display function for autocompletion matches
    readline.set_completion_display_matches_hook(custom_display_matches)

    while True:
        try:
            print_prompt_header()  # Print the prompt header with the current user, hostname, and working directory
            prompt: str = get_input_prompt()  # Get the input prompt string

            user_input: str = input(prompt)  # Wait the user input
        except KeyboardInterrupt:
            print()  # Print a new line to avoid overwriting the prompt
            continue  # Restart the loop to display the prompt again
        except EOFError:
            print()  # Print a new line to avoid overwriting the prompt
            break

        # If the user input is empty or only whitespace, restart the loop to display the prompt again
        if not user_input.strip():
            continue

        # Create a lexer for parsing the user input
        lexer = shlex.shlex(user_input, posix=True, punctuation_chars="<>|&;")
        lexer.whitespace_split = True  # Split the input into tokens based on whitespace

        args: list[str] = list(lexer)  # Convert the lexer output to a list of arguments

        if not args:  # If the user input is empty after parsing, restart the loop to display the prompt again
            continue

        sub_commands: list[list[str]] = []  # List to hold sub-commands separated by semicolons
        current_cmd: list[str] = []  # List to hold the current sub-command being processed

        for arg in args:
            if arg == ";":
                if current_cmd:
                    # If a semicolon is encountered and there are arguments in the current command,
                    # add the current command to the list of sub-commands and reset the current command
                    # list for the next sub-command
                    sub_commands.append(current_cmd)
                    current_cmd = []
            else:
                current_cmd.append(arg)

        if current_cmd:
            # If there are any remaining arguments in the current command after processing all arguments,
            sub_commands.append(current_cmd)

        for cmd_args in sub_commands:
            # Execute each sub-command in the list of sub-commands.
            # If execute_command returns False (e.g., 'exit' command),
            # we terminate the shell directly by returning from main().
            if not execute_command(cmd_args):
                return


if __name__ == '__main__':
    main()
