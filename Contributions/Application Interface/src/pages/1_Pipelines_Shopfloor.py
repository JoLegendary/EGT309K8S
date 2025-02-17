import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState

import time, threading

st.set_page_config(
  page_title="Shopfloor Demo",
  page_icon=""
)

if 'flow_state' not in st.session_state:
    nodes = [StreamlitFlowNode("1", (0, 0), {'content': 'Node 1'}, 'input', 'right')]
    edges = []
    globals()["flow_state"] = StreamlitFlowState(nodes, edges)

st.sidebar.header("Completion Progress")
st.markdown(    r"""
    # Pipeline Demo
    A demonstration!
""")

progress_bar = st.sidebar.progress(0)
status_text = st.sidebar.empty()

"""
for i in range(1, 101):
    new_rows = last_rows[-1, :] + np.random.randn(5, 1).cumsum(axis=0)
    status_text.text("%i%% Complete" % i)
    chart.add_rows(new_rows)
    progress_bar.progress(i)
    last_rows = new_rows
    time.sleep(0.05)

progress_bar.empty()
"""

flow_state = streamlit_flow('flow',
    flow_state,
    fit_view=True, 
    enable_node_menu=True,
    enable_edge_menu=True,
    enable_pane_menu=True,
    get_edge_on_click=True,
    get_node_on_click=True, 
    show_minimap=True, 
    hide_watermark=True, 
    allow_new_edges=True,
    min_zoom=0.0
)

st.button("Run Pipeline", on_click=lambda: print("Lmao"))

xxx = 0
class UpdateLoop:
    @staticmethod
    def update():
        global xxx
        if xxx % 100 == 0:
            print(f"{xxx//100} looped")
        xxx += 1
    def __init__(self, loop=True):
        self.stop = not(loop)
        def target():
            while not(self.stop):
                self.update()
                time.sleep(0.05)
        self.__update_thread = threading.Thread(target=target)
        self.__update_thread.start()
UpdateLoop = UpdateLoop()