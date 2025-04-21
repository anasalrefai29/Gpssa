import streamlit as st
import pandas as pd
import re
import io
from datetime import datetime

st.set_page_config(layout="wide")
st.title("GPSSA Case Dashboard - Full Dataset")

uploaded_file = st.file_uploader("Upload Full Dataset CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    # Standardize column names
    df.columns = df.columns.str.strip()

    # Extract SR and Incident Numbers from Last Note
    def extract_reference(note):
        if pd.isna(note):
            return None
        match = re.search(r'(SR|Incident)\s*#?\s*(\d+)', note, re.IGNORECASE)
        return match.group(2) if match else None

    def extract_type(note):
        if pd.isna(note):
            return None
        if 'incident' in note.lower():
            return 'Incident'
        elif 'sr' in note.lower():
            return 'SR'
        return None

    df['Ref Number'] = df['Last Note'].apply(extract_reference)
    df['Ref Type'] = df['Last Note'].apply(extract_type)

    # Replace NaNs in user field
    df['Current User Id'] = df['Current User Id'].fillna('Unassigned')

    # Add DIT Team grouping
    dit_team = ['anas.hasan', 'fatima.bero', 'ali.babiker']
    df['User Group'] = df['Current User Id'].apply(lambda x: 'DIT Team' if x in dit_team else x)

    # Add status flags
    df['Status Group'] = df.apply(lambda row: 'Not Triaged' if pd.isna(row['Last Note']) or row['Last Note'].strip() == ''
                                   else ('Pending' if 'pending' in str(row['Process Status']).lower() else 'Other'), axis=1)

    # Sidebar Filters
    st.sidebar.header("Filters")

    selected_user = st.sidebar.selectbox("Filter by User or DIT Team", options=['All'] + sorted(df['User Group'].unique()))
    selected_status = st.sidebar.multiselect("Filter by Status", options=df['Status Group'].unique(), default=df['Status Group'].unique())
    selected_type = st.sidebar.multiselect("Type (Incident or SR)", options=['SR', 'Incident'], default=['SR', 'Incident'])

    search_value = st.sidebar.text_input("Search by Emirates ID, Mobile, or Note")

    # Apply filters
    filtered_df = df[df['Status Group'].isin(selected_status)]
    if selected_user != 'All':
        filtered_df = filtered_df[filtered_df['User Group'] == selected_user]
    if selected_type:
        filtered_df = filtered_df[filtered_df['Ref Type'].isin(selected_type)]
    if search_value:
        search_value = search_value.lower()
        filtered_df = filtered_df[filtered_df.apply(lambda row: search_value in str(row['Emirates ID']).lower()
                                                    or search_value in str(row['mobile Number']).lower()
                                                    or search_value in str(row['Last Note']).lower(), axis=1)]

    # Group by Ref Number
    grouped = filtered_df.groupby(['Ref Type', 'Ref Number'])

    st.subheader("Grouped Cases by SR/Incident")
    for (ref_type, ref_number), group in grouped:
        if pd.isna(ref_number):
            continue
        with st.expander(f"{ref_type} #{ref_number} - {len(group)} case(s)"):
            st.dataframe(group[['Case Id', 'Process Status', 'Category', 'Last Note', 'Current User Id']])

    # Show full filtered table
    st.subheader("Filtered Case List")
    st.dataframe(filtered_df)

    # Download filtered data
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Filtered Data as CSV", csv, "Filtered_Cases.csv", "text/csv")
