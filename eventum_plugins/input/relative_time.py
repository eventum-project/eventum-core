import re
from datetime import timedelta


def parse_relative_time(expression: str) -> timedelta:
    """Parse expression representing relative time and return
    corresponding timedelta object.

    Parameters
    ----------
    expression : str
        Expression in the following format:
        ```
        <expression> ::= [<sign>]<term>{<term>}...
        <sign> ::= '+' | '-'
        <term> ::= <value><unit>
        <value> ::= <integer>
        <unit> ::= 'd' | 'h' | 'm' | 's'
        ```
        Example expressions: `+1d12h`; `1h30m10s`; `-3d4h`; `-1d2h30m`

    Returns
    -------
    timedelta
        Parsed expression represented as timedelta object

    Raises
    ------
    ValueError
        If expression cannot be parsed due to invalid format
    """
    if not expression:
        raise ValueError('Empty expression is provided')

    pattern = (
        r'^(?P<sign>[-+])?'
        r'(?:(?P<days>\d+)d)?'
        r'(?:(?P<hours>\d+)h)?'
        r'(?:(?P<minutes>\d+)m)?'
        r'(?:(?P<seconds>\d+)s)?$'
    )
    match = re.match(pattern, expression)

    if match is None or match.start() != 0 or match.end() != (len(expression)):
        raise ValueError('Failed to parse expression')

    groups = match.groupdict()

    match groups.pop('sign'):
        case None:
            sign = 1
        case '+':
            sign = 1
        case '-':
            sign = -1
        case char:
            raise ValueError(f'Unexpected sign "{char}"')

    return timedelta(
        **{
            unit: int(value) * sign
            for unit, value in groups.items()
            if value is not None
        }
    )
