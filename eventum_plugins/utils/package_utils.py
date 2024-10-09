import importlib
import pkgutil


def get_subpackage_names(package_name: str) -> list[str]:
    """Get subpackage names list of specified package.

    Parameters
    ----------
    package_name : str
        Absolute name of the package

    Returns
    -------
    list[str]
        List of subpackage names without parent part

    Raises
    ------
    ValueError
        If specified package is not found or not a package
    """
    try:
        package = importlib.import_module(package_name)
    except ModuleNotFoundError:
        raise ValueError(f'Package "{package_name}" not found') from None

    if not hasattr(package, '__path__'):
        raise ValueError(f'"{package_name}" is not a package') from None

    subpackages = [
        module.name
        for module in pkgutil.iter_modules(package.__path__)
        if module.ispkg
    ]

    return subpackages
