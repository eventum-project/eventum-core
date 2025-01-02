import os


def resolve_config_path(path: str) -> str:
    """Resolve path to configuration file from current location. If
    resolved absolute path does not exists return original path."""
    if os.path.isabs(path):
        return path
    else:
        config_path = os.path.join(
            os.path.abspath(os.getcwd()), path
        )

        if not os.path.exists(config_path):
            config_path = path

        return config_path
