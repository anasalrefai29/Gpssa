import streamlit as st
import pandas as pd
import os
import chardet

st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")

# Sidebar title
st.sidebar.title("GPSSA Case Dashboard")

# Default file paths (update these if needed)
default_file_paths = [
    "data/gpssa_cases.csv",
    "gpssa_cases.csv"
]

@st.cache_data
def detect_encoding(filepath):
    """Detect file encoding using chardet"""
    with open(filepath, "rb") as f:
        result = chardet.detect(f.read())
    return result['encoding']

@st.cache_data
def load_data(file):
    """Load and preprocess the GPSSA case data"""
    try:
        if hasattr(file, "read"):  # Uploaded file-like object
            raw_data = file.read()
            detected_encoding = chardet.detect(raw_data)['encoding']
            file.seek(0)
            df = pd.read_csv(file, encoding=detected_encoding)
        else:  # Local path
            encoding = detect_encoding(file)
            df = pd.read_csv(file, encoding=encoding)
    except Exception:
        # Try fallback encodings
        encodings = ['utf-8-sig', 'windows-1256', 'iso-8859-6', 'cp1256', 'utf-8']
        for enc in encodings:
            try:
                df = pd.read_csv(file, encoding=enc)
                break
            except Exception:
                continue
        else:
            return None
    return df

# Upload file via sidebar
uploaded_file = st.sidebar.file_uploader("Upload Case CSV File", type=["csv"])

df = None

# Priority: uploaded file > local default file
if uploaded_file:
    df = load_data(uploaded_file)
else:
    for path in default_file_paths:
        if os.path.exists(path):
            df = load_data(path)
            st.sidebar.success(f"Using default file: {path}")
            break

if df is None:
    st.error("No valid CSV file found or uploaded.")
    st.stop()

# Clean and rename columns for clarity
df.columns = [col.strip() for col in df.columns]
if "Case Category" in df.columns:
    df["Case Category"] = df["Case Category"].str.strip()
if "Module" in df.columns:
    df["Module"] = df["Module"].str.strip()
if "Status" in df.columns:
    df["Status"] = df["Status"].str.strip()
if "Created Date" in df.columns:
    df["Created Date"] = pd.to_datetime(df["Created Date"], errors='coerce')

# Sidebar filters
st.sidebar.subheader("Filters")
selected_category = st.sidebar.multiselect("Case Category", df["Case Category"].dropna().unique(), default=None)
selected_module = st.sidebar.multiselect("Module", df["Module"].dropna().unique(), default=None)
selected_status = st.sidebar.multiselect("Status", df["Status"].dropna().unique(), default=None)

# Apply filters
filtered_df = df.copy()
if selected_category:
    filtered_df = filtered_df[filtered_df["Case Category"].isin(selected_category)]
if selected_module:
    filtered_df = filtered_df[filtered_df["Module"].isin(selected_module)]
if selected_status:
    filtered_df = filtered_df[filtered_df["Status"].isin(selected_status)]

# Display summary
st.title("📊 GPSSA Case Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Total Cases", len(filtered_df))
col2.metric("Open Cases", (filtered_df["Status"] == "Open").sum())
col3.metric("Closed Cases", (filtered_df["Status"] == "Closed").sum())

# Show data table
st.subheader("Case Details")
st.dataframe(filtered_df, use_container_width=True)
