import argparse


def _initialize_argparser(argparser: argparse.ArgumentParser) -> None:
    """Add subparsers and arguments for initial argparser object."""

    subparsers = argparser.add_subparsers(
        description='Use different subcomands to control eventum running action',
        dest='subcommand',
        required=True,
        metavar='subcommand'
    )

    # eventum start
    start_argparser = subparsers.add_parser(
        'start',
        help='start generating of events according to the provided configuration'
    )

    start_argparser.add_argument(
        '-c', '--config',
        required=True,
        help='Configuration file'
    )

    # eventum studio
    _ = subparsers.add_parser(
        'studio',
        help='run the eventum studio app',
    )


def handle_start_subcommand(args: argparse.Namespace) -> None:
    """Execute corresponding actions for `start` subcommand."""

    # TODO Implement
    raise NotImplementedError


def handle_studio_subcommand(args: argparse.Namespace) -> None:
    """Execute corresponding actions for `studio` subcommand."""

    # TODO Implement
    raise NotImplementedError


def main() -> None:
    argparser = argparse.ArgumentParser(
        prog="eventum",
        description="Flexible event generation tool",
        epilog="Repo: https://github.com/rnv812/Eventum",
    )

    # TODO adjust logger

    _initialize_argparser(argparser)

    args = argparser.parse_args()

    match args.subcommand:
        case 'start':
            handle_start_subcommand(args)
        case 'studio':
            handle_studio_subcommand(args)


if __name__ == '__main__':
    main()
