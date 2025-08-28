import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from firebase_admin import firestore
from zoneinfo import ZoneInfo
import time

def get_existing_groups(docs):
    existing_groups = sorted({d.to_dict().get("group") for d in docs if d.exists})
    if ["All"] not in existing_groups:
        return ["All"] + existing_groups
    else:
        return existing_groups

def get_existing_groups_e_All(docs):
    existing_groups = sorted({d.to_dict().get("group") for d in docs if d.exists})
    return existing_groups

def docs_init_com(tasks_ref):
    docs_com = list(tasks_ref.where("completed", "==", True).stream())
    return docs_com

def docs_init_pen(tasks_ref):
    docs_pen = list(tasks_ref.where("completed", "==", False).stream())
    return docs_pen

def docs_init_all(tasks_ref):
    docs_all = list(tasks_ref.stream())
    return docs_all

def docs_init_Cust_Grp(tasks_ref, cat, groupname):
    docs_cust = list(
        tasks_ref.where("completed", "==", cat)
                 .where("group", "==", groupname)
                 .stream()
    )
    return docs_cust

def on_snapshot(doc_snapshot, changes, read_time):
    st.session_state.tasks_updated = True

def start_listener():
    db = st.session_state.db
    doc_watch = db.collection("tasks").on_snapshot(on_snapshot)

def format_duration(td):
    if not td or not isinstance(td, pd.Timedelta):
        return ""

    total_seconds = int(td.total_seconds())
    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    return ", ".join(parts) if parts else "less than a minute"

def time_restring(datestr):
    naive_dt = datetime.strptime(datestr, "%Y-%m-%d %H:%M")
    local_tz_name = time.tzname[0]
    local_offset_sec = -time.timezone
    offset_hours = local_offset_sec // 3600
    offset_minutes = (local_offset_sec % 3600) // 60
    offset_str = f"{offset_hours:+03d}:{offset_minutes:02d}"
    try:
        local_zone = ZoneInfo(time.tzname[0])
    except:
        local_zone = ZoneInfo("UTC")
    timestamp = naive_dt.replace(tzinfo=local_zone)
    iso_string = timestamp.isoformat()
    return timestamp

def format_task_timestamp(ts: datetime) -> str:
    if not isinstance(ts, datetime):
        return "N/A"
    tz_offset = timedelta(hours=5, minutes=30)
    local_time = ts + tz_offset
    return local_time.strftime("%d %B %Y at %H:%M:%S UTC+5:30")

def add_new_task(name, group, comment, tasks_ref):
    doc = {
        "task": name,
        "group": group,
        "comment": comment,
        "completed": False,
        "timestamp": firestore.SERVER_TIMESTAMP,
        "created_str": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    try:
        result = tasks_ref.add(doc)
        st.toast(f"✅ {name} successfully added to {group} task group!")
    except Exception as e:
        st.toast("❌ Failed to add task.")
