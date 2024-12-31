from datetime import datetime


def produce(params: dict) -> str | list[str]:
    ts: datetime = params['timestamp']
    tags: tuple[str, ...] = params['tags']

    return [ts.isoformat(), *tags]
