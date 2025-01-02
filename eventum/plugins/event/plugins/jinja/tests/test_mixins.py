from typing import Any

import pytest
from pydantic import BaseModel

from eventum.plugins.event.plugins.jinja.mixins import (
    TemplateAliasesUniquenessValidatorMixin,
    TemplateSingleItemElementsValidatorMixin)


class ValidatedAliasesConfig(
    TemplateAliasesUniquenessValidatorMixin,
    BaseModel
):
    templates: list[dict[str, Any]]

    __test__ = False


class ValidatedSingleItemElementsConfig(
    TemplateSingleItemElementsValidatorMixin,
    BaseModel
):
    templates: list[dict[str, Any]]

    __test__ = False


def test_alias_uniqueness_validator_mixin():
    with pytest.raises(ValueError):
        ValidatedAliasesConfig(templates=[{'a': 1}, {'a': 2}])


def test_single_item_elements_validator_mixin():
    with pytest.raises(ValueError):
        ValidatedSingleItemElementsConfig(templates=[{'a': 1, 'b': 2}])
