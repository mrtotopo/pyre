import importlib.resources
import os
import shlex


class ShellConfig:
    """
    Configuration class for the shell environment.
    """

    def __init__(self):
        self.aliases: dict[str, str] = {}

    @staticmethod
    def get_rc_path() -> str:
        """
        Get the path to the .pyrerc file in the user's home directory
        """
        return os.path.join(os.path.expanduser("~"), ".pyrerc")

    @staticmethod
    def ensure_rc_file_exists() -> None:
        """
        Ensure that the .pyrerc file exists
        """

        # Get the path to the .pyrerc file in the user's home directory
        rc_path: str = ShellConfig.get_rc_path()

        if not os.path.exists(rc_path):
            try:
                # Read the template file from the package resources
                template_text: str = importlib.resources.files("pyre.assets").joinpath("pyrerc.template").read_text(
                    encoding="utf-8")

                with open(rc_path, "w", encoding="utf-8") as f:
                    f.write(template_text)  # Write the template text to the .pyrerc file

                print(f"pyre: created .pyrerc file at {rc_path}")

            except Exception as e:
                print(f"pyre: error creating .pyrerc from template: {e}")

    def resolve_alias(self, args: list[str]) -> list[str]:
        """
        Resolve the alias for the given command
        """
        if not args:  # If the args list is empty, return it as is
            return args

        command = args[0]  # Get the command (first argument) from the args list

        if command in self.aliases:
            # Expand the alias command into a list of arguments using shlex.split
            expanded: list[str] = shlex.split(self.aliases[command])
            return expanded + args[1:]  # Append the remaining arguments after the alias expansion

        return args


# Create a global instance of ShellConfig to be used throughout the application
shell_config = ShellConfig()
