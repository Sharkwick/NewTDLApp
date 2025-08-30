from datetime import datetime
from firebase_admin import firestore
from zoneinfo import ZoneInfo
import streamlit as st
import pandas as pd
from functions import get_existing_groups, docs_init_com, docs_init_pen, format_duration, docs_init_all, \
    docs_init_Cust_Grp, time_restring, format_task_timestamp, add_new_task, get_existing_groups_e_All


def get_existing_groups_e_all(docs):
    pass


def get_ux_pending_tasks(tasks_ref):
    docs_all_master = docs_init_all(tasks_ref)
    docs = docs_init_pen(tasks_ref)
    existing_groups = get_existing_groups(docs)
    existing_groupswall = get_existing_groups_e_All(docs)

    pending_count2 = sum(1 for doc in docs_all_master if not doc.to_dict().get("completed", False))

    if not pending_count2:
        st.markdown(f"## No pending tasks 🎉")
    else:
        selected_group_pen = st.selectbox("Select a group to filter tasks:", existing_groups, key="selgrppen")

        if selected_group_pen == "All":
            fil_docs = docs
        else:
            fil_docs = docs_init_Cust_Grp(tasks_ref, False,selected_group_pen)

        if selected_group_pen == "All":
            fil_docs_all = docs_init_all(tasks_ref)
        else:
            fil_docs_all = docs_init_Cust_Grp(tasks_ref, True,selected_group_pen)

        task_data = []
        doc_refs = []

        completed_count = sum(1 for doc in fil_docs_all if doc.to_dict().get("completed", True))
        pending_count = sum(1 for doc in fil_docs if not doc.to_dict().get("completed", False))
        completion_Percent = (completed_count / (pending_count + completed_count)) * 100 if completed_count + pending_count > 0 else 0
        tgcount = completed_count + pending_count

        for doc in fil_docs:
            data = doc.to_dict()
            task_data.append({
                "Task Name": data.get("task", ""),
                "Task Group": data.get("group", "General"),
                "Task Description": data.get("comment", ""),
                "Start Date & Time": data.get("timestamp").strftime("%Y-%m-%d %H:%M") if data.get("timestamp") else "",
                "Completed ?": data.get("completed", False),
                "Delete ?": data.get("delete", False)
            })
            doc_refs.append(doc.reference)

        df = pd.DataFrame(task_data).reset_index(drop=True)

        if "original_df" not in st.session_state:
            st.session_state.original_df = df.copy()
        else:
            st.session_state.original_df = st.session_state.original_df.reset_index(drop=True)

        with ((st.form(key="task_edit_form_Pen"))):
            if selected_group_pen == "All":
                st.markdown(f"#### ⌛ {selected_group_pen} Pending Tasks")
            else:
                st.markdown(f"#### ⌛ {selected_group_pen} Pending Tasks ({tgcount})")
            if selected_group_pen != "All":
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"Pending Tasks : {pending_count}")
                col2.markdown(f"Completed Tasks : {completed_count}")
                col3.markdown(f"Completion : {completion_Percent:.0f}%")
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Task Name": st.column_config.TextColumn("Task Name", pinned="left"),
                    "Task Group": st.column_config.SelectboxColumn(
                        "Task Group",
                        help="Select from an Existing Task Group",
                        options=existing_groupswall,
                        required=True,
                    )
                },
                disabled=[],
            )
            submitted = st.form_submit_button("🔃 Save Changes")
            Delconf = st.form_submit_button("❌ Delete Selected Items")
            rerun_needed = False
            if Delconf:
                for i, row in edited_df.iterrows():
                    taskname = row.get("Task Name")
                    taskgroup = row.get("Task Group")
                    if row.get("Delete ?", False):
                        try:
                            doc_refs[i].delete()
                            st.toast(f"🗑️ {taskname} deleted from {taskgroup}")
                            rerun_needed = True
                        except Exception as e:
                            st.toast(f"⚠️ Error deleting task {i}: {e}")
                        continue

            if submitted:
                for i, row in edited_df.iterrows():
                    if i >= len(st.session_state.original_df):
                        st.toast(f"⚠️ Skipping row {i}: index out of bounds")
                        continue

                    original_row = st.session_state.original_df.iloc[i]
                    has_changes = any([
                        row.get("Task Name") != original_row.get("Task Name"),
                        row.get("Task Group") != original_row.get("Task Group"),
                        row.get("Task Description") != original_row.get("Task Description"),
                        row.get("Start Date & Time") != original_row.get("Start Date & Time"),
                        row.get("Completed ?") != original_row.get("Completed ?")
                    ])

                    if has_changes:
                        updated_data = {
                            "task": row["Task Name"],
                            "group": row["Task Group"],
                            "comment": row["Task Description"],
                            "timestamp": time_restring(row["Start Date & Time"]),
                            "completed": row["Completed ?"],
                            "completed time": firestore.SERVER_TIMESTAMP if row["Completed ?"] else None
                        }
                        try:
                            doc_refs[i].update(updated_data)
                            st.toast(f"✅ {row['Task Name']} attributes updated!")
                            rerun_needed = True
                        except Exception as e:
                            st.toast(f"⚠️ Error updating task {row['Task Name']}: {e}")

                st.session_state.original_df = edited_df.copy()

            if rerun_needed:
                st.rerun()


