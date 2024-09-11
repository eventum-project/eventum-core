import importlib
import pkgutil


def get_subpackage_names(package_name: str) -> list[str]:
    """Get subpackage names list of specified package.

    Parameters
    ----------
    package_name : str
        Name of the package

    Returns
    -------
    list[str]
        List of subpackage names

    Raises
    ------
    ModuleNotFoundError
        If specified package is not found

    ImportError
        If specified package cannot be imported
    """
    ModuleNotFoundError
    package = importlib.import_module(package_name)

    package_names = []
    for module_info in pkgutil.walk_packages(package.__path__):
        if module_info.ispkg:
            package_names.append(module_info.name)

    return package_names
