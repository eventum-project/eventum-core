from abc import ABC
from enum import StrEnum
from typing import Literal, Self, TypeAlias

from pydantic import BaseModel, Field, model_validator

Encoding: TypeAlias = Literal[
    'ascii',            'big5',         'big5hkscs',        'cp037',
    'cp273',            'cp424',        'cp437',            'cp500',
    'cp720',            'cp737',        'cp775',            'cp850',
    'cp852',            'cp855',        'cp856',            'cp857',
    'cp858',            'cp860',        'cp861',            'cp862',
    'cp863',            'cp864',        'cp865',            'cp866',
    'cp869',            'cp874',        'cp875',            'cp932',
    'cp949',            'cp950',        'cp1006',           'cp1026',
    'cp1125',           'cp1140',       'cp1250',           'cp1251',
    'cp1252',           'cp1253',       'cp1254',           'cp1255',
    'cp1256',           'cp1257',       'cp1258',           'euc_jp',
    'euc_jis_2004',     'euc_jisx0213', 'euc_kr',           'gb2312',
    'gbk',              'gb18030',      'hz',               'iso2022_jp',
    'iso2022_jp_1',     'iso2022_jp_2', 'iso2022_jp_2004',  'iso2022_jp_3',
    'iso2022_jp_ext',   'iso2022_kr',   'latin_1',          'iso8859_2',
    'iso8859_3',        'iso8859_4',    'iso8859_5',        'iso8859_6',
    'iso8859_7',        'iso8859_8',    'iso8859_9',        'iso8859_10',
    'iso8859_11',       'iso8859_13',   'iso8859_14',       'iso8859_15',
    'iso8859_16',       'johab',        'koi8_r',           'koi8_t',
    'koi8_u',           'kz1048',       'mac_cyrillic',     'mac_greek',
    'mac_iceland',      'mac_latin2',   'mac_roman',        'mac_turkish',
    'ptcp154',          'shift_jis',    'shift_jis_2004',   'shift_jisx0213',
    'utf_32',           'utf_32_be',    'utf_32_le',        'utf_16',
    'utf_16_be',        'utf_16_le',    'utf_7',            'utf_8',
    'utf_8_sig'
]


class Format(StrEnum):
    PLAIN = 'plain'
    JSON = 'json'
    JSON_BATCH = 'json-batch'
    TEMPLATE = 'template'
    TEMPLATE_BATCH = 'template-batch'
    EVENTUM_HTTP_INPUT = 'eventum-http-input'


class BaseFormatterConfig(BaseModel, ABC, frozen=True, extra='forbid'):
    """Base formatter config.

    Parameters
    ----------
    encoding : Encoding, default='utf-8'
        Target encoding

    separator : str, default=os.linesep
        Separator between events
    """


class SimpleFormatterConfig(BaseFormatterConfig, frozen=True):
    """Config for formats without additional parameters.

    format : Literal[Format.PLAIN, Format.EVENTUM_HTTP_INPUT]
        Target format
    """
    format: Literal[Format.PLAIN, Format.EVENTUM_HTTP_INPUT]


class JsonFormatterConfig(BaseFormatterConfig, frozen=True):
    """Config for json-like formats.

    Parameters
    ----------
    format : Literal[Format.JSON, Format.JSON_BATCH]
        Target format

    indent : int, default=0
        Indentation size
    """
    format: Literal[Format.JSON, Format.JSON_BATCH]
    indent: int = Field(default=0, ge=0)


class TemplateFormatterConfig(BaseFormatterConfig, frozen=True):
    """Config for template-like formats.

    Parameters
    ----------
    format : Literal[Format.TEMPLATE, Format.TEMPLATE_BATCH]
        Target format

    template : str | None, default=None
        Template content

    template_path : str | None, default=None
        Template path

    Notes
    -----
    Template and template path are mutually exclusive parameters

    To access original event (for `template` mode) or events sequence
    (for `template-batch` mode) use `event` or `events` variable in
    template correspondingly
    """
    format: Literal[Format.TEMPLATE, Format.TEMPLATE_BATCH]
    template: str | None = Field(default=None, min_length=1)
    template_path: str | None = Field(default=None, min_length=1)

    @model_validator(mode='after')
    def validate_template_or_path_provided(self) -> Self:
        if self.template is None and self.template_path is None:
            raise ValueError('Template or template path must be provided')

        if self.template is not None and self.template_path is not None:
            raise ValueError(
                'Template or template path must be provided, but not both'
            )

        return self


FormatterConfigT = (
    SimpleFormatterConfig | JsonFormatterConfig | TemplateFormatterConfig
)
