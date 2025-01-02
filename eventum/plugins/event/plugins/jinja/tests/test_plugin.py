# type: ignore
import os
from datetime import datetime
from multiprocessing import RLock

from jinja2 import DictLoader

from eventum.plugins.event.plugins.jinja.config import (
    CSVSampleConfig, ItemsSampleConfig, JinjaEventPluginConfig,
    JinjaEventPluginConfigForGeneralModes, SampleType,
    TemplateConfigForGeneralModes, TemplatePickingMode)
from eventum.plugins.event.plugins.jinja.plugin import JinjaEventPlugin
from eventum.plugins.event.plugins.jinja.state import MultiProcessState

STATIC_FILES_DIR = os.path.join(
    os.path.abspath(os.path.dirname(__file__)),
    'static'
)


def test_rendering():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={},
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={'test.jinja': '1 + 1 = {{ 1 + 1 }}'}
            ),
            'global_state': ...
        }
    )

    events = plugin.produce(
        params={
            'tags': tuple(),
            'timestamp': datetime.now().astimezone()
        }
    )

    assert len(events) == 1
    assert events.pop() == '1 + 1 = 2'


def test_rendering_parameters():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={'passed_parameter': 'value of parameter'},
                samples={},
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={'test.jinja': '{{ params.passed_parameter }}'}
            ),
            'global_state': ...
        }
    )

    events = plugin.produce(
        params={
            'tags': tuple(),
            'timestamp': datetime.now().astimezone()
        }
    )

    assert len(events) == 1
    assert events.pop() == 'value of parameter'


def test_items_sample():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': ItemsSampleConfig(
                        type=SampleType.ITEMS,
                        source=['value1', 'value2']
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={'test.jinja': '{{ samples.test_sample[0][0] }}'}
            ),
            'global_state': ...
        }
    )

    events = plugin.produce(
        params={
            'tags': tuple(),
            'timestamp': datetime.now().astimezone()
        }
    )

    assert len(events) == 1
    assert events.pop() == 'value1'


def test_csv_sample():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv'),
                        header=True
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={'test.jinja': '{{ samples.test_sample[0] }}'}
            ),
            'global_state': ...
        }
    )

    events = plugin.produce(
        params={
            'tags': tuple(),
            'timestamp': datetime.now().astimezone()
        }
    )

    assert len(events) == 1
    assert events.pop() == str(tuple(['John', 'john@example.com', 'Manager']))


def test_subprocess():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={
                    'test.jinja': (
                        '{{subprocess.run("echo Hello").stdout | trim}}'
                    )
                }
            ),
            'global_state': ...
        }
    )

    events = plugin.produce(
        params={
            'tags': tuple(),
            'timestamp': datetime.now().astimezone()
        }
    )

    assert len(events) == 1
    assert events.pop() == 'Hello'


def test_locals_state():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    },
                    {
                        'other_test': TemplateConfigForGeneralModes(
                            template='other_test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={
                    'test.jinja': (
                        '{%- set i = locals.get("i", 1) -%}\n'
                        '{{ i }}\n'
                        '{%- do locals.set("i", i + 1) -%}\n'
                    ),
                    'other_test.jinja': (
                        '{%- set i = locals.get("i", 1) -%}\n'
                        '{{ i }}\n'
                    )
                }
            ),
            'global_state': ...
        }
    )

    events = []
    for _ in range(3):
        events.extend(
            plugin.produce(
                params={
                    'tags': tuple(),
                    'timestamp': datetime.now().astimezone()
                }
            )
        )

    assert len(events) == 6
    assert events == [
        '1', '1',
        '2', '1',
        '3', '1'
    ]


def test_shared_state():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    },
                    {
                        'other_test': TemplateConfigForGeneralModes(
                            template='other_test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={
                    'test.jinja': (
                        '{%- set i = shared.get("i", 1) -%}\n'
                        '{{ i }}\n'
                        '{%- do shared.set("i", i + 1) -%}\n'
                    ),
                    'other_test.jinja': (
                        '{%- set i = shared.get("i", 1) -%}\n'
                        '{{ i }}\n'
                    )
                }
            ),
            'global_state': ...
        }
    )

    events = []
    for _ in range(3):
        events.extend(
            plugin.produce(
                params={
                    'tags': tuple(),
                    'timestamp': datetime.now().astimezone()
                }
            )
        )

    assert len(events) == 6
    assert events == [
        '1', '2',
        '2', '3',
        '3', '4'
    ]


def test_global_state():
    global_state = MultiProcessState('test', True, 1024, RLock())
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    },
                    {
                        'other_test': TemplateConfigForGeneralModes(
                            template='other_test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={
                    'test.jinja': (
                        '{%- set i = globals.get("i", 1) -%}\n'
                        '{{ i }}\n'
                        '{%- do globals.set("i", i + 1) -%}\n'
                    ),
                    'other_test.jinja': (
                        '{%- set i = globals.get("i", 1) -%}\n'
                        '{{ i }}\n'
                    )
                }
            ),
            'global_state': global_state
        }
    )

    events = []
    for _ in range(3):
        events.extend(
            plugin.produce(
                params={
                    'tags': tuple(),
                    'timestamp': datetime.now().astimezone()
                }
            )
        )

    global_state.close()
    global_state.destroy()

    assert len(events) == 6
    assert events == [
        '1', '2',
        '2', '3',
        '3', '4'
    ]


def test_modules():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={
                    'test.jinja': (
                        '{{ module.rand.number.integer(1, 10) }}'
                    )
                }
            ),
            'global_state': ...
        }
    )

    events = plugin.produce(
        params={
            'tags': tuple(),
            'timestamp': datetime.now().astimezone()
        }
    )

    assert len(events) == 1
    assert events.pop() in list(str(n) for n in range(0, 11))


def test_timestamp():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={
                    'test.jinja': '{{ timestamp.isoformat() }}'
                }
            ),
            'global_state': ...
        }
    )
    ts = datetime.now().astimezone()

    events = plugin.produce(
        params={
            'tags': tuple(),
            'timestamp': ts
        }
    )

    assert len(events) == 1
    assert events.pop() == ts.isoformat()


def test_tags():
    plugin = JinjaEventPlugin(
        config=JinjaEventPluginConfig(
            root=JinjaEventPluginConfigForGeneralModes(
                params={},
                samples={
                    'test_sample': CSVSampleConfig(
                        type=SampleType.CSV,
                        source=os.path.join(STATIC_FILES_DIR, 'sample.csv')
                    )
                },
                mode=TemplatePickingMode.ALL,
                templates=[
                    {
                        'test': TemplateConfigForGeneralModes(
                            template='test.jinja'
                        )
                    }
                ]

            )
        ),
        params={
            'id': 1,
            'templates_loader': DictLoader(
                mapping={
                    'test.jinja': '{{ tags[1] }}'
                }
            ),
            'global_state': ...
        }
    )

    events = plugin.produce(
        params={
            'tags': ('some', 'interesting', 'tags'),
            'timestamp': datetime.now().astimezone()
        }
    )

    assert len(events) == 1
    assert events.pop() == 'interesting'
