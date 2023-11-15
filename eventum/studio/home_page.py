import streamlit as st

from eventum.studio import session

st.set_page_config(
    page_title="Eventum Studio",
)

session.initialize(st.session_state)

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
                    key=session.get_widget_key('oscillator_interval', id)
                )
                col1, col2 = st.columns([2, 1])
                col1.date_input(
                    'Start date',
                    key=session.get_widget_key('oscillator_start_date', id),
                )
                col2.time_input(
                    'Start time',
                    key=session.get_widget_key('oscillator_start_time', id),
                )
                col1.date_input(
                    'End date',
                    key=session.get_widget_key('oscillator_end_date', id),
                )
                col2.time_input(
                    'End time',
                    key=session.get_widget_key('oscillator_end_time', id),
                )

                st.divider()

                st.header('Multiplier')
                st.number_input(
                    'Ratio',
                    value=1,
                    key=session.get_widget_key('multiplier_ratio', id)
                )

                st.divider()

                st.header('Randomizer')
                col1, col2 = st.columns(2)
                col1.number_input(
                    'Mean',
                    value=1,
                    key=session.get_widget_key('randomizer_mean', id)
                )
                col2.number_input(
                    'Deviation',
                    value=0,
                    key=session.get_widget_key('randomizer_deviation', id)
                )
                st.selectbox(
                    'Direction',
                    options=['Greater', 'Lower', 'Both'],
                    key=session.get_widget_key('randomizer_direction', id),
                    help='...'
                )

                st.divider()

                st.selectbox(
                    'Function',
                    options=['Linear', 'Random', 'Gaussian'],
                    key=session.get_widget_key('spreader_function', id),
                    help='...'
                )

                st.divider()

                st.button(
                    'Save',
                    key=session.get_widget_key('save_pattern', id),
                    use_container_width=True,
                )
                st.button(
                    'Delete',
                    key=session.get_widget_key('delete_pattern', id),
                    on_click=lambda id=id: session.delete_pattern(st.session_state, id),
                    use_container_width=True,
                    type='primary'
                )
    else:
        st.sidebar.text('No time patterns')

    st.divider()

    st.button(
        'Add',
        on_click=lambda: session.add_pattern(st.session_state),
        use_container_width=True
    )
