import glob
import os

from pyre.core.builtins import BUILTIN_COMMANDS
from pyre.core.config import shell_config
from pyre.utils.expansions import expand_braces
from pyre.utils.redirections import handle_redirections


def execute_command(args: list[str]) -> bool:
    """
    Execute built-in and external commands applied global redirections.
    Returns True to continue execution, False to close the shell.
    """
    if not args:  # If no arguments are provided, return True to continue execution
        return True

    if "|" in args:  # If a pipe is present in the arguments, handle the pipe execution
        pipe_index: int = args.index("|")  # Find the index of the pipe symbol in the arguments
        left_args: list[str] = args[:pipe_index]  # Get the arguments to the left of the pipe symbol
        right_args: list[str] = args[pipe_index + 1:]  # Get the arguments to the right of the pipe symbol

        r, w = os.pipe()  # Create a pipe with read and write file descriptors

        pid_left: int = os.fork()  # Fork a child process to execute the left command of the pipe
        if pid_left == 0:  # Child process for the left command
            os.close(r)  # Close the read end of the pipe in the child process
            os.dup2(w, 1)  # Duplicate the write end of the pipe to standard output (stdout)
            os.close(w)  # Close the original write end of the pipe in the child process

            execute_command(left_args)  # Execute the left command of the pipe recursively
            os._exit(0)  # Exit the child process after executing the left command

        pid_right: int = os.fork()  # Fork another child process to execute the right command of the pipe
        if pid_right == 0:  # Child process for the right command
            os.close(w)  # Close the write end of the pipe in the child process
            os.dup2(r, 0)  # Duplicate the read end of the pipe to standard input (stdin)
            os.close(r)  # Close the original read end of the pipe in the child process

            execute_command(right_args)  # Execute the right command of the pipe recursively
            os._exit(0)  # Exit the child process after executing the right command

        os.close(r)  # Close the read end of the pipe in the parent process
        os.close(w)  # Close the write end of the pipe in the parent process

        os.waitpid(pid_left, 0)  # Wait for the left child process to finish
        os.waitpid(pid_right, 0)  # Wait for the right child process to finish

        return True  # Return True to indicate successful execution of the piped commands

    args: list[str] = shell_config.resolve_alias(args)  # Resolve any aliases for the command before execution

    braced_args: list[str] = []  # Initialize an empty list to store the arguments after brace expansion

    for arg in args:
        # Recursively expand braces in each argument and add the expanded results to the braced_args list
        braced_args.extend(expand_braces(arg))

    # Update the arguments list with the expanded arguments after brace expansion
    args: list[str] = braced_args

    # Replace the special variable "$?" with the last exit status of the previous command in the arguments
    args = [arg.replace("$?", str(shell_config.last_exit_status)) for arg in args]

    # Expand environment variables and user home directory in the arguments
    args: list[str] = [os.path.expanduser(os.path.expandvars(arg)) for arg in args]

    expanded_args: list[str] = []  # Initialize an empty list to store the expanded arguments

    for arg in args:
        if any(char in arg for char in "*?[]"):  # Check if the argument contains any wildcard characters for globbing
            matches = glob.glob(arg)  # Use glob to find all files and directories that match the wildcard pattern

            if matches:  # If there are matches, sort them and add them to the expanded arguments list
                expanded_args.extend(sorted(matches))

            else:  # If there are no matches, keep the original argument in the expanded arguments list
                expanded_args.append(arg)

        else:  # If the argument does not contain any wildcard characters, keep it as is in the expanded arguments list
            expanded_args.append(arg)

    args: list[str] = expanded_args  # Update the arguments list with the expanded arguments

    saved_stdin: int = os.dup(0)  # Save the original standard input file descriptor
    saved_stdout: int = os.dup(1)  # Save the original standard output file descriptor

    try:
        clean_args: list[str] = handle_redirections(args)

        # If there are no arguments left after handling redirections, return True to indicate successful execution
        if not clean_args:
            return True

        # Check if the last argument is "&" to indicate background execution
        background: bool = False

        # Check if the last argument is "&" to indicate background execution
        if clean_args[-1] == "&":
            background: bool = True
            clean_args.pop()  # Remove the "&" symbol from the arguments list to indicate background execution

            # If there are no arguments left after removing the "&" symbol, return True to indicate successful execution
            if not clean_args:
                return True

        command: str = clean_args[0]

        # Build-in commands
        if command in BUILTIN_COMMANDS:
            return BUILTIN_COMMANDS[command](clean_args)

        # External commands
        if command in ["ls", "grep", "egrep", "fgrep"]:
            if not any(arg.startswith("--color") for arg in clean_args):
                clean_args.append("--color=auto")

        pid: int = os.fork()  # Create a child process to execute the command

        if pid == 0:  # Child process
            try:
                # Replace the current process with the new command, passing the arguments
                os.execvp(clean_args[0], clean_args)
            except FileNotFoundError:
                print(f"pyre: {command}: command not found")
                os._exit(127)  # Exit child process with error code 127 (command not found)
            except Exception as e:
                print(f"pyre: {command}: {e}")
                os._exit(1)  # Exit child process with error code

        elif pid > 0:  # Parent process
            if background:
                # If the command is to be executed in the background,
                # print a message indicating that it is running in the background
                print(f"[{pid}] {command} command is running in the background")
                shell_config.last_exit_status = 0

            else:
                try:
                    _, status = os.waitpid(pid, 0)  # Wait for the child process to finish

                    if os.WIFEXITED(status):
                        # If the child process exited normally, update the last exit status in the shell configuration
                        shell_config.last_exit_status = os.WEXITSTATUS(status)

                    else:
                        # If the child process did not exit normally, set the last exit status to 1 (indicating an error)
                        shell_config.last_exit_status = 1

                except KeyboardInterrupt:
                    print()  # Print a new line to avoid overwriting the prompt

                    # Set the last exit status to 130 (indicating termination by Ctrl+C)
                    shell_config.last_exit_status = 130

        return True  # Return True to indicate successful execution

    finally:
        os.dup2(saved_stdin, 0)  # Restore the original standard input file descriptor
        os.dup2(saved_stdout, 1)  # Restore the original standard output file descriptor
        os.close(saved_stdin)  # Close the saved standard input file descriptor
        os.close(saved_stdout)  # Close the saved standard output file descriptor
