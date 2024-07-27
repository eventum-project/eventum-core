from enum import StrEnum


class PluginType(StrEnum):
    INPUT = 'input'
    EVENT = 'event'
    OUTPUT = 'output'
