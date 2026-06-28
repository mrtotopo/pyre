import os


def handle_redirections(args: list[str]) -> list[str]:
    """
    Handle input and output redirections in the command arguments.
    """
    clean_args: list[str] = []
    index: int = 0

    while index < len(args):
        if args[index] == ">":
            if index + 1 < len(args):
                filename: str = args[index + 1]

                # O_WRONLY: Open for writing only
                # O_CREAT: Create the file if it does not exist
                # O_TRUNC: Truncate the file to zero length if it already exists
                # 0o644: Set the file permissions to rw-r--r-- (owner can read/write, group and others can read)

                # Open the file for writing, creating it if it doesn't exist, and truncating it if it does
                fd: int = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)

                os.dup2(fd, 1)  # Redirect standard output (stdout) to the file descriptor
                os.close(fd)  # Close the file descriptor after redirection
                index += 1  # Skip the filename argument after redirection

        elif args[index] == "<":
            if index + 1 < len(args):
                filename: str = args[index + 1]

                try:
                    fd: int = os.open(filename, os.O_RDONLY)  # Open the file for reading only
                    os.dup2(fd, 0)  # Redirect standard input (stdin) to the file descriptor
                    os.close(fd)  # Close the file descriptor after redirection
                except FileNotFoundError:
                    print(f"pyre: {filename}: No such file or directory")
                    return []  # Return an empty list to indicate an error in redirection

                index += 1  # Skip the filename argument after redirection

        else:
            clean_args.append(args[index])  # Add the argument to the clean_args list if it's not a redirection operator

        index += 1

    return clean_args
