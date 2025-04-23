import requests
import streamlit as st

st.title("EIDA Personal Info Lookup")

eid = st.text_input("Enter Emirates ID (15 digits):")

if st.button("Lookup"):
    if eid and len(eid) == 15 and eid.isdigit():
        url = f"http://172.23.12.77:7575/api/gsb/eida/get-personal-info/{eid}"
        headers = {
            "username": "user1",
            "password": "password123",
            # Optional: Add content-type if needed
            # "Content-Type": "application/json"
        }

        try:
            with st.spinner("Contacting EIDA API..."):
                response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                st.success("Data Retrieved Successfully ✅")
                st.json(response.json())
            elif response.status_code == 401:
                st.error("Unauthorized: Check your credentials ❌")
            elif response.status_code == 404:
                st.warning("No data found for the provided Emirates ID.")
            else:
                st.error(f"Unexpected error: {response.status_code}")
        except requests.exceptions.ConnectTimeout:
            st.error("⏱ Connection timed out. The API server is reachable, but the service may not be running.")
        except requests.exceptions.ConnectionError:
            st.error("❌ Failed to connect. Service might be down or port 7575 is blocked.")
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
    else:
        st.warning("Please enter a valid 15-digit Emirates ID.")
