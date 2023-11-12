import os


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
STUDIO_ENTRYPOINT = os.path.join(BASE_PATH, 'home_page.py')


def main() -> None:
    """Execute command to run streamlit app."""
    return os.system(f'streamlit run {STUDIO_ENTRYPOINT}')


if __name__ == '__main__':
    main()
