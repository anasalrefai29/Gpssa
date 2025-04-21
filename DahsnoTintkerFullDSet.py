import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="GPSSA Case Dashboard", layout="wide")

st.title("📊 GPSSA Case Dashboard")
st.caption("Devolved by **Anas H. Alrefai**")

uploaded_file = st.file_uploader("📂 Upload Full Dataset CSV File", type=["csv"])

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)

        # Clean column names
        df.columns = df.columns.str.strip()

        required_columns = ["Current User Id", "Process Status", "Case Id", "Request Type"]
        if not all(col in df.columns for col in required_columns):
            st.error("⚠️ Required columns not found. Please upload a valid file.")
        else:
            # Sidebar filters
            st.sidebar.header("Filters")

            users = sorted(df["Current User Id"].dropna().unique().tolist())
            user_filter = st.sidebar.selectbox("Select User", options=["All"] + users)

            type_filter = st.sidebar.selectbox("Select Type", options=["All", "Incident", "SR"])

            search_text = st.sidebar.text_input("🔍 Search (EID, Mobile, Case ID, etc.)")

            filtered_df = df.copy()

            if user_filter != "All":
                filtered_df = filtered_df[filtered_df["Current User Id"] == user_filter]

            if type_filter != "All":
                filtered_df = filtered_df[filtered_df["Request Type"].str.contains(type_filter, case=False, na=False)]

            if search_text:
                search_text = search_text.strip()
                mask = pd.Series(False, index=filtered_df.index)
                for col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.contains(search_text, case=False, na=False)
                filtered_df = filtered_df[mask]

            st.subheader("📋 Filtered Case Data")
            st.write(f"Showing **{len(filtered_df)}** cases")
            st.dataframe(filtered_df, use_container_width=True)

            # Download
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download Filtered Data as CSV",
                csv,
                "filtered_cases.csv",
                "text/csv",
                key="download-csv",
            )

            # Grouped summary
            grouped = filtered_df.groupby(["Request Type", "Process Status"]).size().reset_index(name="Count")
            st.subheader("📈 Request Type and Status Breakdown")
            fig = px.bar(grouped, x="Request Type", y="Count", color="Process Status", barmode="group", text="Count")
            st.plotly_chart(fig, use_container_width=True)

    except Exception as e:
        st.error(f"❌ Error loading file: {e}")
else:
    st.warning("📌 Please upload a CSV file to begin.")
