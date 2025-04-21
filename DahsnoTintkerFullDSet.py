import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")
st.title("📊 GPSSA Case Dashboard")
st.caption("Devolved by **Anas H. Alrefai**")

uploaded_file = st.file_uploader("📂 Upload Full Dataset CSV File", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        df.columns = df.columns.str.strip()

        # Fix missing expected columns
        rename_map = {
            "Case Id": "SR Number",
            "Process Status": "Status",
            "Current User Id": "User",
            "Request Type": "Type",
        }
        df.rename(columns=rename_map, inplace=True)

        required_columns = ["User", "Status", "SR Number", "Type"]
        if not all(col in df.columns for col in required_columns):
            st.error("⚠️ Required columns not found. Please upload a valid file.")
        else:
            st.sidebar.header("Filters")

            # User filter with 'DIT Team' option
            users = sorted(df["User"].dropna().unique().tolist())
            user_filter = st.sidebar.selectbox("Select User", options=["All", "DIT Team"] + users)

            # Type filter (Incident / SR)
            type_filter = st.sidebar.selectbox("Select Type", options=["All", "Incident", "SR"])

            # Search by any text including SR Number, EID, etc.
            search_text = st.sidebar.text_input("🔍 Search (EID, Mobile, SR Number, etc.)")

            filtered_df = df.copy()

            if user_filter != "All":
                if user_filter == "DIT Team":
                    filtered_df = filtered_df[filtered_df["User"].str.contains("DIT", case=False, na=False)]
                else:
                    filtered_df = filtered_df[filtered_df["User"] == user_filter]

            if type_filter != "All":
                filtered_df = filtered_df[filtered_df["Type"].str.contains(type_filter, case=False, na=False)]

            if search_text:
                search_text = search_text.strip()
                mask = pd.Series(False, index=filtered_df.index)
                for col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
                filtered_df = filtered_df[mask]

            st.subheader("📋 Filtered Case Data")
            st.write(f"Showing **{len(filtered_df)}** cases")
            st.dataframe(filtered_df, use_container_width=True)

            # Download
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Filtered Data as CSV",
                csv,
                "filtered_cases.csv",
                "text/csv",
                key="download-csv",
            )

            # Grouping for Pending and Not Triaged
            pending_group = df[df["Status"].str.contains("Pending", case=False, na=False)]
            not_triaged_group = df[df["Status"].str.contains("Not Triaged", case=False, na=False)]

            st.subheader("🕒 Pending and Not Triaged Cases")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Pending Cases: {len(pending_group)}**")
                st.dataframe(pending_group, use_container_width=True)
            with col2:
                st.markdown(f"**Not Triaged Cases: {len(not_triaged_group)}**")
                st.dataframe(not_triaged_group, use_container_width=True)

            # Linking SR/Incidents with their cases
            st.subheader("🔗 SR/Incident Linking")
            grouped_link = df.groupby(["SR Number", "Type"]).size().reset_index(name="Linked Cases Count")
            st.dataframe(grouped_link, use_container_width=True)

            # Visualization
            st.subheader("📈 Request Type and Status Breakdown")
            grouped = df.groupby(["Type", "Status"]).size().reset_index(name="Count")
            fig = px.bar(grouped, x="Type", y="Count", color="Status", barmode="group", text="Count")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
else:
    st.warning("📌 Please upload a CSV file to begin.")
