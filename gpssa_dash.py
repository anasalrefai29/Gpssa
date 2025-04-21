import pandas as pd
import streamlit as st
import re
import os
import chardet
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

# Set page config first
st.set_page_config(layout="wide", page_title="GPSSA Case Dashboard", page_icon="📊")

# File selection function
def select_file():
    """Open a file dialog to select the CSV file"""
    try:
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes('-topmost', 1)
        filename = filedialog.askopenfilename(
            title="Select GPSSA CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")
        )
        root.destroy()
        return filename
    except Exception as e:
        st.error(f"Could not open file dialog: {str(e)}")
        return None

# Detect encoding
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

# Load data
@st.cache_data
def load_data(file_path):
    if not file_path or not os.path.exists(file_path):
        return None

    try:
        detected_encoding = detect_encoding(file_path)
    except Exception:
        detected_encoding = 'utf-8-sig'

    try:
        df = pd.read_csv(file_path, encoding=detected_encoding)
    except Exception:
        encodings = ['utf-8-sig', 'windows-1256', 'iso-8859-6', 'cp1256', 'utf-8']
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
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
        df['Last Note'] = df['Last Note'].astype(str).apply(lambda x: x.encode('raw_unicode_escape').decode('utf-8', errors='replace'))

    return df

# Categorization
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

# Main App
def main():
    st.title("📊 GPSSA Case Management Dashboard")

    if 'file_path' not in st.session_state:
        st.session_state.file_path = None

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Developed by Anas H. Alrefai")

    st.sidebar.header("📂 Data Source")
    file_option = st.sidebar.radio("Select data source:", ["Use default file", "Select different file"])

    if file_option == "Use default file":
        possible_paths = [
            r"C:\Users\Admin\Desktop\Gpssa\20April.csv",
            os.path.join(os.path.dirname(__file__), "20April.csv"),
            os.path.join(os.getcwd(), "20April.csv"),
            "20April.csv"
        ]
        for path in possible_paths:
            if os.path.exists(path):
                st.session_state.file_path = path
                st.sidebar.success(f"Using default file: {st.session_state.file_path}")
                break
        else:
            st.sidebar.warning("Default file not found")
            st.session_state.file_path = None
    else:
        if st.sidebar.button("Browse for CSV File"):
            selected_file = select_file()
            if selected_file:
                st.session_state.file_path = selected_file
                st.sidebar.success(f"Selected file: {st.session_state.file_path}")
            else:
                st.sidebar.error("No file selected")
                st.session_state.file_path = None

    if st.session_state.file_path:
        df = load_data(st.session_state.file_path)
    else:
        df = None

    if df is None:
        st.warning("Please select a valid CSV file to continue")
        return

    target_users = ['anas.hasan', 'ali.babiker', 'mohammed.reda']
    all_users = ['DIT-Team'] + target_users

    df['Status'] = df['Last Note'].apply(categorize_case)
    df['SR/Incident Number'] = df['Status'].apply(lambda x: x.split()[-1] if x != 'Not Triaged' else '')

    st.sidebar.header("🔍 Filters")
    selected_user = st.sidebar.selectbox("Select User", all_users, index=0)
    status_options = ['All', 'Not Triaged', 'Pending SR/Incident']
    selected_status = st.sidebar.selectbox("Filter by Status", status_options, index=0)

    min_date = df['Case Start Date'].min().to_pydatetime().date()
    max_date = df['Case Start Date'].max().to_pydatetime().date()
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
    with col1:
        st.metric("Total Cases", len(filtered_data))
    with col2:
        pending = filtered_data[filtered_data['Status'] != 'Not Triaged']
        st.metric("Pending SR/Incident", len(pending))
    with col3:
        st.metric("Not Triaged", len(filtered_data) - len(pending))

    if selected_status == 'Pending SR/Incident':
        st.subheader("🔖 Cases Grouped by SR/Incident Number and Status")

        grouped_cases = filtered_data.groupby(['SR/Incident Number', 'Status']).agg({
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

        st.dataframe(
            grouped_cases,
            use_container_width=True
        )

        # Allow users to choose based on SR/Incident Number + Status
        grouped_cases['Display'] = grouped_cases['SR/Incident Number'] + " - " + grouped_cases['Status']
        selection_map = dict(zip(grouped_cases['Display'], zip(grouped_cases['SR/Incident Number'], grouped_cases['Status'])))
        selected_display = st.selectbox("Select SR/Incident to View Details", grouped_cases['Display'].unique())

        if selected_display:
            selected_number, selected_status_value = selection_map[selected_display]
            st.subheader(f"🧾 Detailed Cases for {selected_status_value} ({selected_number})")
            detailed_cases = filtered_data[
                (filtered_data['SR/Incident Number'] == selected_number) &
                (filtered_data['Status'] == selected_status_value)
            ]
            st.dataframe(detailed_cases, use_container_width=True)

# Run the app
if __name__ == "__main__":
    main()
