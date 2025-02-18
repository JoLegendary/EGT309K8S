import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_cookies_controller import CookieController

from streamlit.runtime.scriptrunner import add_script_run_ctx
#from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from streamlit.runtime.scriptrunner import (
    RerunData,
    ScriptRunContext,
    get_script_run_ctx,
)
from streamlit.commands.execution_control import _new_fragment_id_queue
from streamlit.runtime import get_instance

import joblib
import io
import datetime
import regex
import random
import tomllib

import time, threading

st.set_page_config(
  page_title="Shopfloor Demo",
  page_icon=""
)


with open("data/appconfig.toml", "rb") as f:
    config = tomllib.load(f)
    servicesURI = config["services"]["URI"]


cookie_con = CookieController(key="cookies")
def status_breakdown(input):
    regexer = regex.compile(r"""^(\d+)-(\d+)(?::(.*))?$""")
    result = regex.search(input).groups()
    return {"code": result[:2], "message":result[2]}


def RunPipelines():
    pass

if 'flow_state' not in st.session_state:
    flow_state = cookie_con.get('streamlit_pipeline_overview')
    if flow_state is None:
        edge_arrowhead = {"type":"arrow","height":30,"width":30}
        edge_adParams = {
            "marker_end": edge_arrowhead,
            "animated": True
        }
        nodes = [
            StreamlitFlowNode("1", (-255, -85), {'content': "Input"}, 'input', 'right', style={'color': 'white', 'backgroundColor': '#6666BB'}),
            StreamlitFlowNode("2", (-151, -15), {'content': 'Data Preprocessing'}, 'default', 'right', 'left'),
            StreamlitFlowNode("3", (15, -70), {'content': 'Model Training'}, 'default', 'right', 'left'),
            StreamlitFlowNode("4", (115, -5), {'content': 'Prediction'}, 'default', 'right', 'left'),
            StreamlitFlowNode("5", (195, -105), {'content': 'Output @ Save'}, 'output', 'right', 'left', style={'color': 'black', 'backgroundColor': '#FFAAAA'})
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

if "lastUpdate" not in st.session_state: st.session_state["lastUpdate"] = {}

st.markdown(r"""
    # Pipeline Demo
    A demonstration!
""")

pipeline_progress = -1

with st.sidebar:
    st.header("Pipeline Status")
    @st.fragment(run_every="1.5s")
    def deploy_sidebar_api():
        global pipeline_progress
        progressbar = st.empty()
        if 0 <= pipeline_progress < 100: progressbar.progress(int(pipeline_progress))
        st.text(f"{pipeline_progress:0.2f}% Complete" if pipeline_progress >= 0 else "No pipeline running")

    deploy_sidebar_api()

@st.fragment(run_every="1.5s")
def deploy_flow_state():
    global flow_state, pipeline_progress
    pipeline_progress = min(1 - random.random() * random.random() + 0.015, 1) * 100
    st.session_state["flow_state"] = flow_state = streamlit_flow('flow',
        flow_state,
        fit_view=True, 
        get_edge_on_click=True,
        get_node_on_click=True, 
        show_minimap=True, 
        hide_watermark=True, 
        allow_new_edges=True,
        min_zoom=0.5
    )

    selected_node = st.session_state["flow_state"].selected_id
    if st.session_state.get("lastFlowSelect", None) != selected_node:
        match(selected_node):
            case "1" | "2" | "3" | "4" | "5":
                st.session_state["flow_interface"] = ( (st.session_state.get("flow_interface", (None,))[0] != int(selected_node)) * int(selected_node), time.perf_counter())
        rerun_req = st.session_state.get("NodesIORerun")
        if rerun_req is not None: rerun_req()

    st.session_state["lastFlowSelect"] = st.session_state["flow_state"].selected_id
    st.session_state["lastUpdate"]["flowUpdate"] = time.time()

with st.container():
    deploy_flow_state()

col1, _, col2, _, col3 = st.columns((2,1,2,1,2))

with col3:
    st.button("Run Pipeline", on_click=RunPipelines, use_container_width=True)

@st.fragment(run_every="0.05s")
def NodesIO():
    match(st.session_state.get("flow_interface", (0,))[0]):
        case 1:
            st.header("Input:")
            with st.container():
                st.file_uploader("Drop training data here (.csv):", type=["csv"])
        case 3:
            st.header("Output:")
            lcol, rcol = st.columns((5,1))
            with lcol:
                st.caption("""### Download Model""", unsafe_allow_html=True)
            with rcol:
                st.download_button("Download", "content", "app.py")
        case 5:
            st.header("Output:")
            lcol, rcol = st.columns((5,1))
            with lcol:
                st.caption("""### Download Model""", unsafe_allow_html=True)
            with rcol:
                st.download_button("Download", "content", "app.py")

NodesIO()

currentLastUpdate = st.session_state["lastUpdate"]["scriptUpdate"] = time.time()

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
