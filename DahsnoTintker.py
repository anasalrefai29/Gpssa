import pandas as pd
import streamlit as st
import os

st.set_page_config(layout="wide")
st.title("GPSSA Case Dashboard")

# File uploader
uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Clean and preprocess data
        if 'Case Start Date' in df.columns:
            df['Case Start Date'] = pd.to_datetime(df['Case Start Date'], errors='coerce')
            df['Start Date'] = df['Case Start Date'].dt.date
        else:
            st.error("Missing 'Case Start Date' column in the uploaded CSV.")
            st.stop()

        # Filters
        request_types = df["Request Type"].dropna().unique() if "Request Type" in df.columns else []
        sub_categories = df["Sub Category"].dropna().unique() if "Sub Category" in df.columns else []
        users = df["Current User Id"].dropna().unique() if "Current User Id" in df.columns else []

        selected_request_type = st.sidebar.multiselect("Request Type", request_types)
        selected_sub_category = st.sidebar.multiselect("Sub Category", sub_categories)
        selected_user = st.sidebar.multiselect("Current User Id", users)

        start_date = st.sidebar.date_input("Start Date", value=pd.to_datetime("2023-01-01").date())
        end_date = st.sidebar.date_input("End Date", value=pd.to_datetime("today").date())

        # Apply filters
        filtered_df = df.copy()

        if selected_request_type:
            filtered_df = filtered_df[filtered_df["Request Type"].isin(selected_request_type)]

        if selected_sub_category:
            filtered_df = filtered_df[filtered_df["Sub Category"].isin(selected_sub_category)]

        if selected_user:
            filtered_df = filtered_df[filtered_df["Current User Id"].isin(selected_user)]

        filtered_df = filtered_df[
            (filtered_df["Start Date"] >= start_date) &
            (filtered_df["Start Date"] <= end_date)
        ]

        # Show results
        st.markdown(f"### Filtered Cases: {len(filtered_df)}")
        st.dataframe(filtered_df)

    except Exception as e:
        st.error(f"An error occurred: {e}")
else:
    st.info("Please upload a CSV file to begin.")
