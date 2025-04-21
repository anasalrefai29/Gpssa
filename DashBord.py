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

# File selection function - fixed version
def select_file():
    """Open a file dialog to select the CSV file"""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the root window
        root.wm_attributes('-topmost', 1)  # Bring dialog to front
        filename = filedialog.askopenfilename(
            title="Select GPSSA CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=os.path.expanduser("~")  # Start at user home directory
        )
        root.destroy()  # Clean up the Tkinter instance
        return filename
    except Exception as e:
        st.error(f"Could not open file dialog: {str(e)}")
        return None

# Function to detect file encoding
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

# Load data function with robust file handling
@st.cache_data
def load_data(file_path):
    """Load and preprocess the GPSSA case data"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    # Detect file encoding
    try:
        detected_encoding = detect_encoding(file_path)
    except Exception as e:
        detected_encoding = 'utf-8-sig'  # Fallback to UTF-8 with BOM
    
    # Try loading with detected encoding first
    try:
        df = pd.read_csv(file_path, encoding=detected_encoding)
    except Exception as e:
        # Try multiple encodings to handle different file formats
        encodings = ['utf-8-sig', 'windows-1256', 'iso-8859-6', 'cp1256', 'utf-8']
        
        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                break
            except Exception:
                continue
        else:
            return None
    
    # Convert date columns with error handling
    date_columns = ['Case Start Date', 'Last Note Date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
    
    # Remove rows with invalid dates
    df = df.dropna(subset=['Case Start Date'])
    
    # Clean up any empty strings that might have been read as NaN
    df = df.fillna('')
    
    # Ensure Last Note is treated as string and properly encoded
    if 'Last Note' in df.columns:
        df['Last Note'] = df['Last Note'].astype(str).apply(lambda x: x.encode('raw_unicode_escape').decode('utf-8', errors='replace'))
    
    return df

# Main App
def main():
    st.title("📊 GPSSA Case Management Dashboard")
    
    # Initialize session state for file path if it doesn't exist
    if 'file_path' not in st.session_state:
        st.session_state.file_path = None
    
    # Add attribution
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Developed by Anas H. Alrefai")
    
    # File selection in sidebar
    st.sidebar.header("📂 Data Source")
    file_option = st.sidebar.radio("Select data source:", 
                                 ["Use default file", "Select different file"])
    
    if file_option == "Use default file":
        # Try default locations
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
    
    # Load data
    if st.session_state.file_path:
        df = load_data(st.session_state.file_path)
    else:
        df = None
    
    if df is None:
        st.warning("Please select a valid CSV file to continue")
        return
    
    # Define users and add DIT-Team option
    target_users = ['anas.hasan', 'ali.babiker', 'mohammed.reda']
    all_users = ['DIT-Team'] + target_users

    # Improved categorization function with better pattern matching
    def categorize_case(note):
        """Categorize cases based on notes to identify SR/Incident numbers"""
        if pd.isna(note) or str(note).strip() == '':
            return 'Not Triaged'
        
        note = str(note).lower()
        
        # Patterns to match SR/Incident numbers in English and Arabic
        patterns = [
            (r'(sr|service request|اس ار|طلب خدمة)\s*[:#]?\s*(\d{4,5})', 'SR'),
            (r'(inc|incident|انسدنت|حالة)\s*[:#]?\s*(\d{4,5})', 'Incident'),
            (r'\b(1[45]\d{3})\b', 'SR'),  # SR numbers starting with 14 or 15
            (r'\b(2[12]\d{3})\b', 'Incident'),  # Incident numbers starting with 21 or 22
            (r'(tkt|ticket|تيكت)\s*[_:]?\s*(\d{4,5})', 'Incident')  # Ticket numbers like Tkt_21905 or Tkt 21905
        ]
        
        for pattern, prefix in patterns:
            matches = re.finditer(pattern, note)
            for match in matches:
                number = match.group(2) if len(match.groups()) > 1 else match.group(1)
                if prefix == 'SR' and (number.startswith('14') or number.startswith('15')):
                    return f'Pending SR {number}'
                elif prefix == 'Incident' and (number.startswith('21') or number.startswith('22')):
                    return f'Pending Incident {number}'
                elif prefix == 'Incident':  # For ticket numbers
                    return f'Pending Incident {number}'
        
        return 'Not Triaged'

    # Apply categorization and extract SR/Incident numbers
    df['Status'] = df['Last Note'].apply(categorize_case)
    df['SR/Incident Number'] = df['Status'].apply(lambda x: x.split()[-1] if x != 'Not Triaged' else '')

    # Filters in sidebar
    st.sidebar.header("🔍 Filters")

    # User filter
    selected_user = st.sidebar.selectbox("Select User", all_users, index=0)

    # Status filter with clear options
    status_options = ['All', 'Not Triaged', 'Pending SR/Incident']
    selected_status = st.sidebar.selectbox("Filter by Status", status_options, index=0)

    # Date range filter with improved date handling
    min_date = df['Case Start Date'].min().to_pydatetime().date()
    max_date = df['Case Start Date'].max().to_pydatetime().date()
    date_range = st.sidebar.date_input(
        "Date Range", 
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )

    # Apply filters
    if selected_user == 'DIT-Team':
        user_filtered = df[df['Current User Id'].isin(target_users)]
    else:
        user_filtered = df[df['Current User Id'] == selected_user]

    # Handle date range selection (user might not have selected both dates)
    if len(date_range) == 2:
        start_date, end_date = date_range
        date_filtered = user_filtered[
            (user_filtered['Case Start Date'].dt.date >= start_date) & 
            (user_filtered['Case Start Date'].dt.date <= end_date)
        ]
    else:
        date_filtered = user_filtered

    # Apply status filter
    if selected_status == 'Not Triaged':
        filtered_data = date_filtered[date_filtered['Status'] == 'Not Triaged']
    elif selected_status == 'Pending SR/Incident':
        filtered_data = date_filtered[date_filtered['Status'] != 'Not Triaged']
    else:
        filtered_data = date_filtered

    # Metrics row with improved formatting
    st.subheader(f"📈 Case Summary for {selected_user}")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Cases", len(filtered_data), help="Total cases matching your filters")
    with col2:
        pending = filtered_data[filtered_data['Status'] != 'Not Triaged']
        st.metric("Pending SR/Incident", len(pending), help="Cases with pending SR or Incident numbers")
    with col3:
        st.metric("Not Triaged", len(filtered_data) - len(pending), help="Cases without SR or Incident numbers")

    # Group cases by SR/Incident number if viewing pending cases
    if selected_status == 'Pending SR/Incident':
        st.subheader("🔖 Cases Grouped by SR/Incident Number")
        
        # Create grouped dataframe with more information
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
        }).sort_values('Number of Cases', ascending=False)
        
        # Reset index to make SR/Incident Number a column
        grouped_cases = grouped_cases.reset_index()
        
        # Display the grouped cases table with improved formatting
        st.dataframe(
            grouped_cases,
            use_container_width=True,
            column_config={
                "SR/Incident Number": st.column_config.TextColumn(
                    "SR/Incident #",
                    help="The service request or incident number"
                ),
                "Number of Cases": st.column_config.NumberColumn(
                    "Cases",
                    help="Number of cases linked to this SR/Incident"
                ),
                "Assigned To": st.column_config.TextColumn(
                    "Assigned To",
                    help="Users currently assigned these cases"
                ),
                "First Case Date": st.column_config.DateColumn(
                    "First Case",
                    help="Date of the earliest case in this group"
                ),
                "Categories": st.column_config.TextColumn(
                    "Categories",
                    help="Sub-categories of cases in this group"
                )
            }
        )
        
        # Allow selection of specific SR/Incident for detailed view
        selected_sr_incident = st.selectbox(
            "Select SR/Incident to view details:",
            [""] + grouped_cases["SR/Incident Number"].tolist()
        )
        
        # Show detailed cases for selected SR/Incident Number
        if selected_sr_incident and selected_sr_incident != "":
            st.subheader(f"📋 Cases for {selected_sr_incident}")
            detailed_cases = filtered_data[filtered_data['SR/Incident Number'] == selected_sr_incident]
            
            st.dataframe(
                detailed_cases[[
                    'Case Id', 
                    'Case Start Date', 
                    'Sub Category', 
                    'Status', 
                    'Current User Id',
                    'Last Note'
                ]].sort_values('Case Start Date', ascending=False),
                height=300,
                use_container_width=True,
                column_config={
                    "Case Id": "Case ID",
                    "Case Start Date": st.column_config.DateColumn("Start Date"),
                    "Sub Category": "Category",
                    "Status": "Status",
                    "Current User Id": "Assigned To",
                    "Last Note": st.column_config.TextColumn(
                        "Last Note",
                        help="Last note with Arabic text preserved"
                    )
                }
            )

    # Main case details table with improved display
    st.subheader("📋 Case Details")

    # Determine columns to display based on filters
    if selected_status == 'Pending SR/Incident':
        display_cols = ['Case Id', 'Case Start Date', 'Sub Category', 'Status', 'SR/Incident Number', 'Current User Id', 'Last Note']
    else:
        display_cols = ['Case Id', 'Case Start Date', 'Sub Category', 'Status', 'Current User Id', 'Last Note']

    # Display the data with improved formatting
    st.dataframe(
        filtered_data[display_cols].sort_values('Case Start Date', ascending=False),
        height=600,
        use_container_width=True,
        column_config={
            "Case Id": st.column_config.TextColumn("Case ID", width="small"),
            "Case Start Date": st.column_config.DateColumn("Start Date", width="small"),
            "Sub Category": st.column_config.TextColumn("Category", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
            "SR/Incident Number": st.column_config.TextColumn("SR/Incident #", width="small"),
            "Current User Id": st.column_config.TextColumn("Assigned To", width="medium"),
            "Last Note": st.column_config.TextColumn(
                "Last Note", 
                width="large",
                help="Last note with Arabic text preserved"
            )
        }
    )

    # Download button for filtered data
    csv = filtered_data.to_csv(index=False).encode('utf-8-sig')
    st.sidebar.download_button(
        "💾 Download Filtered Data",
        csv,
        f"gpssa_cases_{selected_user}_{datetime.now().strftime('%Y%m%d')}.csv",
        "text/csv",
        help="Download the currently filtered data as a CSV file"
    )

    # Add some helpful information in the sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ℹ️ Helpful Information")
    st.sidebar.markdown("""
    - **DIT-Team** shows all cases assigned to the target users
    - **Pending SR/Incident** shows cases with identified tracking numbers
    - **Not Triaged** shows cases needing review
    - Click column headers to sort tables
    """)

    # Add a refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Add debug information (can be removed in production)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🐞 Debug Info")
    st.sidebar.text(f"Working directory: {os.getcwd()}")
    st.sidebar.text(f"Python version: {os.sys.version}")

    # Add footer with attribution
    st.markdown("---")
    st.markdown("### Developed and maintained by Anas H. Alrefai")

if __name__ == "__main__":
    main()