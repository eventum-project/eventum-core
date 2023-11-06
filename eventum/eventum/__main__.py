import argparse


def _initialize_argparser(argparser: argparse.ArgumentParser) -> None:
    subparsers = argparser.add_subparsers(
        description=''
    )

    start_argparser = subparsers.add_parser(
        'start',
        help='start generating of events according to the provided configuration'
    )

    show_argparser = subparsers.add_parser(
        'show',
        help='show specific data about the provided configuration'
    )

    start_argparser.add_argument(
        '-c', '--config',
        required=True,
        help='Configuration file'
    )

    show_argparser.add_argument(
        '-c', '--config',
        required=True,
        help='configuration file'
    )

    show_argparser.add_argument(
        'show_option',
        choices=['hist', 'event'],
        help=(
            '`hist` - show a histogram of the distribution of events over time; '
            '`event` - show example event generated from template'
        ),
    )


def main() -> None:
    argparser = argparse.ArgumentParser(
        prog="eventum",
        description="Flexible event generation tool",
        epilog="Repository: https://github.com/rnv812/Eventum",
    )

    _initialize_argparser(argparser)

    argparser.parse_args()


if __name__ == '__main__':
    main()
