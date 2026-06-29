import os

from pyre.core.builtins import BUILTIN_COMMANDS
from pyre.core.config import shell_config
from pyre.utils.redirections import handle_redirections


def execute_command(args: list[str]) -> bool:
    """
    Execute built-in and external commands applied global redirections.
    Returns True to continue execution, False to close the shell.
    """
    args = shell_config.resolve_alias(args)  # Resolve any aliases for the command before execution

    # Expand environment variables and user home directory in the arguments
    args = [os.path.expanduser(os.path.expandvars(arg)) for arg in args]

    saved_stdin: int = os.dup(0)  # Save the original standard input file descriptor
    saved_stdout: int = os.dup(1)  # Save the original standard output file descriptor

    try:
        clean_args: list[str] = handle_redirections(args)

        # If there are no arguments left after handling redirections, return True to indicate successful execution
        if not clean_args:
            return True

        command: str = clean_args[0]

        # Build-in commands
        if command in BUILTIN_COMMANDS:
            return BUILTIN_COMMANDS[command](clean_args)

        # External commands
        if command == "ls":
            if not any(arg.startswith("--color") for arg in clean_args):
                clean_args.append("--color=auto")

        pid: int = os.fork()  # Create a child process to execute the command

        if pid == 0:  # Child process
            try:
                # Replace the current process with the new command, passing the arguments
                os.execvp(clean_args[0], clean_args)
            except FileNotFoundError:
                print(f"pyre: {command}: command not found")
            except Exception as e:
                print(f"pyre: {command}: {e}")
                os._exit(1)  # Exit child process with error code

        elif pid > 0:  # Parent process
            try:
                os.waitpid(pid, 0)  # Wait for the child process to finish
            except KeyboardInterrupt:
                print()  # Print a new line to avoid overwriting the prompt

        return True  # Return True to indicate successful execution

    finally:
        os.dup2(saved_stdin, 0)  # Restore the original standard input file descriptor
        os.dup2(saved_stdout, 1)  # Restore the original standard output file descriptor
        os.close(saved_stdin)  # Close the saved standard input file descriptor
        os.close(saved_stdout)  # Close the saved standard output file descriptor
