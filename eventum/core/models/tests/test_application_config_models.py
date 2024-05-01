import pytest
from pydantic import ValidationError

from eventum.core.models.application_config import (ApplicationConfig,
                                                    CronInputConfig,
                                                    CSVSampleConfig,
                                                    FileOutputConfig,
                                                    InputName,
                                                    ItemsSampleConfig,
                                                    JinjaEventConfig,
                                                    NullOutputConfig,
                                                    OpensearchOutputConfig,
                                                    OutputFormat, OutputName,
                                                    SampleInputConfig,
                                                    SampleType,
                                                    StdOutOutputConfig,
                                                    TemplateConfig,
                                                    TemplatePickingMode)


def test_crontab_input_config():
    CronInputConfig(expression='* * * * *', count=5)


def test_sample_input_config():
    SampleInputConfig(count=100)


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

    with pytest.raises(ValidationError):
        CSVSampleConfig(
            type=SampleType.CSV,
            source=''
        )


def test_items_sample_config():
    ItemsSampleConfig(
        type=SampleType.ITEMS,
        source=['item1', 'item2', 'item3']
    )
    with pytest.raises(ValidationError):
        ItemsSampleConfig(
            type=SampleType.ITEMS,
            source=[]
        )


def test_template_config():
    TemplateConfig(template='test/test.json.jinja')
    TemplateConfig(template='test/test.json.jinja', chance=0.8)


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
            'test_template': TemplateConfig(
                template='test/test.json.csv'
            )
        }
    )


def test_std_out_output_config():
    StdOutOutputConfig()
    StdOutOutputConfig(format=OutputFormat.JSON_LINES)


def test_null_output_config():
    NullOutputConfig()


def test_file_output_config():
    FileOutputConfig(path='test.out')
    FileOutputConfig(path='test.out', format=OutputFormat.JSON_LINES)

    with pytest.raises(ValidationError):
        FileOutputConfig(path='')


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

    with pytest.raises(ValidationError):
        OpensearchOutputConfig(
            hosts=[],
            user='admin',
            index='test',
            verify_ssl=False
        )

    with pytest.raises(ValidationError):
        OpensearchOutputConfig(
            hosts=['https://localhost:9200'],
            user='',
            index='test',
            verify_ssl=False
        )

    with pytest.raises(ValidationError):
        OpensearchOutputConfig(
            hosts=['https://localhost:9200'],
            user='admin',
            index='',
            verify_ssl=False
        )


def test_application_config():
    event_config = JinjaEventConfig(
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
            'test_template': TemplateConfig(
                template='test/test.json.csv'
            )
        }
    )
    ApplicationConfig(
        input={InputName.SAMPLE: SampleInputConfig(count=100)},
        event=event_config,
        output={OutputName.NULL: NullOutputConfig()}
    )

    with pytest.raises(ValidationError):
        ApplicationConfig(
            input={
                InputName.SAMPLE: SampleInputConfig(count=100),
                InputName.CRON: CronInputConfig(
                    expression='* * * * *',
                    count=1
                )
            },
            event=event_config,
            output={OutputName.NULL: NullOutputConfig()}
        )

    with pytest.raises(ValidationError):
        ApplicationConfig(
            input={InputName.SAMPLE: SampleInputConfig(count=100)},
            event=event_config,
            output={}
        )

    with pytest.raises(ValidationError):
        ApplicationConfig(
            input={},
            event=event_config,
            output={OutputName.NULL: NullOutputConfig()}
        )
