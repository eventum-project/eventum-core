from typing import Any, Callable

import tablib  # type: ignore[import-untyped]

from eventum_plugins.event.plugins.jinja.config import (CSVSampleConfig,
                                                        ItemsSampleConfig,
                                                        JSONSampleConfig,
                                                        SampleConfig,
                                                        SampleType)


class SampleLoadError(Exception):
    """Failed to load sample."""


class Sample:
    """Immutable sample."""

    def __init__(self, dataset: tablib.Dataset) -> None:
        self._dataset = dataset

    def __len__(self) -> int:
        return self._dataset.__len__()

    def __getitem__(self, key: Any) -> list | tuple:
        return self._dataset.__getitem__(key)


def _load_items_sample(config: ItemsSampleConfig) -> Sample:
    """Load sample using configuration of type `items`.

    Parameters
    ----------
    config: ItemsSampleConfig
        Sample configuration

    Returns
    -------
    Sample
        Loaded sample
    """
    data = tablib.Dataset()
    try:
        len(config.source[0])   # check if source is a flat collection
        data.extend(config.source)
    except TypeError:
        data.extend((item, ) for item in config.source)

    return Sample(data)


def _load_csv_sample(config: CSVSampleConfig) -> Sample:
    """Load sample using configuration of type `csv`.

    Parameters
    ----------
    config: CSVSampleConfig
        Sample configuration

    Returns
    -------
    Sample
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
        return Sample(data)


def _load_json_sample(config: JSONSampleConfig) -> Sample:
    """Load sample using configuration of type `json`.

    Parameters
    ----------
    config: JSONSampleConfig
        Sample configuration

    Returns
    -------
    Sample
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
        return Sample(data)


def _get_sample_loader(
    sample_type: SampleType
) -> Callable[[SampleConfig], Sample]:
    """Get sample loader for specified sample type.

    Parameters
    ----------
    sample_type : SampleType
        Type of sample

    Returns
    -------
    Callable[[SampleConfig], Sample]
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

    def __getitem__(self, name: str) -> Sample:
        try:
            return self._samples[name]
        except KeyError as e:
            raise KeyError(f'No such sample "{e}"') from None

    def _load_samples(
        self,
        config: dict[str, SampleConfig]
    ) -> dict[str, Sample]:
        """Load samples specified in config.

        Parameters
        ----------
        config : dict[str, SampleConfig]
            Sample names to their configurations mapping

        Returns
        -------
        dict[str, Sample]
            Sample names to their data mapping

        Raises
        ------
        SampleLoadError
            If some error occurs during samples loading
        """
        samples: dict[str, Sample] = dict()

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
