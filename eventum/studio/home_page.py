import glob

import streamlit as st

from eventum.studio import models
from eventum.studio.session import add_pattern, delete_pattern
from eventum.studio.session import get_pattern_widget_key as pwk
from eventum.studio.session import initialize, load_pattern, save_pattern
from eventum.utils.fs import TIME_PATTERNS_DIR

MAX_TIME_PATTERNS = 5


st.set_page_config(
    page_title="Eventum Studio",
)

initialize(st.session_state)

with st.sidebar:
    st.title('Time Patterns')
    st.divider()
    if st.session_state['time_pattern_ids']:
        for id in st.session_state['time_pattern_ids']:
            is_saved = st.session_state[pwk('pattern_is_saved', id)]

            label = st.session_state[pwk('pattern_label', id)]
            color = st.session_state[pwk('pattern_color', id)]

            with st.expander(f':{color}[{label}]'):
                st.header('General')
                st.text_input(
                    'Label',
                    key=pwk('pattern_label', id)
                )
                st.text_input(
                    'File name',
                    key=pwk('pattern_filename', id),
                    disabled=is_saved is True,
                )

                if is_saved:
                    st.button(
                        'Update',
                        key=pwk('update_pattern', id),
                        on_click=lambda id=id: save_pattern(
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
                        key=pwk('save_pattern', id),
                        on_click=lambda id=id: save_pattern(
                            st.session_state,
                            id,
                            notify_callback=st.toast
                        ),
                        use_container_width=True,
                    )
                st.button(
                    'Delete',
                    key=pwk('delete_pattern', id),
                    on_click=(
                        lambda id=id: delete_pattern(st.session_state, id)
                    ),
                    use_container_width=True,
                    type='primary'
                )

                st.divider()

                st.header('Ocillator')
                col1, col2 = st.columns([8, 2])
                col1.number_input(
                    'Interval',
                    step=1,
                    key=pwk('oscillator_interval', id)
                )
                col2.selectbox(
                    'Unit',
                    options=[unit.value for unit in models.TimeUnit],
                    key=pwk('oscillator_interval_unit', id)
                )
                col1, col2 = st.columns(2)
                col1.text_input(
                    'Start timestamp',
                    key=pwk('oscillator_start_timestamp', id),
                )
                col2.text_input(
                    'End timestamp',
                    key=pwk('oscillator_end_timestamp', id),
                )

                st.divider()

                st.header('Multiplier')
                st.number_input(
                    'Ratio',
                    step=1,
                    key=pwk('multiplier_ratio', id)
                )

                st.divider()

                st.header('Randomizer')
                st.number_input(
                    'Deviation',
                    step=1,
                    key=pwk('randomizer_deviation', id)
                )
                st.selectbox(
                    'Direction',
                    options=[
                        direction.value
                        for direction in models.RandomizerDirection
                    ],
                    key=pwk('randomizer_direction', id),
                    help='...'
                )

                st.divider()

                st.header('Spreader')
                st.selectbox(
                    'Function',
                    options=[
                        func.value
                        for func in models.DistributionFunction
                    ],
                    key=pwk('spreader_function', id),
                    help='...'
                )

    else:
        st.markdown(
            (
                '<div style="text-align: center; color: grey;">'
                'No time patterns'
                '</div>'
            ),
            unsafe_allow_html=True
        )

    st.divider()

    st.button(
        'Create new',
        disabled=(
            len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS
        ),
        on_click=lambda: add_pattern(st.session_state),
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
        on_click=lambda: load_pattern(
            st.session_state,
            st.session_state['pattern_selected_for_load'],
            notify_callback=st.toast
        ),
        use_container_width=True,
    )

    if len(st.session_state['time_pattern_ids']) >= MAX_TIME_PATTERNS:
        st.write('*:grey[Maximum number of patterns]*')
