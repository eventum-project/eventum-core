import sys

from eventum.core.plugins.output.base import BaseOutputPlugin


class StdoutOutputPlugin(BaseOutputPlugin):
    def write(self, content: str) -> None:
        sys.stdout.write(content)
        sys.stdout.flush()

    def write_many(self, content: list[str]) -> None:
        sys.stdout.writelines(content)
        sys.stdout.flush()
