import re
from datetime import timedelta


def parse_relative_time(expression: str) -> timedelta:
    """Parse `expression` representing relative time and return
    coresponding`timedelta` object. The exression format is next:

    <expression> ::= <term>{<term>}...
    <term> ::= [<sign>]<value><unit>
    <sign> ::= '+' | '-'
    <value> ::= <integer>
    <unit> ::= 'd' | 'h' | 'm' | 's'

    Example expressions: '+1d+12h'; '1h+30m+10s'; '-3d-4h'; '1d-2h+30m';
    If expression cannot be properly parsed then `ValueError` is raised.
    """
    if not expression:
        raise ValueError('Empty expression is provided')

    pattern = (
        r'(?:(?P<days>[-+]?\d+)d)?'
        r'(?:(?P<hours>[-+]?\d+)h)?'
        r'(?:(?P<minutes>[-+]?\d+)m)?'
        r'(?:(?P<seconds>[-+]?\d+)s)?'
    )
    match = re.match(pattern, expression)

    if match.start() != 0 or match.end() != (len(expression)):
        raise ValueError('Failed to parse expression')

    return timedelta(
        **{
            unit: int(value)
            for unit, value in match.groupdict().items()
            if value is not None
        }
    )
