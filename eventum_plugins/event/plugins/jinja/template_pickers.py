import random
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Unpack, assert_never

from eventum_plugins.event.plugins.jinja.config import (
    TemplateConfigForChanceMode, TemplateConfigForFSMMode,
    TemplateConfigForGeneralModes, TemplatePickingMode)
from eventum_plugins.event.plugins.jinja.context import EventContext

T = TypeVar('T', bound=TemplateConfigForGeneralModes)


class TemplatePicker(ABC, Generic[T]):
    """Base picker of templates."""

    def __init__(
        self,
        config: dict[str, T]
    ) -> None:
        self._config = config
        self._aliases = tuple(self._config.keys())

    @abstractmethod
    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        """Pick template.

        Returns
        -------
        tuple[str, ...]
            Aliases of picked templates
        """
        ...


class AllTemplatePicker(TemplatePicker[TemplateConfigForGeneralModes]):
    def __init__(
        self,
        config: dict[str, TemplateConfigForGeneralModes]
    ) -> None:
        super().__init__(config)

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        return self._aliases


class AnyTemplatePicker(TemplatePicker[TemplateConfigForGeneralModes]):
    def __init__(
        self,
        config: dict[str, TemplateConfigForGeneralModes]
    ) -> None:
        super().__init__(config)

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        return (random.choice(self._aliases), )


class ChanceTemplatePicker(TemplatePicker[TemplateConfigForChanceMode]):
    def __init__(
        self,
        config: dict[str, TemplateConfigForChanceMode]
    ) -> None:
        super().__init__(config)
        self._chances = [conf.chance for conf in self._config.values()]

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        return tuple(
            random.choices(self._aliases, weights=self._chances, k=1)
        )


class SpinTemplatePicker(TemplatePicker[TemplateConfigForGeneralModes]):
    def __init__(
        self,
        config: dict[str, TemplateConfigForGeneralModes]
    ) -> None:
        super().__init__(config)
        self._spin_index = 0

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        alias = self._aliases[self._spin_index]

        self._spin_index += 1
        if self._spin_index == len(self._aliases):
            self._spin_index = 0

        return (alias, )


class FSMTemplatePicker(TemplatePicker[TemplateConfigForFSMMode]):
    def __init__(
        self,
        config: dict[str, TemplateConfigForFSMMode]
    ) -> None:
        super().__init__(config)
        self._state = self._get_initial_state()

    def _get_initial_state(self) -> str:
        """Get alias of initial state.

        Returns
        -------
        str
            Alias of state

        Raises
        ------
        RuntimeError
            If no initial state found
        """
        for alias, conf in self._config.items():
            if conf.initial:
                return alias

        raise RuntimeError('No initial state found')

    def _check_transition(self, **kwargs: Unpack[EventContext]) -> None:
        """Check condition of current state and perform transition to
        next state if it is true.
        """
        transition = self._config[self._state].transition

        if transition is None:
            return

        if transition.when.check(**kwargs):
            self._state = transition.to

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        self._check_transition(**kwargs)
        return (self._state, )


def get_picker_class(
    picking_mode: TemplatePickingMode
) -> type[TemplatePicker]:
    """Return specific picker class depending on picking mode.

    Parameters
    ----------
        picking_mode : TemplatePickingMode
            Picking mode
    """
    match picking_mode:
        case TemplatePickingMode.ALL:
            return AllTemplatePicker
        case TemplatePickingMode.ANY:
            return AnyTemplatePicker
        case TemplatePickingMode.CHANCE:
            return ChanceTemplatePicker
        case TemplatePickingMode.SPIN:
            return SpinTemplatePicker
        case TemplatePickingMode.FSM:
            return FSMTemplatePicker
        case mode:
            assert_never(mode)
