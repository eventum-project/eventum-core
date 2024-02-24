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
    pattern = r'([-+]?\d+)([dhms])'
    matches = re.findall(pattern, expression)

    if not matches:
        raise ValueError('Failed to parse expression')

    try:
        kwargs = {
            {
                'd': 'days',
                'h': 'hours',
                'm': 'minutes',
                's': 'seconds'
            }[unit]: int(value) for value, unit in matches
        }
    except KeyError as e:
        raise ValueError(
            f'Failed to parse expression due to unexpected unit {e}'
        )
    return timedelta(**kwargs)
