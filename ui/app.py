"""Streamlit UI for resume screening."""

import httpx
import streamlit as st

API_URL = "http://localhost:8000"

st.title("ScreenGPT")

uploaded_file = st.file_uploader("Upload a resume (PDF)", type="pdf")

if uploaded_file is not None:
    st.write("File uploaded successfully!", uploaded_file.name)

    if st.button("Process Resume"):
        with st.spinner("Processing resume..."):
            try:
                with httpx.Client(timeout=60.0) as client:
                    response = client.post(
                        f"{API_URL}/screening/",
                        files={"resume": (uploaded_file.name, uploaded_file, "application/pdf")},
                    )

                if response.status_code == 200:
                    st.success("Resume processed successfully!")
                    response_data = response.json()

                    status = response_data.get("candidate_status")
                    if status == "Selected":
                        st.success(f"**Status:** {status}")
                    else:
                        st.error(f"**Status:** {status}")

                    st.write("**Feedback:**", response_data.get("reason"))
                    st.write(
                        "**Skills Matched:**",
                        f"{response_data.get('skill_match_percentage')}%",
                    )

                    matched_skills = response_data.get("matched_skills", [])
                    if matched_skills:
                        st.write("**Matched Skills:**", ", ".join(matched_skills))

                else:
                    st.error(f"Error processing resume: {response.text}")

            except httpx.ConnectError:
                st.error("Could not connect to API. Is the backend running?")
            except httpx.TimeoutException:
                st.error("Request timed out. The server may be overloaded.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
