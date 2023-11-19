import glob

import streamlit as st

from eventum.studio import session, models
from eventum.utils.fs import TIME_PATTERNS_DIR


MAX_TIME_PATTERNS = 5


st.set_page_config(
    page_title="Eventum Studio",
)

session.initialize(st.session_state)

with st.sidebar:
    st.title('Time Patterns')
    if st.session_state['time_pattern_ids']:
        for id in st.session_state['time_pattern_ids']:
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

                if is_saved:
                    st.button(
                        'Update',
                        key=session.get_widget_key('update_pattern', id),
                        on_click=lambda id=id: session.save_pattern(
                            st.session_state,
                            id,
                            overwrite=True,
                            notify_callback=st.toast
                        ),
                        use_container_width=True,
                    )
                else:
                    st.button(
                        'Save',
                        key=session.get_widget_key('save_pattern', id),
                        on_click=lambda id=id: session.save_pattern(
                            st.session_state,
                            id,
                            notify_callback=st.toast
                        ),
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
                    options=[unit.value for unit in models.TimeUnit],
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
                st.number_input(
                    'Deviation',
                    value=0,
                    key=session.get_widget_key('randomizer_deviation', id)
                )
                st.selectbox(
                    'Direction',
                    options=[direction.value for direction in models.RandomizerDirection],
                    key=session.get_widget_key('randomizer_direction', id),
                    help='...'
                )

                st.divider()

                st.header('Spreader')
                st.selectbox(
                    'Function',
                    options=[func.value for func in models.DistributionFunction],
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
        options=glob.glob(pathname='*.y*ml', root_dir=TIME_PATTERNS_DIR),
        key='pattern_selected_for_load',
        label_visibility='collapsed'
    )

    col2.button(
        'Load',
        disabled=(
            len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS
            or not st.session_state['pattern_selected_for_load']
        ),
        on_click=lambda: session.load_pattern(
            st.session_state,
            st.session_state['pattern_selected_for_load'],
            notify_callback=st.toast
        ),
        use_container_width=True,
    )

    if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS:
        st.write('*:grey[Maximum number of patterns]*')
