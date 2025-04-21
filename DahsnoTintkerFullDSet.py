import streamlit as st
import pandas as pd
import plotly.express as px

# Load the CSV file
df = pd.read_csv("/mnt/data/SupportRequest_20250421_182402FUllDataSet.csv")

# Convert 'Created Date' to datetime if exists
if 'Created Date' in df.columns:
    df['Created Date'] = pd.to_datetime(df['Created Date'], errors='coerce')

st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")
st.title("📊 GPSSA Case Dashboard")

# Ownership info
st.markdown("**Devolved by Anas H. Alrefai**")

# Sidebar Filters
with st.sidebar:
    st.header("Filters")

    # Select User
    users = ['All'] + sorted(df['Admin'].dropna().unique().tolist()) if 'Admin' in df.columns else ['All']
    selected_user = st.selectbox("Select User", users)

    # Select Category
    categories = ['All'] + sorted(df['Category'].dropna().unique().tolist()) if 'Category' in df.columns else ['All']
    selected_category = st.selectbox("Select Category", categories)

    # Select Status
    statuses = ['All'] + sorted(df['Status'].dropna().unique().tolist()) if 'Status' in df.columns else ['All']
    selected_status = st.selectbox("Select Status", statuses)

    # Search Bar
    search_term = st.text_input("🔍 Search by any column (EID, Mobile, Case Id, etc.)")

# Filter Logic
filtered_df = df.copy()
if selected_user != 'All':
    filtered_df = filtered_df[filtered_df['Admin'] == selected_user]
if selected_category != 'All':
    filtered_df = filtered_df[filtered_df['Category'] == selected_category]
if selected_status != 'All':
    filtered_df = filtered_df[filtered_df['Status'] == selected_status]
if search_term:
    search_term = search_term.lower()
    filtered_df = filtered_df[filtered_df.apply(lambda row: row.astype(str).str.lower().str.contains(search_term).any(), axis=1)]

# KPIs
st.subheader("📌 Summary KPIs")
col1, col2, col3 = st.columns(3)
col1.metric("Total Cases", len(filtered_df))
col2.metric("Open Cases", len(filtered_df[filtered_df['Status'].str.lower() == 'open']) if 'Status' in filtered_df.columns else "N/A")
col3.metric("Closed Cases", len(filtered_df[filtered_df['Status'].str.lower() == 'closed']) if 'Status' in filtered_df.columns else "N/A")

# Case Table
st.subheader("🗂️ Case Details")
st.dataframe(filtered_df.reset_index(drop=True), use_container_width=True)

# Charts Section
st.subheader("📈 Trends and Charts")

if 'Category' in filtered_df.columns:
    fig_cat = px.histogram(filtered_df, x='Category', title='Cases by Category', color='Category')
    st.plotly_chart(fig_cat, use_container_width=True)

if 'Created Date' in filtered_df.columns:
    time_df = filtered_df.copy()
    time_df['Month'] = time_df['Created Date'].dt.to_period('M').astype(str)
    fig_time = px.histogram(time_df, x='Month', title='Cases Over Time (Monthly)', color='Month')
    st.plotly_chart(fig_time, use_container_width=True)

if 'Admin' in filtered_df.columns:
    fig_admin = px.histogram(filtered_df, x='Admin', title='Cases by Admin', color='Admin')
    st.plotly_chart(fig_admin, use_container_width=True)

if 'SubCategory' in filtered_df.columns:
    fig_subcat = px.histogram(filtered_df, x='SubCategory', title='Top Subcategories', color='SubCategory')
    st.plotly_chart(fig_subcat, use_container_width=True)

st.markdown("---")
st.markdown("🔁 **Tip:** You can search and filter data from the left panel or use the search box to look up any keyword from the table.")
