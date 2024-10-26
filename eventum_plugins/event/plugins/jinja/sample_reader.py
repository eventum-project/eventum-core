from typing import Callable

import tablib  # type: ignore[import-untyped]

from eventum_plugins.event.plugins.jinja.config import (CSVSampleConfig,
                                                        ItemsSampleConfig,
                                                        JSONSampleConfig,
                                                        SampleConfig,
                                                        SampleType)


class SampleLoadError(Exception):
    """Failed to load sample."""


def _load_items_sample(config: ItemsSampleConfig) -> tablib.Dataset:
    """Load sample using configuration of type `items`.

    Parameters
    ----------
    config: ItemsSampleConfig
        Sample configuration

    Returns
    -------
    tablib.Dataset
        Loaded sample
    """
    data = tablib.Dataset()
    try:
        len(config.source[0])   # check if source is a flat collection
        data.extend(config.source)
    except TypeError:
        data.extend((item, ) for item in config.source)
    return data


def _load_csv_sample(config: CSVSampleConfig) -> tablib.Dataset:
    """Load sample using configuration of type `csv`.

    Parameters
    ----------
    config: CSVSampleConfig
        Sample configuration

    Returns
    -------
    tablib.Dataset
        Loaded sample

    Raises
    ------
    OSError
        If some error occurs during sample loading
    """
    data = tablib.Dataset()
    with open(config.source) as f:
        data.load(
            in_stream=f,
            format='csv',
            headers=config.header,
            delimiter=config.delimiter
        )
        return data


def _load_json_sample(config: JSONSampleConfig) -> tablib.Dataset:
    """Load sample using configuration of type `json`.

    Parameters
    ----------
    config: JSONSampleConfig
        Sample configuration

    Returns
    -------
    tablib.Dataset
        Loaded sample

    Raises
    ------
    OSError
        If some error occurs during sample loading
    """
    data = tablib.Dataset()
    with open(config.source) as f:
        data.load(
            in_stream=f,
            format='json'
        )
        return data


def _get_sample_loader(
    sample_type: SampleType
) -> Callable[[SampleConfig], tablib.Dataset]:
    """Get sample loader for specified sample type.

    Parameters
    ----------
    sample_type : SampleType
        Type of sample

    Returns
    -------
    Callable[[SampleConfig], tablib.Dataset]
        Function for loading sample of specified type

    Raises
    ------
    ValueError
        If no loader is registered for specified sample type
    """
    try:
        return {
            SampleType.ITEMS: _load_items_sample,
            SampleType.CSV: _load_csv_sample,
            SampleType.JSON: _load_json_sample
        }[sample_type]  # type: ignore[return-value]
    except KeyError as e:
        raise ValueError(f'No loader is registered for sample type "{e}"')


class SampleReader:
    """Sample reader.

    Parameters
    ----------
    config : dict[str, SampleConfig]
        Sample names to their configurations mapping

    Raises
    ------
    SampleLoadError
        If some error occurs during samples loading
    """

    def __init__(self, config: dict[str, SampleConfig]) -> None:
        self._samples = self._load_samples(config)

    def __getitem__(self, name: str) -> tablib.Dataset:
        try:
            return self._samples[name]
        except KeyError as e:
            raise KeyError(f'No such sample "{e}"') from None

    def _load_samples(
        self,
        config: dict[str, SampleConfig]
    ) -> dict[str, tablib.Dataset]:
        """Load samples specified in config.

        Parameters
        ----------
        config : dict[str, SampleConfig]
            Sample names to their configurations mapping

        Returns
        -------
        dict[str, tablib.Dataset]
            Sample names to their data mapping

        Raises
        ------
        SampleLoadError
            If some error occurs during samples loading
        """
        samples: dict[str, SampleConfig] = dict()

        for name, sample_config in config.items():
            loader = _get_sample_loader(sample_config.root.type)
            try:
                sample = loader(sample_config.root)  # type: ignore[arg-type]
            except Exception as e:
                raise SampleLoadError(
                    f'Failed to load sample "{name}": {e}'
                ) from None

            samples[name] = sample
        return samples
