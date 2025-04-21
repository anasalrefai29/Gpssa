import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")
st.title("📊 GPSSA Case Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Try reading with UTF-8, fallback to ISO-8859-1
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')

        # Show preview
        st.subheader("Data Preview")
        st.dataframe(df.head())

        # Convert dates if possible
        if "Created Date" in df.columns:
            df["Created Date"] = pd.to_datetime(df["Created Date"], errors='coerce')

        # Sidebar filters
        st.sidebar.header("🔍 Filter Cases")

        if "Case Category" in df.columns:
            selected_category = st.sidebar.multiselect(
                "Case Category",
                df["Case Category"].dropna().unique(),
                default=None
            )
            if selected_category:
                df = df[df["Case Category"].isin(selected_category)]

        if "Case Status" in df.columns:
            selected_status = st.sidebar.multiselect(
                "Case Status",
                df["Case Status"].dropna().unique(),
                default=None
            )
            if selected_status:
                df = df[df["Case Status"].isin(selected_status)]

        if "Created By" in df.columns:
            selected_creator = st.sidebar.multiselect(
                "Created By",
                df["Created By"].dropna().unique(),
                default=None
            )
            if selected_creator:
                df = df[df["Created By"].isin(selected_creator)]

        # KPIs
        st.subheader("📈 Summary Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Cases", len(df))
        if "Case Status" in df.columns:
            col2.metric("Open Cases", df["Case Status"].str.lower().eq("open").sum())
            col3.metric("Closed Cases", df["Case Status"].str.lower().eq("closed").sum())

        # Pie chart - Case Categories
        if "Case Category" in df.columns:
            st.subheader("🧩 Case Distribution by Category")
            category_counts = df["Case Category"].value_counts().reset_index()
            category_counts.columns = ["Category", "Count"]
            fig1 = px.pie(category_counts, names="Category", values="Count", title="Case Categories")
            st.plotly_chart(fig1, use_container_width=True)

        # Bar chart - Created By
        if "Created By" in df.columns:
            st.subheader("👤 Cases by Creator")
            creator_counts = df["Created By"].value_counts().reset_index()
            creator_counts.columns = ["Created By", "Count"]
            fig2 = px.bar(creator_counts, x="Created By", y="Count", title="Cases by Creator")
            st.plotly_chart(fig2, use_container_width=True)

        # Line chart - Cases over Time
        if "Created Date" in df.columns:
            st.subheader("📅 Cases Over Time")
            df["Created Date Only"] = df["Created Date"].dt.date
            date_counts = df.groupby("Created Date Only").size().reset_index(name="Count")
            fig3 = px.line(date_counts, x="Created Date Only", y="Count", title="Cases Over Time")
            st.plotly_chart(fig3, use_container_width=True)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("👈 Please upload a CSV file to begin.")