def get_ux_completed_tasks(tasks_ref):
    docs_all_master = docs_init_all(tasks_ref)
    docs = docs_init_com(tasks_ref)
    all_docs = docs_init_all(tasks_ref)
    existing_groups = get_existing_groups(docs)

    # Corrected completion logic
    completed_count2 = sum(1 for doc in docs_all_master if doc.to_dict().get("completed", True))

    if not completed_count2:
        edited_df = st.markdown(f"## No completed tasks ⌛")
    else:
        selected_group_com = st.selectbox("Select a group to filter tasks:", existing_groups, key="selgrpcom")

        fil_docs = docs if selected_group_com == "All" else [d for d in docs if d.to_dict().get("group", "General") == selected_group_com]
        fil_docs_all = all_docs if selected_group_com == "All" else docs_init_Cust_Grp(tasks_ref, False, selected_group_com)

        task_data = []
        doc_refs = []

        completed_count = sum(1 for doc in fil_docs if doc.to_dict().get("completed", True))
        pending_count = sum(1 for doc in fil_docs_all if not doc.to_dict().get("completed", False))
        total_tasks = completed_count + pending_count
        if completed_count > 0 and pending_count > 0:
            completion_percent = round((completed_count / total_tasks) * 100, 0) if total_tasks > 0 else 0

        for d in fil_docs:
            doc_data = d.to_dict()
            timestamp = doc_data.get("timestamp")
            completed_time = doc_data.get("completed time")

            if timestamp and completed_time:
                time_delta = completed_time - timestamp
                duration_str = format_duration(pd.to_timedelta(time_delta))
                completed_date_str = completed_time.strftime("%Y-%m-%d %H:%M")
            else:
                duration_str = ""
                completed_date_str = ""

            added_date_str = timestamp.strftime("%Y-%m-%d %H:%M") if timestamp else ""

            task_data.append({
                "Task Name": doc_data.get("task", ""),
                "Task Group": doc_data.get("group", "General"),
                "Task Description": doc_data.get("comment", ""),
                "Added Date": added_date_str,
                "Completed Date": completed_date_str,
                "Task Duration": duration_str,
                "Completed": bool(doc_data.get("completed", False))
            })
            doc_refs.append(d.reference)

        df = pd.DataFrame(task_data).reset_index(drop=True)

        # Store original for change detection
        if "original_df" not in st.session_state:
            st.session_state.original_df = df.copy()
        else:
            st.session_state.original_df = st.session_state.original_df.reset_index(drop=True)

        with st.form(key="task_edit_form_com"):
            if selected_group_com == "All":
                st.markdown(f"#### ✅ {selected_group_com} Completed Tasks")
            else:
                st.markdown(f"#### ✅ {selected_group_com} Completed Tasks ({total_tasks})")
            if selected_group_com != "All":
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"Pending Tasks: {pending_count}")
                col2.markdown(f"Completed Tasks: {completed_count}")
                col3.markdown(f"Completion: {completion_percent:.0f}%")

            edited_df = st.data_editor(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Task Name": st.column_config.TextColumn("Task Name", pinned="left"),
                },
                disabled=["Task Name", "Task Group", "Task Description", "Completed Date", "Task Duration"],
            )

            submitted = st.form_submit_button("🔃 Save Changes")

        if submitted:
            hide_exp = False
            for i, row in edited_df.iterrows():
                if i >= len(st.session_state.original_df):
                    st.toast(f"⚠️ Skipping row {i}: index out of bounds")
                    continue

                original_row = st.session_state.original_df.iloc[i]
                if not row.equals(original_row):
                    updated_data = {
                        "completed": bool(row["Completed"]),
                        "completed_time": datetime.now().replace(tzinfo=ZoneInfo("Asia/Colombo"))
                    }

                    task_name = row["Task Name"]
                    try:
                        doc_refs[i].update(updated_data)
                        st.toast(f"✅ {task_name} updated successfully!")
                    except Exception as e:
                        st.toast(f"⚠️ Error updating {task_name}: {e}")

            st.session_state.original_df = edited_df.copy()
            st.rerun()

    return edited_df


def  get_task_metrics(tasks_ref):
    com_docs = docs_init_com(tasks_ref)
    pen_docs = docs_init_pen(tasks_ref)

    comc = sum(1 for doc in com_docs if doc.to_dict().get("completed") is True)
    penc = sum(1 for doc in pen_docs if doc.to_dict().get("completed") is not True)
    totc = comc + penc
    Completion_Perc_cal = round(comc/totc,2)*100 if totc > 0 else 0
    Completion_Perc = f"{Completion_Perc_cal:.0f}%" if totc > 0 else 0
    col1, col2, col3 , col4 = st.columns(4)
    col1.metric(label="📃 Total Tasks", value=totc)
    col2.metric(label="⌛ Pending Tasks", value=penc)
    col3.metric(label="✅ Completed Tasks", value=comc)
    col4.metric(label="*️⃣ Completion Percentage", value=Completion_Perc)

def delete_task(doc_id, task_text, tasks_ref):
    tasks_ref.document(doc_id).delete()
    st.toast(f"❌ Deleted '{task_text}'.")
    st.rerun()

def task_add_ux(tasks_ref):
    docs = docs_init_all(tasks_ref)
    existing_groups = get_existing_groups_e_All(docs)
    group_count = len(existing_groups)

    with st.form("add_task_form", clear_on_submit=True):
        task_txt = st.text_input("📝 Task Name")
        c1, c2 = st.columns(2)
        group_cust = c1.text_input("➕ Create New Group")
        group_sel = c2.selectbox("📂 Or select an existing group", options=existing_groups, index=0)
        comment = st.text_area("💬 Task Description")
        if group_count > 1:
            if group_cust.strip() == "" and group_sel.strip() == "":
                group_cust = "General"
            else:
                group_cust = group_sel
        else:
            group_cust = "General"

        if st.form_submit_button("✅ Add Task"):
            final_grp = group_cust.strip() or group_sel
            if task_txt.strip():
                add_new_task(task_txt.strip(), final_grp, comment.strip(), tasks_ref)
                st.rerun()
