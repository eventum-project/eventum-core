import os

from jinja2 import DictLoader

from eventum_plugins.event.jinja import (CSVSampleConfig, ItemsSampleConfig,
                                         JinjaEventConfig, JinjaEventPlugin,
                                         SampleType, TemplateConfig,
                                         TemplatePickingMode)

STATIC_FILES_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'static'
)


def test_rendering():
    events = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(template='test.jinja')
            }
        ),
        loader=DictLoader(mapping={'test.jinja': '1 + 1 = {{ 1 + 1 }}'})
    ).render()

    assert len(events) == 1
    assert events.pop() == '1 + 1 = 2'


def test_rendering_parameters():
    events = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={'passed_parameter': 'value of parameter'},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(template='test.jinja')
            }
        ),
        loader=DictLoader(mapping={'test.jinja': '{{ test_param }}'})
    ).render(test_param='test value')

    assert len(events) == 1
    assert events.pop() == 'test value'


def test_items_sample():
    events = JinjaEventPlugin(
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
                'test': TemplateConfig(template='test.jinja')
            }
        ),
        loader=DictLoader(
            mapping={'test.jinja': '{{ samples.test_sample[0] }}'}
        )
    ).render()

    assert len(events) == 1
    assert events.pop() == 'value1'


def test_csv_sample():
    events = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={
                'test_sample': CSVSampleConfig(
                    type=SampleType.CSV,
                    source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                )
            },
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(template='test.jinja')
            }
        ),
        loader=DictLoader(
            mapping={'test.jinja': '{{ samples.test_sample[0] }}'}
        )
    ).render()

    assert len(events) == 1
    assert events.pop() == str(tuple(['John', 'john@example.com', 'Manager']))


def test_subprocess():
    events = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={
                'test': TemplateConfig(template='test.jinja')
            }
        ),
        loader=DictLoader(
            mapping={
                'test.jinja': (
                    '{{ subprocess.run("echo -n \'Hello, World!\'", True) }}'
                )
            }
        )
    ).render()

    assert len(events) == 1
    assert events.pop() == 'Hello, World!'
