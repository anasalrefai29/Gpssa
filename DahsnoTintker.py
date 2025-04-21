import streamlit as st
import pandas as pd
import os

# Set Streamlit page config
st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")

st.title("📊 GPSSA Case Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload your GPSSA CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        # Try different encodings
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(uploaded_file, encoding='latin1')

        # Display raw data
        if st.checkbox("Show Raw Data"):
            st.subheader("Raw Data")
            st.dataframe(df, use_container_width=True)

        # Convert date columns to datetime
        date_columns = ["Created On", "Resolved On"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')

        # Sidebar filters
        st.sidebar.header("Filter Data")

        if "Case Category" in df.columns:
            categories = df["Case Category"].dropna().unique().tolist()
            selected_category = st.sidebar.multiselect("Case Category", categories, default=categories)

            df = df[df["Case Category"].isin(selected_category)]

        if "Case Status" in df.columns:
            statuses = df["Case Status"].dropna().unique().tolist()
            selected_status = st.sidebar.multiselect("Case Status", statuses, default=statuses)

            df = df[df["Case Status"].isin(selected_status)]

        # Main dashboard
        st.subheader("Case Summary")

        if "Case Category" in df.columns:
            category_counts = df["Case Category"].value_counts()
            st.write("### Case Category Distribution")
            st.bar_chart(category_counts)

        if "Case Status" in df.columns:
            status_counts = df["Case Status"].value_counts()
            st.write("### Case Status Distribution")
            st.bar_chart(status_counts)

        if "Created On" in df.columns:
            df['Created Month'] = df["Created On"].dt.to_period('M').astype(str)
            created_monthly = df["Created Month"].value_counts().sort_index()
            st.write("### Cases Created Per Month")
            st.line_chart(created_monthly)

        if "Resolved On" in df.columns:
            df['Resolved Month'] = df["Resolved On"].dt.to_period('M').astype(str)
            resolved_monthly = df["Resolved Month"].value_counts().sort_index()
            st.write("### Cases Resolved Per Month")
            st.line_chart(resolved_monthly)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
