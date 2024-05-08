import pytest
from eventum.utils.fs import validate_jinja_filename, validate_yaml_filename


def test_validate_yaml_filename():
    validate_yaml_filename('correct.yml')
    validate_yaml_filename('correct.yaml')

    with pytest.raises(ValueError):
        validate_yaml_filename('wrong.mammal')

    with pytest.raises(ValueError):
        validate_yaml_filename('whoami')


def test_validate_jinja_filename():
    validate_jinja_filename('correct.jinja')

    with pytest.raises(ValueError):
        validate_yaml_filename('wrong.john')

    with pytest.raises(ValueError):
        validate_yaml_filename('whoami')
