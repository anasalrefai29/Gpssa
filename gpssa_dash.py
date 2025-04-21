import pandas as pd
import streamlit as st
import re
import os
import chardet
from datetime import datetime

# Set page config
st.set_page_config(layout="wide", page_title="GPSSA Case Dashboard", page_icon="📊")

# Function to detect file encoding
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

# Load data function with robust file handling
@st.cache_data
def load_data(file):
    """Load and preprocess the GPSSA case data"""
    if file is None:
        return None

    try:
        detected_encoding = detect_encoding(file.name)
    except Exception:
        detected_encoding = 'utf-8-sig'

    try:
        df = pd.read_csv(file, encoding=detected_encoding)
    except Exception:
        encodings = ['utf-8-sig', 'windows-1256', 'iso-8859-6', 'cp1256', 'utf-8']
        for enc in encodings:
            try:
                df = pd.read_csv(file, encoding=enc)
                break
            except Exception:
                continue
        else:
            return None

    date_columns = ['Case Start Date', 'Last Note Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')

    df = df.dropna(subset=['Case Start Date'])
    df = df.fillna('')

    if 'Last Note' in df.columns:
        df['Last Note'] = df['Last Note'].astype(str).apply(
            lambda x: x.encode('raw_unicode_escape').decode('utf-8', errors='replace'))

    return df

# Main App
def main():
    st.title("📊 GPSSA Case Management Dashboard")

    # Sidebar Attribution
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Developed by Anas H. Alrefai")

    # Sidebar File Upload
    st.sidebar.header("📂 Data Source")
    uploaded_file = st.sidebar.file_uploader("Upload CSV File", type="csv")

    # Default file path fallback
    default_file_paths = [
        r"C:\Users\Admin\Desktop\Gpssa\20April.csv",
        os.path.join(os.path.dirname(__file__), "20April.csv"),
        os.path.join(os.getcwd(), "20April.csv"),
        "20April.csv"
    ]
    if uploaded_file is not None:
        df = load_data(uploaded_file)
    else:
        for path in default_file_paths:
            if os.path.exists(path):
                df = load_data(open(path, "rb"))
                st.sidebar.success(f"Using default file: {path}")
                break
        else:
            df = None
            st.sidebar.warning("No file uploaded and no default file found")

    if df is None:
        st.warning("Please upload a valid CSV file to continue.")
        return

    # Define users
    target_users = ['anas.hasan', 'ali.babiker', 'mohammed.reda']
    all_users = ['DIT-Team'] + target_users

    def categorize_case(note):
        if pd.isna(note) or str(note).strip() == '':
            return 'Not Triaged'
        note = str(note).lower()
        patterns = [
            (r'(sr|service request|اس ار|طلب خدمة)\s*[:#]?\s*(\d{4,5})', 'SR'),
            (r'(inc|incident|انسدنت|حالة)\s*[:#]?\s*(\d{4,5})', 'Incident'),
            (r'\b(1[45]\d{3})\b', 'SR'),
            (r'\b(2[12]\d{3})\b', 'Incident'),
            (r'(tkt|ticket|تيكت)\s*[_:]?\s*(\d{4,5})', 'Incident')
        ]
        for pattern, prefix in patterns:
            matches = re.finditer(pattern, note)
            for match in matches:
                number = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if prefix == 'SR' and (number.startswith('14') or number.startswith('15')):
                    return f'Pending SR {number}'
                elif prefix == 'Incident' and (number.startswith('21') or number.startswith('22')):
                    return f'Pending Incident {number}'
                elif prefix == 'Incident':
                    return f'Pending Incident {number}'
        return 'Not Triaged'

    df['Status'] = df['Last Note'].apply(categorize_case)
    df['SR/Incident Number'] = df['Status'].apply(lambda x: x.split()[-1] if x != 'Not Triaged' else '')

    # Filters
    st.sidebar.header("🔍 Filters")
    selected_user = st.sidebar.selectbox("Select User", all_users, index=0)
    status_options = ['All', 'Not Triaged', 'Pending SR/Incident']
    selected_status = st.sidebar.selectbox("Filter by Status", status_options, index=0)

    min_date = df['Case Start Date'].min().to_pydatetime().date()
    max_date = df['Case Start Date'].max().to_pydatetime().date()
    date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

    # Apply filters
    if selected_user == 'DIT-Team':
        user_filtered = df[df['Current User Id'].isin(target_users)]
    else:
        user_filtered = df[df['Current User Id'] == selected_user]

    if len(date_range) == 2:
        start_date, end_date = date_range
        date_filtered = user_filtered[
            (user_filtered['Case Start Date'].dt.date >= start_date) &
            (user_filtered['Case Start Date'].dt.date <= end_date)
        ]
    else:
        date_filtered = user_filtered

    if selected_status == 'Not Triaged':
        filtered_data = date_filtered[date_filtered['Status'] == 'Not Triaged']
    elif selected_status == 'Pending SR/Incident':
        filtered_data = date_filtered[date_filtered['Status'] != 'Not Triaged']
    else:
        filtered_data = date_filtered

    # Display Metrics
    st.subheader(f"📈 Case Summary for {selected_user}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", len(filtered_data))
    with col2:
        pending = filtered_data[filtered_data['Status'] != 'Not Triaged']
        st.metric("Pending SR/Incident", len(pending))
    with col3:
        st.metric("Not Triaged", len(filtered_data) - len(pending))

    # Group by SR/Incident Number
    if selected_status == 'Pending SR/Incident':
        st.subheader("🔖 Cases Grouped by SR/Incident Number")
        grouped_cases = filtered_data.groupby('SR/Incident Number').agg({
            'Case Id': 'count',
            'Current User Id': lambda x: ', '.join(set(x)),
            'Case Start Date': 'min',
            'Sub Category': lambda x: ', '.join(set(x))
        }).rename(columns={
            'Case Id': 'Number of Cases',
            'Current User Id': 'Assigned To',
            'Case Start Date': 'First Case Date',
            'Sub Category': 'Categories'
        }).sort_values('Number of Cases', ascending=False).reset_index()

        st.dataframe(grouped_cases, use_container_width=True)

# Run app
if __name__ == "__main__":
    main()
