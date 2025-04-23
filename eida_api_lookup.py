import streamlit as st
import requests
import json

st.set_page_config(page_title="EIDA API Lookup", layout="centered")

st.title("🔍 EIDA Personal Info Lookup")

# Input field for Emirates ID
emirates_id = st.text_input("Enter Emirates ID", max_chars=15, help="Enter full Emirates ID without spaces")

# Submit button
if st.button("Get Info"):
    if not emirates_id:
        st.warning("Please enter a valid Emirates ID.")
    else:
        # API setup
        url = f"http://172.23.12.77:7575/api/gsb/eida/get-personal-info/{emirates_id}"
        headers = {
            "username": "user1",
            "password": "password123"
        }

        try:
            with st.spinner("Fetching data from EIDA API..."):
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()

                st.success("✅ Data retrieved successfully!")
                st.json(data)

        except requests.exceptions.ConnectTimeout:
            st.error("⏱️ Connection timed out. Make sure you're connected to the internal network or VPN.")
        except requests.exceptions.ConnectionError:
            st.error("🚫 Could not connect to the server. Please check the network or IP address.")
        except requests.exceptions.HTTPError as e:
            st.error(f"❌ HTTP error occurred: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")
