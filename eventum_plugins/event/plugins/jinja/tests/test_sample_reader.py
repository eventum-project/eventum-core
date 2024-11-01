import os

import pytest

from eventum_plugins.event.plugins.jinja.config import (CSVSampleConfig,
                                                        ItemsSampleConfig,
                                                        JSONSampleConfig,
                                                        SampleConfig,
                                                        SampleType)
from eventum_plugins.event.plugins.jinja.sample_reader import (Sample,
                                                               SampleLoadError,
                                                               SampleReader)

BASE_PATH = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def items_sample_config():
    return {
        'items_sample': SampleConfig(
            root=ItemsSampleConfig(
                type=SampleType.ITEMS,
                source=(
                    ('one', 'two'),
                    ('three', 'four')
                )
            )
        )
    }


@pytest.fixture
def flat_items_sample_config():
    return {
        'items_sample': SampleConfig(
            root=ItemsSampleConfig(
                type=SampleType.ITEMS,
                source=[1, 2, 3]
            )
        )
    }


@pytest.fixture
def csv_sample_config():
    return {
        'csv_sample': SampleConfig(
            root=CSVSampleConfig(
                type=SampleType.CSV,
                source=os.path.join(BASE_PATH, 'static/sample.csv'),
                header=True,
                delimiter=','
            )
        )
    }


@pytest.fixture
def no_header_csv_sample_config():
    return {
        'csv_sample': SampleConfig(
            root=CSVSampleConfig(
                type=SampleType.CSV,
                source=os.path.join(BASE_PATH, 'static/sample.csv'),
                header=False,
                delimiter=','
            )
        )
    }


@pytest.fixture
def not_existing_csv_sample_config():
    return {
        'csv_sample': SampleConfig(
            root=CSVSampleConfig(
                type=SampleType.CSV,
                source=os.path.join(BASE_PATH, 'static/not_existing.csv'),
                header=True,
                delimiter=','
            )
        )
    }


@pytest.fixture
def other_delimiter_csv_sample_config():
    return {
        'csv_sample': SampleConfig(
            root=CSVSampleConfig(
                type=SampleType.CSV,
                source=os.path.join(BASE_PATH, 'static/piped_sample.csv'),
                header=True,
                delimiter='|'
            )
        )
    }


@pytest.fixture
def json_sample_config():
    return {
        'json_sample': SampleConfig(
            root=JSONSampleConfig(
                type=SampleType.JSON,
                source=os.path.join(BASE_PATH, 'static/sample.json'),
            )
        )
    }


@pytest.fixture
def nested_json_sample_config():
    return {
        'json_sample': SampleConfig(
            root=JSONSampleConfig(
                type=SampleType.JSON,
                source=os.path.join(BASE_PATH, 'static/nested_sample.json'),
            )
        )
    }


def test_load_items_sample(items_sample_config):
    sample_reader = SampleReader(items_sample_config)
    sample = sample_reader['items_sample']

    assert isinstance(sample, Sample)
    assert sample[0] == ('one', 'two')
    assert sample[1] == ('three', 'four')


def test_load_flat_items_sample(flat_items_sample_config):
    sample_reader = SampleReader(flat_items_sample_config)
    sample = sample_reader['items_sample']

    assert isinstance(sample, Sample)
    assert sample[0] == (1, )
    assert sample[1] == (2, )
    assert sample[2] == (3, )


def test_load_csv_sample(csv_sample_config):
    sample_reader = SampleReader(csv_sample_config)
    sample = sample_reader['csv_sample']

    assert isinstance(sample, Sample)
    assert sample[0] == ('John', 'john@example.com', 'Manager')
    assert sample[1] == ('Jane', 'jane@example.com', 'HR')


def test_load_csv_sample_with_wrong_path(not_existing_csv_sample_config):
    with pytest.raises(SampleLoadError):
        SampleReader(not_existing_csv_sample_config)


def test_load_csv_sample_with_other_delimiter(
    other_delimiter_csv_sample_config
):
    sample_reader = SampleReader(other_delimiter_csv_sample_config)

    sample = sample_reader['csv_sample']
    assert sample[0] == ('John', 'john@example.com', 'Manager')
    assert sample[1] == ('Jane', 'jane@example.com', 'HR')


def test_load_csv_sample_without_header(no_header_csv_sample_config):
    sample_reader = SampleReader(no_header_csv_sample_config)
    sample = sample_reader['csv_sample']

    assert sample[0] == ('name', 'email', 'position')
    assert sample[1] == ('John', 'john@example.com', 'Manager')
    assert sample[2] == ('Jane', 'jane@example.com', 'HR')


def test_load_json_sample(json_sample_config):
    sample_reader = SampleReader(json_sample_config)
    sample = sample_reader['json_sample']

    assert isinstance(sample, Sample)
    assert sample[0] == ('John', 'john@example.com', 'Manager')
    assert sample[1] == ('Jane', 'jane@example.com', 'HR')


def test_load_nested_json_sample(nested_json_sample_config):
    sample_reader = SampleReader(nested_json_sample_config)
    sample = sample_reader['json_sample']

    assert isinstance(sample, Sample)
    assert sample[0] == (
        {'firstname': 'John', 'lastname': 'Doe'},
        ['john@example.com', 'john.public@example.com'],
        'Manager'
    )
    assert sample[1] == (
        {'firstname': 'Jane', 'lastname': 'Doe'},
        ['jane@example.com', 'jane.public@example.com'],
        'HR'
    )


def test_missing_samples(items_sample_config):
    sample_reader = SampleReader(items_sample_config)
    with pytest.raises(KeyError):
        sample_reader['missing_samples']
