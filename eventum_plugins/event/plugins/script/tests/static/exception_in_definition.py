from datetime import datetime


def produce(params: dict) -> str | list[str]:
    ts: datetime = params['timestamp']
    tags: tuple[str, ...] = params['tags']

    return f'{ts.isoformat()}, {tags}'


raise RuntimeError(
    'I am a hacker that replaced script to inject error in runtime '
    'to brake whole generator!!! Ha ha ha ༼ つ ◕_◕ ༽つ'
)
