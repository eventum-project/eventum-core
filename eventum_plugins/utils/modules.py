import importlib
import pkgutil


def get_module_names(package_name: str) -> list[str]:
    package = importlib.import_module(package_name)

    module_names = []
    for module_info in pkgutil.walk_packages(package.__path__):
        module_names.append(module_info.name)

    return module_names
