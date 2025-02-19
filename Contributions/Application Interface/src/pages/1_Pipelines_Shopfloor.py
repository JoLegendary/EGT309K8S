import streamlit as st
from streamlit_flow import streamlit_flow
from streamlit_flow.elements import StreamlitFlowNode, StreamlitFlowEdge
from streamlit_flow.state import StreamlitFlowState
from streamlit_cookies_controller import CookieController

from streamlit.runtime.scriptrunner import add_script_run_ctx
#from streamlit.runtime.scriptrunner_utils.script_run_context import get_script_run_ctx
from streamlit.runtime import Runtime
from streamlit.runtime.scriptrunner import (
    RerunData,
    ScriptRunContext,
    get_script_run_ctx,
)
from streamlit.runtime import get_instance

import joblib
import io
import datetime
import regex
import random
import tomllib
import requests

import gc
import asyncio
import time, threading

st.set_page_config(
  page_title="Shopfloor Demo",
  page_icon=""
)

cookie_con = CookieController()
uploaded_input = None
uploaded_predict = None
uploaded_predict_model = None


with open("/datas/appconfig.toml", "rb") as f:
    config = tomllib.load(f)
    servicesURI = config["services"]["URI"]
    print(servicesURI)

def status_breakdown(input):
    regexer = regex.compile(r"""^(\d+)-(\d+)(?::(.*))?$""")
    result = regex.search(input).groups()
    return {"code": result[:2], "message":result[2]}


def find_streamlit_main_loop():
    loops = []
    for obj in gc.get_objects():
        try:
            if isinstance(obj, asyncio.BaseEventLoop):
                loops.append(obj)
        except ReferenceError: pass
        
    main_thread = next((t for t in threading.enumerate() if t.name == 'MainThread'), None)
    if main_thread is None:
        raise Exception("No main thread")
    main_loop = next((lp for lp in loops if lp._thread_id == main_thread.ident), None) # type: ignore
    if main_loop is None:
        raise Exception("No event loop on 'MainThread'")
    
    return main_loop

def RunPipelines(ctx=None):
    st_error.empty()
    if st.session_state["pipelineLock"].locked(): return
    if uploaded_input is None or uploaded_predict is None:
        missings = []
        if uploaded_input is None: missings += ["Input data"]
        if uploaded_predict is None: missings += ["Prediction input data"]
        st_error.error(f"{", ".join(missings)} has to be given first! Click on the respective node(s) on the flow graph and upload the required file(s) in the context menu below the flow graph.")
        return
    def target(ctx,rt):
        with st.session_state["pipelineLock"]: # Practically allows only 1 run per session
            session = next((
                s.session
                for s in rt._session_mgr.list_sessions()
                if s.session.id == ctx.session_id
            ), None)
            _state = session.session_state["pipelineRunData"] = {
                "state": 0, # -1: No Active Pipe, 0: Running Pipe, 1: Finished Pipe
                "progress": 0,
                "services": {}
            }
            try:
                response = None
                for i, (servn, uri) in enumerate(servicesURI.items()):
                        post_input = None
                        _state["services"][servn] = {
                            "progress": 0,
                            "status": None,
                            "output": None
                        }
                        match(servn):
                            case "data_prep":    post_input = {"csv":("data.csv", uploaded_input.getvalue(), "text/csv")}
                            case "model_train":  post_input = {"csv":("data.csv", _state["services"]["data_prep"]["output"], "text/csv")}
                            case "predict":      post_input = {"csv":("data.csv", uploaded_predict.getvalue(), "text/csv")}
                        main_response = None
                        def req_target(*vargs, **kwargs):
                            nonlocal main_response
                            try:  main_response = requests.post(*vargs, **kwargs)
                            except Exception as er: main_response = er
                        t = threading.Thread(target=req_target, args=(uri + "/upload",), kwargs=dict(files=post_input), daemon=True)
                        t.start()
                        keep_poll = True
                        time.sleep(0.5)
                        while keep_poll:
                            if main_response is not None: keep_poll = False
                            response = requests.get(uri + "/poll")
                            if response is None: continue
                            try: json = response.json()
                            except: continue
                            if 199 < response.status_code < 300 and json is not None:
                                _state["services"][servn]["status"] = json["status"]
                                _state["services"][servn]["progress"] = json["percentage"]
                                _state["progress"] = ( 100 * i + json["percentage"] ) / len(servicesURI)
                            time.sleep(1.25)
                        if isinstance(main_response, Exception): raise main_response
                        if not(199 < main_response.status_code < 300):
                            raise requests.exceptions.ConnectionError()
                        _state["services"][servn]["output"] = main_response.content
            except requests.exceptions.ConnectionError as er:
                st_error.error(f"Error occured while trying to connect to '{servn}' service.") # Not always working dk why.
                _state["state"] = -1
            else:
                _state["state"] = 1
    if ctx is None: ctx = get_script_run_ctx()
    rt = Runtime.instance()
    t = threading.Thread(target=target, args=(ctx,rt), daemon=True)
    add_script_run_ctx(t)
    t.start()



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
if "pipelineRunData" not in st.session_state: st.session_state["pipelineRunData"] = {"state": -1}
#if "pipelineThread" not in st.session_state: st.session_state["pipelineThread"] = None
if "pipelineLock" not in st.session_state: st.session_state["pipelineLock"] = threading.Lock()





