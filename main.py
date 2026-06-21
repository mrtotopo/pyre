import getpass
import os
import socket


def main():
    while True:
        current_path = os.getcwd()
        home_dir = os.path.expanduser("~")

        if current_path.startswith(home_dir):
            current_path = current_path.replace(home_dir, "~", 1)

        username = getpass.getuser()
        hostname = socket.gethostname()

        user_input = input(f"{username}@{hostname}:{current_path} $ ")

        if not user_input:
            continue

        args = user_input.split()
        command = args[0]

        if command == "exit":
            break

        if command == "cd":
            try:
                if len(args) == 1:
                    os.chdir(os.path.expanduser("~"))
                else:
                    os.chdir(args[1])
            except FileNotFoundError:
                print(f"pyre: cd: {args[1]}: No such file or directory")
            except NotADirectoryError:
                print(f"pyre: cd: {args[1]}: Not a directory")
            continue

        pid = os.fork()

        if pid == 0:  # Child process
            try:
                os.execvp(command, args)
            except FileNotFoundError:
                print(f"pyre: {command}: command not found")
            except Exception as e:
                print(f"pyre: {command}: {e}")
                os._exit(1)  # Exit child process with error code

        elif pid > 0:  # Parent process
            os.wait()  # Wait for the child process to finish


if __name__ == '__main__':
    main()
