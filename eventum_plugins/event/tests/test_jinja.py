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
            templates=[{'test': TemplateConfig(template='test.jinja')}]
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
            templates=[{'test': TemplateConfig(template='test.jinja')}]
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
            templates=[{'test': TemplateConfig(template='test.jinja')}]
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
            templates=[{'test': TemplateConfig(template='test.jinja')}]
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
            templates=[{'test': TemplateConfig(template='test.jinja')}]
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


def test_templates_picking_all():
    events = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates=[
                {'a': TemplateConfig(template='a.jinja')},
                {'b': TemplateConfig(template='b.jinja')},
                {'c': TemplateConfig(template='c.jinja')}
            ]
        ),
        loader=DictLoader(
            mapping={
                'a.jinja': 'a',
                'b.jinja': 'b',
                'c.jinja': 'c'
            }
        )
    ).render()

    assert events == ['a', 'b', 'c']


def test_templates_picking_any():
    plugin = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ANY,
            templates=[
                {'a': TemplateConfig(template='a.jinja')},
                {'b': TemplateConfig(template='b.jinja')},
                {'c': TemplateConfig(template='c.jinja')}
            ]
        ),
        loader=DictLoader(
            mapping={
                'a.jinja': 'a',
                'b.jinja': 'b',
                'c.jinja': 'c'
            }
        )
    )

    events = plugin.render()
    assert len(events) == 1

    events = []
    for _ in range(100):
        events.extend(plugin.render())

    for event in ['a', 'b', 'c']:
        assert event in events


def test_templates_picking_spin():
    plugin = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.SPIN,
            templates=[
                {'a': TemplateConfig(template='a.jinja')},
                {'b': TemplateConfig(template='b.jinja')},
                {'c': TemplateConfig(template='c.jinja')}
            ]
        ),
        loader=DictLoader(
            mapping={
                'a.jinja': 'a',
                'b.jinja': 'b',
                'c.jinja': 'c'
            }
        )
    )

    events = plugin.render()
    assert len(events) == 1
    assert 'a' in events

    events = plugin.render()
    assert len(events) == 1
    assert 'b' in events

    events = plugin.render()
    assert len(events) == 1
    assert 'c' in events

    events = plugin.render()
    assert len(events) == 1
    assert 'a' in events


def test_templates_picking_chance():
    events = JinjaEventPlugin(
        config=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.CHANCE,
            templates=[
                {'a': TemplateConfig(template='a.jinja', chance=0.000001)},
                {'b': TemplateConfig(template='b.jinja', chance=999999)},
                {'c': TemplateConfig(template='c.jinja', chance=0.000001)}
            ]
        ),
        loader=DictLoader(
            mapping={
                'a.jinja': 'a',
                'b.jinja': 'b',
                'c.jinja': 'c'
            }
        )
    ).render()

    assert len(events) == 1
    assert 'b' in events