st.markdown(r"""
    # Pipeline Demo
    A demonstration!
""")

with st.sidebar:
    st.header("Pipeline Status")
    @st.fragment(run_every="1.55s")
    def deploy_sidebar_api():
        pState = st.session_state["pipelineRunData"]["state"]
        pipeline_progress = st.session_state["pipelineRunData"].get("progress")
        progressbar = st.empty()
        if pState == 0 and pipeline_progress < 100: progressbar.progress(int(pipeline_progress))
        st.text(f"{pipeline_progress:0.2f}% Complete" if pState > -1 else "No pipeline running")

    deploy_sidebar_api()

@st.fragment(run_every="1.5s")
def deploy_flow_state():
    global flow_state
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

    st.session_state["lastFlowSelect"] = st.session_state["flow_state"].selected_id
    st.session_state["lastUpdate"]["flowUpdate"] = time.time()

with st.container():
    deploy_flow_state()

st_error = st.empty()

col1, _, col2, _, col3 = st.columns((2,1,2,1,2))

with col3:
    @st.fragment(run_every="2s")
    def pipebut():
        st.button("Run Pipeline", on_click=RunPipelines, use_container_width=True, disabled=st.session_state["pipelineLock"].locked())
    pipebut()

@st.fragment(run_every="0.05s")
def NodesIO():
    global uploaded_input, uploaded_predict, uploaded_predict_model
    match(st.session_state.get("flow_interface", (0,))[0]):
        case 1:
            st.header("Input:")
            with st.container():
                uploaded_input = st.file_uploader("Drop training data here (.csv):", type=["csv"])
        case 2:
            st.header("Output:")
            lcol, rcol = st.columns((5,1))
            pData = st.session_state["pipelineRunData"]
            svcData = pData.get("services",{}).get("data_prep",{})
            dlFile = svcData.get("output")
            if dlFile is None: dlFile = b""
            with lcol:
                st.caption("""### Download CSV""", unsafe_allow_html=True)
            with rcol:
                st.download_button("Download", data=dlFile,
                                               file_name="processed_train_data.csv",
                                               disabled=pData["state"] == -1 or svcData.get("progress",0) < 100,
                                               mime="type/csv"
                )
        case 3:
            st.header("Output:")
            lcol, rcol = st.columns((5,1))
            pData = st.session_state["pipelineRunData"]
            svcData = pData.get("services",{}).get("model_train",{})
            dlFile = svcData.get("output")
            if dlFile is None: dlFile = b""
            #dlFName = regex.search(svcData["output"]) filename=(.+) I forgot i dumped js the content too lz to remake
            with lcol:
                st.caption("""### Download Model""", unsafe_allow_html=True)
            with rcol:
                st.download_button("Download", data=dlFile,
                                               file_name="model.pkl",
                                               disabled=pData["state"] == -1 or svcData.get("progress",0) < 100
                )
        case 4:
            st.header("Input:")
            lcol, _, rcol = st.columns((8,1,8))
            with lcol:
                uploaded_predict_model = st.file_uploader("Drop custom ML model here (.pkl):", type=["pkl"])
            with rcol:
                uploaded_predict = st.file_uploader("Drop testing data here (.csv):", type=["csv"])
        case 5:
            st.header("Output:")
            lcol, rcol = st.columns((5,1))
            pData = st.session_state["pipelineRunData"]
            svcData = pData.get("services",{}).get("predict",{})
            dlFile = svcData.get("output")
            if dlFile is None: dlFile = b""
            with lcol:
                st.caption("""### Download Prediction""", unsafe_allow_html=True)
            with rcol:
                st.download_button("Download", data=dlFile,
                                               file_name="prediction.csv",
                                               disabled=pData["state"] == -1 or svcData.get("progress",0) < 100
                )

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
