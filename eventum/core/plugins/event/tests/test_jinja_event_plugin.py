import json
from datetime import datetime

from eventum.core.models.application_config import (CSVSampleConfig,
                                                    ItemsSampleConfig,
                                                    JinjaEventConfig,
                                                    SampleType, TemplateConfig,
                                                    TemplatePickingMode)
from eventum.core.plugins.event.jinja import JinjaEventPlugin
from eventum.core.settings import TIMESTAMP_FIELD_NAME


def test_rendering():
    event = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(template='tests/test.json.jinja')
            }
        )
    ).render(**{TIMESTAMP_FIELD_NAME: datetime.now().isoformat()})

    assert len(event) == 1


def test_parameters():
    event = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={'passed_parameter': 'value of parameter'},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(template='tests/test_params.json.jinja')
            }
        )
    ).render(**{TIMESTAMP_FIELD_NAME: datetime.now().isoformat()}).pop()

    assert json.loads(event)['parameter'] == 'value of parameter'


def test_items_sample():
    event = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={
                'test_sample': ItemsSampleConfig(
                    type=SampleType.ITEMS,
                    source=['value1', 'value2']
                )
            },
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(
                    template='tests/test_items_sample.json.jinja'
                )
            }
        )
    ).render(**{TIMESTAMP_FIELD_NAME: datetime.now().isoformat()}).pop()

    event = json.loads(event)

    assert event['value'] == 'value1' or event['value'] == 'value2'


def test_csv_sample():
    event = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={
                'test_sample': CSVSampleConfig(
                    type=SampleType.CSV,
                    source='tests/sample.csv'
                )
            },
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(
                    template='tests/test_csv_sample.json.jinja'
                )
            }
        )
    ).render(**{TIMESTAMP_FIELD_NAME: datetime.now().isoformat()}).pop()

    event = json.loads(event)

    assert event['col1'] == '1' and event['col2'] == 'string 1'


def test_subprocess():
    event = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(
                    template='tests/test_subprocess.json.jinja'
                )
            }
        )
    ).render(**{TIMESTAMP_FIELD_NAME: datetime.now().isoformat()}).pop()

    event = json.loads(event)

    assert event['value'] == 'Hello, World!'
