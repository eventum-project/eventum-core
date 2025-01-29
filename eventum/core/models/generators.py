from pydantic import Field, RootModel

from eventum.core.models.parameters.generator import GeneratorParameters


class Generators(RootModel, frozen=True):
    """List of generators."""
    root: tuple[GeneratorParameters, ...] = Field(min_length=1)
