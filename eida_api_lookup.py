import streamlit as st
import requests

st.set_page_config(page_title="EIDA Personal Info Lookup", layout="centered")

st.title("🔍 EIDA Personal Info Lookup")

# Input fields
eid = st.text_input("Enter Emirates ID:", placeholder="784199463790875")
username = st.text_input("Username:", placeholder="user1")
password = st.text_input("Password:", type="password", placeholder="password123")

# API Base URL
BASE_URL = "http://172.23.12.77:7575/api/gsb/eida/get-personal-info/"

# Button to fetch data
if st.button("Fetch Info"):
    if not eid or not username or not password:
        st.warning("Please enter Emirates ID, username, and password.")
    else:
        full_url = f"{BASE_URL}{eid}"
        headers = {
            "username": username,
            "password": password
        }

        try:
            response = requests.get(full_url, headers=headers, timeout=10)

            if response.status_code == 200:
                st.success("✅ Info Retrieved Successfully")
                st.json(response.json())
            elif response.status_code == 401:
                st.error("❌ Unauthorized. Check your credentials.")
            elif response.status_code == 404:
                st.warning("⚠️ Record not found.")
            else:
                st.error(f"🚫 Error {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            st.error(f"Connection Error: {e}")
