import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")

st.title("📊 GPSSA Case Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    # Clean column names
    df.columns = df.columns.str.strip()

    # Display raw data if needed
    with st.expander("🔍 View Raw Data"):
        st.dataframe(df)

    # Filter Section
    st.sidebar.header("🔍 Filters")

    user_filter = st.sidebar.selectbox("Select User", options=["All"] + sorted(df["User"].dropna().unique().tolist()))
    status_filter = st.sidebar.selectbox("Select Status", options=["All"] + sorted(df["Status"].dropna().unique().tolist()))

    # Filter logic
    filtered_df = df.copy()
    if user_filter != "All":
        filtered_df = filtered_df[filtered_df["User"] == user_filter]
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df["Status"] == status_filter]

    # Group by SR/Incident Number
    st.subheader("📁 Grouped by SR/Incident Number")
    incident_number = st.selectbox("Select SR/Incident Number", options=["All"] + sorted(filtered_df["SR Number"].dropna().unique().tolist()))

    if incident_number != "All":
        grouped_df = filtered_df[filtered_df["SR Number"] == incident_number]
    else:
        grouped_df = filtered_df

    # Add ownership info if 'User' exists
    if user_filter != "All":
        st.markdown(f"✅ Devolved by **{user_filter}**")

    # Search functionality
    search_query = st.text_input("🔍 Search (EID, Mobile, Title, etc.)")
    if search_query:
        grouped_df = grouped_df[grouped_df.apply(lambda row: search_query.lower() in str(row.values).lower(), axis=1)]

    st.dataframe(grouped_df, use_container_width=True)

    # Show summary numbers
    st.markdown("### 📈 Summary Stats")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cases", len(filtered_df))
    col2.metric("Open Cases", len(filtered_df[filtered_df["Status"] == "Open"]))
    col3.metric("Closed Cases", len(filtered_df[filtered_df["Status"] == "Closed"]))

    # Charts
    if "Created Date" in df.columns:
        df["Created Date"] = pd.to_datetime(df["Created Date"], errors='coerce')
        date_chart = df.groupby(df["Created Date"].dt.date).size().reset_index(name="Case Count")
        fig = px.line(date_chart, x="Created Date", y="Case Count", title="📅 Cases Over Time")
        st.plotly_chart(fig, use_container_width=True)

    if "User" in df.columns:
        user_chart = df["User"].value_counts().reset_index()
        user_chart.columns = ["User", "Case Count"]
        fig2 = px.bar(user_chart, x="User", y="Case Count", title="👤 Cases by User")
        st.plotly_chart(fig2, use_container_width=True)

else:
    st.info("Please upload a CSV file to continue.")
