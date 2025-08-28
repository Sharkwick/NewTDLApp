import streamlit as st
import threading
from AuthUI import setup_page,login, register
from SidebarUI import sidebar
from UX import get_ux_pending_tasks, get_ux_completed_tasks, get_task_metrics, task_add_ux
from firebase_utils import initialize_firebase
from functions import get_existing_groups, start_listener

setup_page()
db = initialize_firebase()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.nickname = ""

if not st.session_state.authenticated:
    st.markdown(
        "<h1 style='text-align: center;'>Wickz Day Planner</h1>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("## Free forever, as long as Streamlit keeps us online 😉")
    st.markdown("## 🔐 Login or Register")

    login_tab, register_tab = st.tabs(["Login", "Click Here to Register"])
    with login_tab: login(db)
    with register_tab: register(db)
    st.stop()

nickname  = st.session_state.nickname
tasks_ref = db.collection("tasks").document(nickname).collection("items")
docs = list(tasks_ref.stream())

pending_count, completed_count = sidebar(nickname, tasks_ref, db)

st.markdown("# Wickz Day Planner 2.0")
st.markdown("---")
st.markdown("## Task Management")
expander = st.expander("### 🔰 Create a New Task", expanded=False)
with expander:
    task_add_ux(tasks_ref)
st.markdown("---")
st.markdown("## Task Overview")
get_task_metrics(tasks_ref)
st.markdown("---")

t1,t2 = st.tabs(["Pending","Completed"])
with t1:
    get_ux_pending_tasks(tasks_ref)
with t2:
    get_ux_completed_tasks(tasks_ref)

if "listener_started" not in st.session_state:
    threading.Thread(target=start_listener, daemon=True).start()
    st.session_state.listener_started = True

if st.session_state.get("tasks_updated"):
    st.rerun()