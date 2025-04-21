import pandas as pd
import streamlit as st
import re
import os
import chardet
from datetime import datetime

# Set page config
st.set_page_config(layout="wide", page_title="GPSSA Case Dashboard", page_icon="📊")

# Detect encoding
def detect_encoding(file):
    raw = file.read()
    result = chardet.detect(raw)
    file.seek(0)  # Reset pointer
    return result['encoding']

# Load CSV data
@st.cache_data
def load_data(uploaded_file):
    if uploaded_file is None:
        return None

    try:
        encoding = detect_encoding(uploaded_file)
        df = pd.read_csv(uploaded_file, encoding=encoding)
    except:
        fallback_encodings = ['utf-8-sig', 'windows-1256', 'iso-8859-6', 'cp1256', 'utf-8']
        for enc in fallback_encodings:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=enc)
                break
            except:
                continue
        else:
            return None

    for col in ['Case Start Date', 'Last Note Date']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
    df = df.dropna(subset=['Case Start Date'])
    df = df.fillna('')
    if 'Last Note' in df.columns:
        df['Last Note'] = df['Last Note'].astype(str).apply(lambda x: x.encode('raw_unicode_escape').decode('utf-8', errors='replace'))

    return df

# Categorize Last Note
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
            if prefix == 'SR' and number.startswith(('14', '15')):
                return f'Pending SR {number}'
            elif prefix == 'Incident' and number.startswith(('21', '22')):
                return f'Pending Incident {number}'
            elif prefix == 'Incident':
                return f'Pending Incident {number}'

    return 'Not Triaged'

# MAIN APP
def main():
    st.title("📊 GPSSA Case Management Dashboard")

    st.sidebar.markdown("### Developed by Anas H. Alrefai")
    st.sidebar.header("📂 Upload or Use Default CSV")

    uploaded_file = st.sidebar.file_uploader("Upload CSV file", type="csv")

    if uploaded_file:
        file_to_load = uploaded_file
        st.sidebar.success("Custom file uploaded.")
    else:
        default_path = r"C:\Users\Admin\Desktop\Gpssa\20April.csv"
        if os.path.exists(default_path):
            file_to_load = open(default_path, 'rb')
            st.sidebar.info("Using default file.")
        else:
            file_to_load = None
            st.sidebar.warning("Default file not found. Please upload a file.")

    df = load_data(file_to_load)
    if df is None:
        st.warning("No data loaded. Please upload a valid CSV file.")
        return

    df['Status'] = df['Last Note'].apply(categorize_case)
    df['SR/Incident Number'] = df['Status'].apply(lambda x: x.split()[-1] if x != 'Not Triaged' else '')

    target_users = ['anas.hasan', 'ali.babiker', 'mohammed.reda']
    all_users = ['DIT-Team'] + target_users

    st.sidebar.header("🔍 Filters")
    selected_user = st.sidebar.selectbox("Select User", all_users, index=0)
    selected_status = st.sidebar.selectbox("Filter by Status", ['All', 'Not Triaged', 'Pending SR/Incident'])

    min_date = df['Case Start Date'].min().date()
    max_date = df['Case Start Date'].max().date()
    date_range = st.sidebar.date_input("Date Range", [min_date, max_date], min_value=min_date, max_value=max_date)

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

    st.subheader(f"📈 Case Summary for {selected_user}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Cases", len(filtered_data))
    col2.metric("Pending", len(filtered_data[filtered_data['Status'] != 'Not Triaged']))
    col3.metric("Not Triaged", len(filtered_data[filtered_data['Status'] == 'Not Triaged']))

    if selected_status == 'Pending SR/Incident':
        st.subheader("🔖 Grouped by SR/Incident Number")
        grouped = filtered_data.groupby('SR/Incident Number').agg({
            'Case Id': 'count',
            'Current User Id': lambda x: ', '.join(set(x)),
            'Case Start Date': 'min',
            'Sub Category': lambda x: ', '.join(set(x))
        }).reset_index().rename(columns={
            'Case Id': 'Number of Cases',
            'Current User Id': 'Assigned To',
            'Case Start Date': 'First Case Date',
            'Sub Category': 'Categories'
        }).sort_values('Number of Cases', ascending=False)

        st.dataframe(grouped, use_container_width=True)

if __name__ == '__main__':
    main()
