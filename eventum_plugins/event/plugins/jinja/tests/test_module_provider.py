import pytest
import eventum_plugins.event.plugins.jinja.modules as modules
import eventum_plugins.event.plugins.jinja.modules.rand as rand
from eventum_plugins.event.plugins.jinja.module_provider import ModuleProvider


def test_module_loader():
    module_provider = ModuleProvider(modules.__name__)
    assert module_provider['rand'] == rand


def test_module_loader_invalid():
    module_provider = ModuleProvider(modules.__name__)

    with pytest.raises(KeyError):
        module_provider['unexistent']
