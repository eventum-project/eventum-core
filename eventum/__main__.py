import argparse


def _initialize_argparser(argparser: argparse.ArgumentParser) -> None:
    """Add arguments for initial argparser object."""

    argparser.add_argument(
        '-c', '--config',
        required=True,
        help='Configuration file'
    )


def main() -> None:
    argparser = argparse.ArgumentParser(
        prog="eventum",
        description="Flexible event generation tool",
        epilog="Repo: https://github.com/rnv812/Eventum",
    )

    # TODO adjust logger

    _initialize_argparser(argparser)

    _ = argparser.parse_args()

    # TODO Implement creating app object and starting it
    raise NotImplementedError


if __name__ == '__main__':
    main()
