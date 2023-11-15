import streamlit as st

from eventum.studio import session

MAX_TIME_PATTERNS = 5


st.set_page_config(
    page_title="Eventum Studio",
)

session.initialize(st.session_state)

with st.sidebar:
    st.title('Time Patterns')
    if st.session_state['time_pattern_ids']:
        for id in st.session_state['time_pattern_ids']:
            filepath = st.session_state[session.get_widget_key('pattern_filepath', id)]
            label = st.session_state[session.get_widget_key('pattern_label', id)]
            color = st.session_state[session.get_widget_key('pattern_color', id)]

            with st.expander(f':{color}[{label}]'):
                st.header('General')
                st.text_input(
                    'Label',
                    key=session.get_widget_key('pattern_label', id)
                )
                st.write(f'File path: *:grey[{filepath}]*')
                # TODO save_button (maybe save directly in repo????)
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

                st.divider()

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

    else:
        st.sidebar.text('No time patterns')

    st.divider()

    st.button(
        'Add new',
        disabled=True if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS else False,
        on_click=lambda: session.add_pattern(st.session_state),
        use_container_width=True
    )

    st.button(
        'Load existing',
        disabled=True if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS else False,
        on_click=lambda: session.add_pattern(st.session_state),
        use_container_width=True
    )

    if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS:
        st.write('*:grey[Maximum number of patterns]*')
