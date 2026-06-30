def expand_braces(arg: str) -> list[str]:
    """
    Brackets expansion recursively.
    Support list {a,b,c} and ranges {1..3}, {a..t}
    """
    if '{' not in arg or '}' not in arg:
        # If there are no braces in the argument, return it as is after replacing placeholders back to original braces
        return [arg.replace('\x01', '{').replace('\x02', '}')]

    # Find the position of the first closing brace in the argument
    end: int = arg.find('}')

    # Find the position of the last opening brace before the closing brace
    start: int = arg.rfind('{', 0, end)

    if start == -1:
        # If there is no opening brace before the closing brace,
        # return the argument as is after replacing placeholders back to original braces
        return [arg.replace('\x01', '{').replace('\x02', '}')]

    prefix: str = arg[:start]  # Get the part of the argument before the opening brace
    inner: str = arg[start + 1:end]  # Get the part of the argument inside the braces
    suffix: str = arg[end + 1:]  # Get the part of the argument after the closing brace

    options: list[str] = []  # Initialize an empty list to store the options for expansion

    if ',' in inner:
        # If there are commas in the inner part, split it into options
        options = inner.split(',')

    elif '..' in inner:
        # If there is a range specified with '..', split it into start and end values
        parts = inner.split('..')

        if len(parts) == 2:
            # Check if both parts are digits (for numeric ranges) or single letters (for alphabetic ranges)
            if parts[0].lstrip('-').isdigit() and parts[1].lstrip('-').isdigit():
                # If both parts are digits, convert them to integers and generate the range of numbers
                s, e = int(parts[0]), int(parts[1])
                step: int = 1 if s <= e else -1
                options: list[str] = [str(i) for i in range(s, e + step, step)]

            # Check if both parts are single alphabetic characters (for alphabetic ranges)
            elif len(parts[0]) == 1 and len(parts[1]) == 1 and parts[0].isalpha() and parts[1].isalpha():
                # If both parts are single letters, convert them to their ASCII values and generate the range of letters
                s, e = ord(parts[0]), ord(parts[1])
                step: int = 1 if s <= e else -1
                options: list[str] = [chr(i) for i in range(s, e + step, step)]

    # If there are options generated from the inner part, recursively expand each option
    # and combine them with the prefix and suffix
    if options:
        # Initialize an empty list to store the final expanded results
        results: list[str] = []

        for opt in options:
            # Recursively expand the argument with the current option and combine it with the prefix and suffix
            results.extend(expand_braces(prefix + opt + suffix))

        # Remove duplicates while preserving order and return the final list of expanded arguments
        return list(dict.fromkeys(results))

    else:
        # If there are no options generated from the inner part,
        # replace the braces with placeholders and recursively expand the argument
        temp_arg = prefix + '\x01' + inner + '\x02' + suffix

        # Recursively expand the argument with placeholders and return the final list of expanded arguments
        return expand_braces(temp_arg)
