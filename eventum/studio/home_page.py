import streamlit as st

st.set_page_config(
    page_title="Eventum Studio",
)


def add_pattern() -> None:
    """Append current `time_pattern_id_counter` to `time_pattern_ids` list
    in session state and incremenet `time_pattern_id_counter`.
    """
    st.session_state['time_pattern_ids'].append(st.session_state['time_pattern_id_counter'])
    st.session_state['time_pattern_id_counter'] += 1


def delete_pattern(id: int) -> None:
    """Remove id from `time_pattern_ids` list and all attributes of specified
    pattern by their id postfix in session state.
    """
    print(f'ID: {id}')
    st.session_state['time_pattern_ids'].remove(id)

    for key in st.session_state.keys():
        parts = key.rsplit(sep='_', maxsplit=1)
        if parts and parts[-1] == str(id):
            del st.session_state[key]


if 'time_pattern_id_counter' not in st.session_state:
    st.session_state['time_pattern_id_counter'] = 1

if 'time_pattern_ids' not in st.session_state:
    st.session_state['time_pattern_ids'] = []

with st.sidebar:
    st.title('Time Patterns')
    if st.session_state['time_pattern_ids']:
        for id in st.session_state['time_pattern_ids']:
            pattern_container = st.sidebar.container()
            with st.expander(f'Pattern {id}'):
                st.header('Ocillator')
                st.number_input(
                    'Interval',
                    value=1,
                    key=f'oscillator_interval_{id}'
                )
                col1, col2 = st.columns([2, 1])
                col1.date_input(
                    'Start date',
                    key=f'oscillator_start_date_{id}',
                )
                col2.time_input(
                    'Start time',
                    key=f'oscillator_start_time_{id}',
                )
                col1.date_input(
                    'End date',
                    key=f'oscillator_end_date_{id}',
                )
                col2.time_input(
                    'End time',
                    key=f'oscillator_end_time_{id}',
                )

                st.divider()

                st.header('Multiplier')
                st.number_input(
                    'Ratio',
                    value=1,
                    key=f'multiplier_ratio_{id}'
                )

                st.divider()

                st.header('Randomizer')
                col1, col2 = st.columns(2)
                col1.number_input(
                    'Mean',
                    value=1,
                    key=f'randomizer_mean_{id}'
                )
                col2.number_input(
                    'Deviation',
                    value=0,
                    key=f'randomizer_deviation_{id}'
                )
                st.selectbox(
                    'Direction',
                    options=['Greater', 'Lower', 'Both'],
                    key=f'randomizer_direction_{id}',
                    help='...'
                )

                st.divider()

                st.selectbox(
                    'Function',
                    options=['Linear', 'Random', 'Gaussian'],
                    key=f'spreader_function_{id}',
                    help='...'
                )

                st.divider()

                st.button(
                    'Save',
                    key=f'save_pattern_{id}',
                    use_container_width=True,
                )
                st.button(
                    'Delete',
                    key=f'delete_pattern_{id}',
                    on_click=lambda id=id: delete_pattern(id),
                    use_container_width=True,
                    type='primary'
                )
    else:
        st.sidebar.text('No time patterns')

    st.divider()

    st.button(
        'Add',
        on_click=add_pattern,
        use_container_width=True
    )
