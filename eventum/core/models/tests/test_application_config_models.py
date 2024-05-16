import pytest
from pydantic import ValidationError

from eventum.core.models.application_config import ApplicationConfig
from eventum.core.models.event_config import (CSVSampleConfig,
                                              ItemsSampleConfig,
                                              JinjaEventConfig, SampleType,
                                              TemplateConfig,
                                              TemplatePickingMode)
from eventum.core.models.input_config import (CronInputConfig,
                                              LinspaceInputConfig,
                                              SampleInputConfig,
                                              TimerInputConfig)
from eventum.core.models.output_config import (FileOutputConfig,
                                               OpensearchOutputConfig,
                                               OutputFormat,
                                               StdOutOutputConfig)


def test_crontab_input_config():
    CronInputConfig(expression='* * * * *', count=5)


def test_crontab_input_config_with_empty_expression():
    with pytest.raises(ValidationError):
        CronInputConfig(expression='', count=1)


def test_crontab_input_config_with_invalid_expression():
    with pytest.raises(ValidationError):
        CronInputConfig(expression='* * % * *', count=1)


def test_crontab_input_config_with_invalid_count():
    with pytest.raises(ValidationError):
        CronInputConfig(expression='* * * * *', count=0)

    with pytest.raises(ValidationError):
        CronInputConfig(expression='* * * * *', count=-10)


def test_linspace_input_config():
    LinspaceInputConfig(
        start='2024-05-01T00:00:00',
        end='2024-05-31T00:00:00',
        count=31
    )

    LinspaceInputConfig(
        start='2024-05-01T00:00:00',
        end='2024-05-31T00:00:00',
        count=4,
        endpoint=False
    )


def test_linspace_input_config_with_interval():
    with pytest.raises(ValidationError):
        LinspaceInputConfig(
            start='2024-05-31T00:00:00',
            end='2024-05-01T00:00:00',
            count=31
        )


def test_linspace_input_config_with_invalid_count():
    with pytest.raises(ValidationError):
        LinspaceInputConfig(
            start='2024-05-01T00:00:00',
            end='2024-05-31T00:00:00',
            count=0
        )

    with pytest.raises(ValidationError):
        LinspaceInputConfig(
            start='2024-05-01T00:00:00',
            end='2024-05-31T00:00:00',
            count=-10
        )


def test_timer_input_config():
    TimerInputConfig(seconds=1, count=1, repeat=True)


def test_timer_config_with_invalid_seconds():
    with pytest.raises(ValidationError):
        TimerInputConfig(seconds=0, count=1, repeat=True)

    with pytest.raises(ValidationError):
        TimerInputConfig(seconds=-1, count=1, repeat=True)


def test_timer_config_with_invalid_count():
    with pytest.raises(ValidationError):
        TimerInputConfig(seconds=1, count=0, repeat=True)

    with pytest.raises(ValidationError):
        TimerInputConfig(seconds=1, count=-1, repeat=True)


def test_sample_input_config():
    SampleInputConfig(count=100)


def test_sample_input_config_with_invalid_count():
    with pytest.raises(ValidationError):
        SampleInputConfig(count=0)

    with pytest.raises(ValidationError):
        SampleInputConfig(count=-10)


def test_csv_sample_config():
    CSVSampleConfig(
        type=SampleType.CSV,
        header=True,
        delimiter=',',
        source='test.csv'
    )
    CSVSampleConfig(
        type=SampleType.CSV,
        source='test.csv'
    )


def test_csv_sample_config_with_empty_delimiter():
    with pytest.raises(ValidationError):
        CSVSampleConfig(
            type=SampleType.CSV,
            delimiter='',
            source='test.csv'
        )


def test_csv_sample_config_with_empty_source():
    with pytest.raises(ValidationError):
        CSVSampleConfig(
            type=SampleType.CSV,
            source=''
        )


def test_csv_sample_config_with_invalid_source():
    with pytest.raises(ValidationError):
        CSVSampleConfig(
            type=SampleType.CSV,
            source='test.xlsx'
        )


def test_csv_sample_config_with_invalid_type():
    with pytest.raises(ValidationError):
        CSVSampleConfig(
            type=SampleType.ITEMS,
            source='test.csv'
        )


def test_items_sample_config():
    ItemsSampleConfig(
        type=SampleType.ITEMS,
        source=['item1', 'item2', 'item3']
    )


def test_items_sample_config_with_empty_source():
    with pytest.raises(ValidationError):
        ItemsSampleConfig(
            type=SampleType.ITEMS,
            source=[]
        )


def test_items_sample_config_with_invalid_type():
    with pytest.raises(ValidationError):
        ItemsSampleConfig(
            type=SampleType.CSV,
            source=['item1', 'item2', 'item3']
        )


