import pkgutil
from types import ModuleType


def get_subpackage_names(package: ModuleType) -> list[str]:
    """Get subpackage names of specified package.

    Parameters
    ----------
    package : ModuleType
        Package to inspect

    Returns
    -------
    list[str]
        List of subpackage names

    Raises
    ------
    ValueError
        If specified package is not a package
    """
    if not hasattr(package, '__path__'):
        raise ValueError(f'"{package.__name__}" is not a package') from None

    return [
        module.name
        for module in pkgutil.iter_modules(package.__path__)
        if module.ispkg
    ]
