import argparse

from pwinput import pwinput  # type: ignore[import-untyped]

from eventum_cli.keyring import get_secret, remove_secret, set_secret


def _initialize_argparser(argparser: argparse.ArgumentParser) -> None:
    subparsers = argparser.add_subparsers(
        title='operation',
        description='Operation to do with keyring',
        required=True,
        dest='operation'
    )

    get_subparser = subparsers.add_parser(
        name='get',
        help='get key from keyring'
    )
    get_subparser.add_argument(
        'key',
        help='name of key to get'
    )

    set_subparser = subparsers.add_parser(
        name='set',
        help='set key to keyring'
    )
    set_subparser.add_argument(
        'key',
        help='name of key to set'
    )

    remove_subparser = subparsers.add_parser(
        name='remove',
        help='remove key from keyring'
    )
    remove_subparser.add_argument(
        'key',
        help='name of key to remove'
    )


def main():
    argparser = argparse.ArgumentParser(
        prog='eventum-keyring',
        description='Keyring management tool for Eventum',
        epilog='Documentation: https://eventum-generatives.github.io/Website/',
    )
    _initialize_argparser(argparser)
    args = argparser.parse_args()

    try:
        match args.operation:
            case 'get':
                value = get_secret(key=args.key)
                if value is None:
                    raise ValueError(
                        f'Key "{args.key}" not found in keyring'
                    )
                print(value)
            case 'set':
                set_secret(
                    key=args.key,
                    value=pwinput(f'Password for "{args.key}": ')
                )
            case 'remove':
                remove_secret(key=args.key)
    except Exception as e:
        print(f'Failed to {args.operation} key "{args.key}": {e}')
        exit(1)


if __name__ == '__main__':
    main()
