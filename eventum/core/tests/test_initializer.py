import os
from eventum.core.initializer import init_plugins
from eventum.core.models.parameters.generator import GeneratorParameters
from eventum.plugins.event.plugins.jinja.plugin import JinjaEventPlugin
from eventum.plugins.input.plugins.cron.plugin import CronInputPlugin
from eventum.plugins.input.plugins.static.plugin import StaticInputPlugin
from eventum.plugins.output.plugins.file.plugin import FileOutputPlugin
from eventum.plugins.output.plugins.stdout.plugin import StdoutOutputPlugin


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(BASE_DIR, 'static', 'template.jinja')
TEMPLATE_REL_PATH = os.path.relpath(TEMPLATE_PATH, start=os.getcwd())


def test_initializer():
    input_config = [
        {'cron': {'expression': '* * * * *', 'count': 1}},
        {'static': {'count': 100}}
    ]
    event_config = {
        'jinja': {
            'params': {},
            'samples': {},
            'mode': 'all',
            'templates': [
                {'test': {'template': TEMPLATE_REL_PATH}}
            ]
        }
    }
    output_config = [
        {'stdout': {'stream': 'stderr'}},
        {'file': {'path': '/tmp/out.log'}}
    ]

    plugins = init_plugins(
        input=input_config,
        event=event_config,
        output=output_config,
        params=GeneratorParameters(
            id='test',
            time_mode='sample',
            path='/tmp/test.yml'
        )
    )

    assert isinstance(plugins.input[0], CronInputPlugin)
    assert isinstance(plugins.input[1], StaticInputPlugin)

    assert isinstance(plugins.event, JinjaEventPlugin)

    assert isinstance(plugins.output[0], StdoutOutputPlugin)
    assert isinstance(plugins.output[1], FileOutputPlugin)
