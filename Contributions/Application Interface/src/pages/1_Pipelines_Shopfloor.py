import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_cookies_controller import CookieController

from streamlit.runtime.scriptrunner import add_script_run_ctx
#from streamlit.runtime.scriptrunner.script_run_context import get_script_run_ctx
from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from streamlit.runtime import get_instance

import joblib
import io
import datetime
import regex

import time, threading

st.set_page_config(
  page_title="Shopfloor Demo",
  page_icon=""
)

cookie_con = CookieController(key="cookies")
def status_breakdown(input):
    regexer = regex.compile(r"""^(\d+)-(\d+)(?::(.*))?$""")
    result = regex.search(input).groups()
    return {"code": result[:2], "message":result[2]}

if 'flow_state' not in st.session_state:
    flow_state = cookie_con.get('streamlit_pipeline_overview')
    if flow_state is None:
        edge_arrowhead = {"type":"arrow","height":30,"width":30}
        edge_adParams = {
            "marker_end": edge_arrowhead,
            "animated": True
        }
        nodes = [
            StreamlitFlowNode("1", (-175, -85), {'content': 'Input'}, 'input', 'right'),
            StreamlitFlowNode("2", (-151, -15), {'content': 'Data Preprocessing'}, 'default', 'right', 'left'),
            StreamlitFlowNode("3", (15, -70), {'content': 'Model Training'}, 'default', 'right', 'left'),
            StreamlitFlowNode("4", (115, -5), {'content': 'Prediction'}, 'default', 'right', 'left'),
            StreamlitFlowNode("5", (195, -105), {'content': 'Output @ Save'}, 'output', 'right', 'left')
        ]
        edges = [
            StreamlitFlowEdge("1-2", "1", "2", "step", **edge_adParams),
            StreamlitFlowEdge("2-3", "2", "3", "smoothstep", **edge_adParams),
            StreamlitFlowEdge("3-4", "3", "4", "smoothstep", **edge_adParams),
            StreamlitFlowEdge("4-5", "4", "5", "step", **edge_adParams),
        ]
        st.session_state["flow_state"] = StreamlitFlowState(nodes, edges)
    else:
        flow_state = bytes.fromhex(flow_state["value"])
        byte_stream = io.BytesIO()
        byte_stream.write(flow_state)
        st.session_state["flow_state"] = joblib.load(byte_stream)

flow_state = st.session_state["flow_state"]

st.sidebar.header("Completion Progress")
st.markdown(r"""
    # Pipeline Demo
    A demonstration!
""")

progress_bar = st.sidebar.progress(0)
status_text = st.sidebar.empty()

"""
for i in range(1, 101):
    status_text.text("%i%% Complete" % i)
    progress_bar.progress(i)
    time.sleep(0.05)

progress_bar.empty()
"""

st.session_state["flow_state"] = flow_state = streamlit_flow('flow',
    flow_state,
    fit_view=True, 
    get_edge_on_click=True,
    get_node_on_click=True, 
    show_minimap=True, 
    hide_watermark=True, 
    allow_new_edges=True,
    min_zoom=1.0
)

col1, col2, col3 = st.columns(3)

with col1:
    st.button("Upload data to 'Input' node", on_click=lambda: print("Lmao"))

with col3:
    st.button("Run Pipeline", on_click=lambda: print("Lmao"))

currentLastUpdate = st.session_state["lastUpdate"] = time.time()

#tempfile_uuid = f"TEMP_{uuid.uuid4().hex}.temp"

byte_stream = io.BytesIO()
joblib.dump(flow_state, byte_stream)
cookie_con.set('streamlit_pipeline_overview',
   {
       "value": byte_stream.getvalue().hex(),
       "expiry_date": (datetime.datetime.now() + datetime.timedelta(days=1)).isoformat()
   }
)

edges =  sorted(flow_state.edges, key=lambda x: x.source)
connections = [[node for node in flow_state.nodes if node.id in [edge.source, edge.target]] for edge in edges]

while currentLastUpdate == st.session_state["lastUpdate"]:
    if time.time() - st.session_state["lastUpdate"] > 2.51:
        st.rerun()
        break
    time.sleep(0.15)