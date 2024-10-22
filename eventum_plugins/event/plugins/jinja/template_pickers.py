import random
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Unpack, assert_never

from eventum_plugins.event.plugins.jinja.config import (
    TemplateConfigForChanceMode, TemplateConfigForFSMMode,
    TemplateConfigForGeneralModes, TemplatePickingMode)
from eventum_plugins.event.plugins.jinja.context import EventContext

T = TypeVar('T', bound=TemplateConfigForGeneralModes)


class TemplatePicker(ABC, Generic[T]):
    """Base picker of templates.
    Parameters
    ----------
    config : dict[str, T]
        Template aliases to configs mapping

    common_config : dict
        Common parameter names to values mapping

    Raises
    ------
    ValueError
        If some required parameter is missing in config
    """

    def __init__(
        self,
        config: dict[str, T],
        common_config: dict[str, Any]
    ) -> None:
        self._config = config
        self._common_config = common_config
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
    """Picker of templates for `all` picking mode."""

    def __init__(
        self,
        config: dict[str, TemplateConfigForGeneralModes],
        common_config: dict[str, Any]
    ) -> None:
        super().__init__(config, common_config)

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        return self._aliases


class AnyTemplatePicker(TemplatePicker[TemplateConfigForGeneralModes]):
    """Picker of templates for `any` picking mode."""

    def __init__(
        self,
        config: dict[str, TemplateConfigForGeneralModes],
        common_config: dict[str, Any]
    ) -> None:
        super().__init__(config, common_config)

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        return (random.choice(self._aliases), )


class ChanceTemplatePicker(TemplatePicker[TemplateConfigForChanceMode]):
    """Picker of templates for `chance` picking mode."""

    def __init__(
        self,
        config: dict[str, TemplateConfigForChanceMode],
        common_config: dict[str, Any]
    ) -> None:
        super().__init__(config, common_config)
        self._chances = [conf.chance for conf in self._config.values()]

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        return tuple(
            random.choices(self._aliases, weights=self._chances, k=1)
        )


class SpinTemplatePicker(TemplatePicker[TemplateConfigForGeneralModes]):
    """Picker of templates for `spin` picking mode."""

    def __init__(
        self,
        config: dict[str, TemplateConfigForGeneralModes],
        common_config: dict[str, Any]
    ) -> None:
        super().__init__(config, common_config)
        self._spin_index = 0

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        alias = self._aliases[self._spin_index]

        self._spin_index += 1
        if self._spin_index == len(self._aliases):
            self._spin_index = 0

        return (alias, )


class FSMTemplatePicker(TemplatePicker[TemplateConfigForFSMMode]):
    """Picker of templates for `fsm` picking mode."""

    def __init__(
        self,
        config: dict[str, TemplateConfigForFSMMode],
        common_config: dict[str, Any]
    ) -> None:
        super().__init__(config, common_config)
        self._state = self._get_initial_state()
        self._initial_pick = True

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
        if self._initial_pick:
            self._initial_pick = False
        else:
            self._check_transition(**kwargs)

        return (self._state, )


class ChainTemplatePicker(TemplatePicker[TemplateConfigForGeneralModes]):
    """Picker of templates for `chain` picking mode."""

    def __init__(
        self,
        config: dict[str, TemplateConfigForGeneralModes],
        common_config: dict[str, Any]
    ) -> None:
        super().__init__(config, common_config)
        try:
            self._chain = common_config['chain']
        except KeyError as e:
            raise ValueError(f'Common config parameter "{e}" is missing')

        self._chain_index = 0

    def pick(self, **kwargs: Unpack[EventContext]) -> tuple[str, ...]:
        alias = self._chain[self._chain_index]

        self._chain_index += 1
        if self._chain_index == len(self._chain):
            self._chain_index = 0

        return (alias, )


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
        case TemplatePickingMode.CHAIN:
            return ChainTemplatePicker
        case mode:
            assert_never(mode)
