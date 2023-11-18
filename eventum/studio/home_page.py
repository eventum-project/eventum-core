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
            save_error = st.session_state[session.get_widget_key('pattern_save_error', id)]
            save_success = st.session_state[session.get_widget_key('pattern_save_success', id)]
            is_saved = st.session_state[session.get_widget_key('pattern_is_saved', id)]

            label = st.session_state[session.get_widget_key('pattern_label', id)]
            color = st.session_state[session.get_widget_key('pattern_color', id)]

            with st.expander(f':{color}[{label}]'):
                st.header('General')
                st.text_input(
                    'Label',
                    key=session.get_widget_key('pattern_label', id)
                )
                st.text_input(
                    'File name',
                    key=session.get_widget_key('pattern_filename', id),
                    disabled=is_saved is True,
                )

                if save_error:
                    st.write(f'*:red[{save_error}]*')
                if save_success:
                    st.write(f'*:green[{save_success}]*')

                if is_saved:
                    st.button(
                        'Update',
                        key=session.get_widget_key('update_pattern', id),
                        on_click=lambda id=id: session.save_pattern(st.session_state, id, overwrite=True),
                        use_container_width=True,
                    )
                else:
                    st.button(
                        'Save',
                        key=session.get_widget_key('save_pattern', id),
                        on_click=lambda id=id: session.save_pattern(st.session_state, id),
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
                col1, col2 = st.columns([8, 2])
                col1.number_input(
                    'Interval',
                    value=1,
                    key=session.get_widget_key('oscillator_interval', id)
                )
                col2.selectbox(
                    'Unit',
                    options=['s', 'm', 'h', 'd'],
                    key=session.get_widget_key('oscillator_interval_unit', id)
                )
                col1, col2 = st.columns(2)
                col1.text_input(
                    'Start timestamp',
                    key=session.get_widget_key('oscillator_start_timestamp', id),
                )
                col2.text_input(
                    'End timestamp',
                    key=session.get_widget_key('oscillator_end_timestamp', id),
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

                st.header('Spreader')
                st.selectbox(
                    'Function',
                    options=['Linear', 'Random', 'Gaussian'],
                    key=session.get_widget_key('spreader_function', id),
                    help='...'
                )

    else:
        st.markdown(
            '<div style="text-align: center; color: grey;">No time patterns</div>',
            unsafe_allow_html=True
        )

    st.divider()

    st.button(
        'Create new',
        disabled=True if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS else False,
        on_click=lambda: session.add_pattern(st.session_state),
        use_container_width=True
    )
    col1, col2 = st.columns([7, 3])
    col1.selectbox(
        'Time patterns',
        options=['pattern1.yml', 'pattern1.yml', 'pattern1.yml'],
        label_visibility='collapsed'
    )

    col2.button(
        'Load',
        disabled=True if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS else False,
        on_click=lambda: session.add_pattern(st.session_state),
        use_container_width=True
    )

    if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS:
        st.write('*:grey[Maximum number of patterns]*')
