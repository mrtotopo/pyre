import glob


def path_completer(text: str, state: int) -> str | None:
    """
    Simple path completer function for readline
    """
    matches = glob.glob(text + '*')
    if state < len(matches):
        return matches[state]
    else:
        return None