def test_template_config():
    TemplateConfig(template='test.json.jinja')
    TemplateConfig(template='test.json.jinja', chance=0.8)


def test_template_config_with_invalid_template():
    with pytest.raises(ValidationError):
        TemplateConfig(template='test', chance=0)


def test_template_config_with_invalid_chance():
    with pytest.raises(ValidationError):
        TemplateConfig(template='test.json.jinja', chance=0)

    with pytest.raises(ValidationError):
        TemplateConfig(template='test.json.jinja', chance=-10)


def test_jinja_event_config():
    JinjaEventConfig(
        params={'param': 'value'},
        samples={
            'csv_sample': CSVSampleConfig(
                type=SampleType.CSV,
                source='test.csv'
            ),
            'items_sample': ItemsSampleConfig(
                type=SampleType.ITEMS,
                source=['item1', 'item2', 'item3']
            )
        },
        mode=TemplatePickingMode.ALL,
        templates={
            'test': TemplateConfig(
                template='test.json.jinja'
            )
        }
    )
    JinjaEventConfig(
        params={},
        samples={},
        mode=TemplatePickingMode.ALL,
        templates={
            'test_template': TemplateConfig(
                template='test.json.jinja'
            )
        }
    )


def test_jinja_event_config_with_empty_templates():
    with pytest.raises(ValidationError):
        JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={}
        )


def test_std_out_output_config():
    StdOutOutputConfig()
    StdOutOutputConfig(format=OutputFormat.JSON_LINES)


def test_file_output_config():
    FileOutputConfig(path='/tmp/test.out')
    FileOutputConfig(
        path='/tmp/test.out',
        format=OutputFormat.JSON_LINES,
        flush=True
    )


def test_file_output_config_with_empty_path():
    with pytest.raises(ValidationError):
        FileOutputConfig(path='')


def test_file_output_config_with_relative_path():
    with pytest.raises(ValidationError):
        FileOutputConfig(path='../relative.txt')


def test_opensearch_output_config():
    OpensearchOutputConfig(
        hosts=['https://localhost:9200'],
        user='admin',
        index='test',
        verify_ssl=True,
        ca_cert_path='ca-cert.pem'
    )
    OpensearchOutputConfig(
        hosts=['https://localhost:9200'],
        user='admin',
        index='test',
        verify_ssl=False
    )


def test_opensearch_output_config_with_invalid_hosts():
    with pytest.raises(ValidationError):
        OpensearchOutputConfig(
            hosts=[],
            user='admin',
            index='test',
            verify_ssl=False
        )


def test_opensearch_output_config_with_invalid_user():
    with pytest.raises(ValidationError):
        OpensearchOutputConfig(
            hosts=['https://localhost:9200'],
            user='',
            index='test',
            verify_ssl=False
        )


def test_opensearch_output_config_with_invalid_index():
    with pytest.raises(ValidationError):
        OpensearchOutputConfig(
            hosts=['https://localhost:9200'],
            user='admin',
            index='',
            verify_ssl=False
        )


def test_application_config():
    ApplicationConfig(
        input={'sample': SampleInputConfig(count=100)},
        event=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={'test': TemplateConfig(template='test.json.jinja')}
        ),
        output=[{'file': FileOutputConfig(path='/tmp/out.log')}]
    )


def test_application_config_with_plural_output():
    ApplicationConfig(
        input={'sample': SampleInputConfig(count=100)},
        event=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={'test': TemplateConfig(template='test.json.jinja')}
        ),
        output=[
            {'file': FileOutputConfig(path='/tmp/out.log')},
            {'stdout': StdOutOutputConfig()}
        ]
    )


def test_application_config_with_plural_input():
    with pytest.raises(ValidationError):
        ApplicationConfig(
            input={
                'sample': SampleInputConfig(count=100),
                'cron': CronInputConfig(
                    expression='* * * * *',
                    count=1
                )
            },
            event=JinjaEventConfig(
                params={},
                samples={},
                mode=TemplatePickingMode.ALL,
                templates={'test': TemplateConfig(template='test.json.jinja')}
            ),
            output=[{'stdout': StdOutOutputConfig()}]
        )


def test_application_config_with_empty_input():
    with pytest.raises(ValidationError):
        ApplicationConfig(
            input={},
            event=JinjaEventConfig(
                params={},
                samples={},
                mode=TemplatePickingMode.ALL,
                templates={'test': TemplateConfig(template='test.json.jinja')}
            ),
            output=[{'stdout': StdOutOutputConfig()}]
        )


def test_application_config_with_empty_output():
    ApplicationConfig(
        input={'sample': SampleInputConfig(count=100)},
        event=JinjaEventConfig(
            params={},
            samples={},
            mode=TemplatePickingMode.ALL,
            templates={'test': TemplateConfig(template='test.json.jinja')}
        ),
        output=[]
    )
