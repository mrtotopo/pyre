import getpass
import os
import readline
import socket

from pyre.utils.autocompletions import smart_completer

# Ansi color codes for the prompt
GREEN = "\x01\033[32m\x02"
BLUE = "\x01\033[34m\x02"
RESET = "\x01\033[0m\x02" # Return to default color
BOLD = "\x01\033[1m\x02"

def main():
    readline.set_completer(smart_completer)  # Set the custom completer function for autocompletion
    readline.parse_and_bind('tab: complete')  # Set Tab key to trigger autocompletion

    while True:
        current_path = os.getcwd()
        home_dir = os.path.expanduser("~")  # Get the home directory path

        if current_path.startswith(home_dir):
            current_path = current_path.replace(home_dir, "~", 1)  # Replace the home directory with ~

        username = getpass.getuser()
        hostname = socket.gethostname()

        prompt = f"{BOLD}{GREEN}{username}@{hostname}{RESET}:{BOLD}{BLUE}{current_path}{RESET} {BOLD}${RESET} "
        user_input = input(prompt)  # Wait the user input

        if not user_input:
            continue

        args = user_input.split()  # Get arguments from the user input
        command = args[0]  # Get the command

        if command == "exit":
            break

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

        pid = os.fork()  # Create a child process to execute the command

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
