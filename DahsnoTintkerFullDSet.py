import streamlit as st
import pandas as pd
import plotly.express as px
import io

st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")
st.title("📊 GPSSA Case Dashboard")

def match_column(df, possible_names):
    for col in df.columns:
        for name in possible_names:
            if col.strip().lower() == name.strip().lower():
                return col
    return None

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Identify relevant columns
    user_col = match_column(df, ["User", "Owner", "Assigned To"])
    status_col = match_column(df, ["Status"])
    sr_col = match_column(df, ["SR Number", "Incident Number", "Ticket Number"])
    date_col = match_column(df, ["Created Date", "Date"])
    type_col = match_column(df, ["Type", "Ticket Type"])

    if not all([user_col, status_col, sr_col]):
        st.error("Required columns not found. Make sure the file contains at least User, Status, and SR Number.")
    else:
        # Sidebar filters
        st.sidebar.header("🔍 Filters")
        user_filter = st.sidebar.selectbox("Select User", options=["All"] + sorted(df[user_col].dropna().unique().tolist()))
        status_filter = st.sidebar.selectbox("Select Status", options=["All"] + sorted(df[status_col].dropna().unique().tolist()))

        if type_col:
            type_filter = st.sidebar.selectbox("Select Type", options=["All"] + sorted(df[type_col].dropna().unique().tolist()))
        else:
            type_filter = "All"

        filtered_df = df.copy()
        if user_filter != "All":
            filtered_df = filtered_df[filtered_df[user_col] == user_filter]
        if status_filter != "All":
            filtered_df = filtered_df[filtered_df[status_col] == status_filter]
        if type_filter != "All" and type_col:
            filtered_df = filtered_df[filtered_df[type_col] == type_filter]

        # Group by SR/Incident Number
        st.subheader("📁 Grouped by SR/Incident Number")
        incident_number = st.selectbox("Select SR/Incident Number", options=["All"] + sorted(filtered_df[sr_col].dropna().unique().tolist()))

        if incident_number != "All":
            grouped_df = filtered_df[filtered_df[sr_col] == incident_number]
        else:
            grouped_df = filtered_df

        # Ownership message
        if user_filter != "All":
            st.markdown(f"✅ Devolved by **{user_filter}**")

        # Search functionality
        search_query = st.text_input("🔍 Search (EID, Mobile, Title, etc.)")
        if search_query:
            grouped_df = grouped_df[grouped_df.apply(lambda row: search_query.lower() in str(row.values).lower(), axis=1)]

        # Display table
        st.dataframe(grouped_df, use_container_width=True)

        # Download filtered data
        csv_buffer = io.StringIO()
        grouped_df.to_csv(csv_buffer, index=False)
        st.download_button("⬇️ Download Filtered Data", data=csv_buffer.getvalue(), file_name="filtered_cases.csv", mime="text/csv")

        # Summary
        st.markdown("### 📈 Summary Stats")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cases", len(filtered_df))
        col2.metric("Open Cases", len(filtered_df[filtered_df[status_col] == "Open"]))
        col3.metric("Closed Cases", len(filtered_df[filtered_df[status_col] == "Closed"]))

        # Charts
        if date_col:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            date_chart = df.groupby(df[date_col].dt.date).size().reset_index(name="Case Count")
            fig = px.line(date_chart, x=date_col, y="Case Count", title="📅 Cases Over Time")
            st.plotly_chart(fig, use_container_width=True)

        user_chart = df[user_col].value_counts().reset_index()
        user_chart.columns = ["User", "Case Count"]
        fig2 = px.bar(user_chart, x="User", y="Case Count", title="👤 Cases by User")
        st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Please upload a CSV file to get started.")
