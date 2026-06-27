import os

import readline

from pyre.utils.autocompletions import smart_completer, custom_display_matches
from pyre.utils.history import setup_history, display_history
from pyre.utils.ui import print_prompt_header, get_input_prompt


def main():
    setup_history()  # Initialize the command history

    readline.set_completer(smart_completer)  # Set the custom completer function for autocompletion

    if getattr(readline, "backend", "") == "editline" or "libedit" in getattr(readline, "__doc__", ""):
        readline.parse_and_bind("bind ^I rl_complete")  # Set Tab key to trigger autocompletion for libedit
    else:
        readline.parse_and_bind("tab: complete")  # Set Tab key to trigger autocompletion for GNU

    # Set the custom display function for autocompletion matches
    readline.set_completion_display_matches_hook(custom_display_matches)

    while True:
        print_prompt_header()  # Print the prompt header with the current user, hostname, and working directory
        prompt: str = get_input_prompt()  # Get the input prompt string

        user_input: str = input(prompt)  # Wait the user input

        if not user_input:
            continue

        args: list[str] = user_input.split()  # Get arguments from the user input
        command: str = args[0]  # Get the command

        if command == "exit":
            break

        if command == "history":
            display_history()
            continue

        if command == "cd":
            try:
                if len(args) == 1:
                    os.chdir(os.path.expanduser("~"))  # If no argument is provided, change to the home directory
                else:
                    os.chdir(args[1])  # Move to the specified directory
            except FileNotFoundError:
                print(f"pyre: cd: {args[1]}: No such file or directory")
            except NotADirectoryError:
                print(f"pyre: cd: {args[1]}: Not a directory")
            continue

        pid: int = os.fork()  # Create a child process to execute the command

        if pid == 0:  # Child process
            try:
                os.execvp(command, args)  # Replace the current process with the new command, passing the arguments
            except FileNotFoundError:
                print(f"pyre: {command}: command not found")
            except Exception as e:
                print(f"pyre: {command}: {e}")
                os._exit(1)  # Exit child process with error code

        elif pid > 0:  # Parent process
            os.wait()  # Wait for the child process to finish


if __name__ == '__main__':
    main()
