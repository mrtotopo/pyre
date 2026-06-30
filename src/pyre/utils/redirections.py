import os
from typing import Final

# Define a dictionary that maps output redirection operators to their
# corresponding file opening flags and target file descriptors.

# O_WRONLY: Open for writing only
# O_CREAT: Create the file if it does not exist
# O_TRUNC: Truncate the file to zero length if it already exists
# 0o644: Set the file permissions to rw-r--r-- (owner can read/write, group and others can read)

OUTPUT_REDIRECTIONS: Final[dict[str, tuple[int, list[int]]]] = {
    "&>": (os.O_WRONLY | os.O_CREAT | os.O_TRUNC, [1, 2]),
    "2>>": (os.O_WRONLY | os.O_CREAT | os.O_APPEND, [2]),
    "2>": (os.O_WRONLY | os.O_CREAT | os.O_TRUNC, [2]),
    ">>": (os.O_WRONLY | os.O_CREAT | os.O_APPEND, [1]),
    ">": (os.O_WRONLY | os.O_CREAT | os.O_TRUNC, [1]),
}


def handle_redirections(args: list[str]) -> list[str]:
    """
    Handle input and output redirections in the command arguments.
    """
    fixed_args: list[str] = []  # Initialize a list to store the fixed command arguments without redirection operators
    i: int = 0  # Initialize an index to iterate through the command arguments

    while i < len(args):
        # Handle special cases for redirection operators that may be split into multiple arguments
        if args[i] == "2":
            # Handle cases where 2>&1 is split as ['2', '>', '&', '1'] or ['2', '>', '&1']
            if i + 2 < len(args) and (
                    (args[i + 1] == ">&" and args[i + 2] == "1") or (args[i + 1] == ">" and args[i + 2] == "&1")):
                fixed_args.append("2>&1")
                i += 3
                continue

            # Detect 2> and 2>>
            if i + 1 < len(args) and args[i + 1] in [">", ">>"]:
                fixed_args.append("2" + args[i + 1])
                i += 2
                continue

        # Fallback for 2>&1 if split as ['2>', '&1']
        if args[i] == "2>" and i + 1 < len(args) and args[i + 1] == "&1":
            fixed_args.append("2>&1")
            i += 2
            continue

        # Detect &> (split as ['&', '>'])
        if args[i] == "&" and i + 1 < len(args) and args[i + 1] == ">":
            fixed_args.append("&>")
            i += 2
            continue

        # Append the current argument to the fixed arguments list if it is not a special case
        fixed_args.append(args[i])
        i += 1

    args: list[str] = fixed_args  # Update the command arguments with the fixed arguments after handling special cases

    clean_args: list[str] = []  # Initialize a list to store the cleaned command arguments without redirection operators
    index: int = 0  # Initialize an index to iterate through the command arguments

    while index < len(args):
        operator = args[index]  # Get the current argument to check if it's a redirection operator

        if operator in OUTPUT_REDIRECTIONS:
            if index + 1 < len(args):
                filename: str = args[index + 1]  # Get the filename specified after the redirection operator

                # Get the corresponding flags and target file descriptors for the redirection operator
                flags, target_fds = OUTPUT_REDIRECTIONS[operator]

                # Open the file with the specified flags and permissions, creating it if it doesn't exist
                fd: int = os.open(filename, flags, 0o644)

                # Redirect the channel to the specified target (1, 2 or both)
                for target_fd in target_fds:
                    os.dup2(fd, target_fd)

                os.close(fd)  # Close the file descriptor after redirection to avoid resource leaks
                index += 1  # Skip the filename argument since it has been processed

        elif operator == "2>&1":
            os.dup2(1, 2)  # Clone standard output (1) to standard error (2)

        # Redirect standard input from a string (<<<): Use a string as input
        elif args[index] == "<<<":
            if index + 1 < len(args):
                content: str = args[index + 1] + "\n"  # Add a newline to the content to simulate end-of-line behavior
                r, w = os.pipe()  # Create a pipe to write the content to standard input

                os.write(w, content.encode('utf-8'))  # Write the content to the write end of the pipe
                os.close(w)  # Close the write end of the pipe after writing the content
                os.dup2(r, 0)  # Redirect the read end of the pipe to standard input (stdin)
                os.close(r)  # Close the read end of the pipe after redirection to avoid resource leaks

                index += 1  # Skip the content argument since it has been processed

        # Redirect standard input from a here-document (<<): Read input until a specified delimiter is encountered
        elif args[index] == "<<":
            if index + 1 < len(args):
                delimiter: str = args[index + 1]  # Get the delimiter specified after the here-document operator

                # Initialize a list to store the lines of input until the delimiter is encountered
                lines: list[str] = []

                while True:
                    try:
                        # Prompt the user for input with a "> " prompt and read the input line
                        line = input("> ")

                        if line == delimiter:
                            break

                        lines.append(line)  # Add the input line to the list of lines if it is not the delimiter

                    except (EOFError, KeyboardInterrupt):
                        break  # Exit the loop if the user sends an EOF (Ctrl+D) or interrupts the input (Ctrl+C)

                content = "\n".join(lines) + "\n"
                r, w = os.pipe()  # Create a pipe to write the content to standard input

                os.write(w, content.encode('utf-8'))  # Write the content to the write end of the pipe
                os.close(w)  # Close the write end of the pipe after writing the content
                os.dup2(r, 0)  # Redirect the read end of the pipe to standard input (stdin)
                os.close(r)  # Close the read end of the pipe after redirection to avoid resource leaks

                index += 1  # Skip the delimiter argument since it has been processed

        # Redirect standard input from a file (<): Read input from a specified file
        elif args[index] == "<":
            if index + 1 < len(args):
                filename: str = args[index + 1]  # Get the filename specified after the input redirection operator

                try:
                    fd: int = os.open(filename, os.O_RDONLY)  # Open the file in read-only mode
                    os.dup2(fd, 0)  # Redirect the file descriptor to standard input (stdin)
                    os.close(fd)  # Close the file descriptor after redirection to avoid resource leaks

                except FileNotFoundError:
                    # If the specified file does not exist, print an error message and return an empty list
                    print(f"pyre: {filename}: No such file or directory")
                    return []

                index += 1  # Skip the filename argument since it has been processed

        # Handle the case where the argument is not a redirection operator, and add it to the cleaned arguments list
        else:
            clean_args.append(args[index])

        index += 1  # Move to the next argument in the list

    # After processing all arguments, return the cleaned list of command arguments without redirection operators
    return clean_args
