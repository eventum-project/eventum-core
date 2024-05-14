def prettify_errors(errors: list[dict]) -> str:
    messages: list[str] = []

    for error in errors:
        match error:
            case {'type': 'extra_forbidden', 'loc': loc}:
                msg = 'Field is unrecognized'
                messages.append(f'Field \"{".".join(loc)}\" - {msg}')
            case {'msg': msg, 'loc': loc}:
                messages.append(f'Field \"{".".join(loc)}\" - {msg}')

    return '; '.join(messages)
