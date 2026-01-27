"""Streamlit UI for resume screening."""

import httpx
import streamlit as st

API_URL = "http://localhost:8000"

st.title("ScreenGPT")

uploaded_file = st.file_uploader("Upload a resume (PDF)", type="pdf")

if uploaded_file is not None:
    st.write("File uploaded successfully!", uploaded_file.name)

    if st.button("Process Resume"):
        with st.spinner(
            "Processing resume through 8-agent pipeline (this may take a few minutes)..."
        ):
            try:
                with httpx.Client(timeout=180.0) as client:
                    response = client.post(
                        f"{API_URL}/screening/",
                        files={"resume": (uploaded_file.name, uploaded_file, "application/pdf")},
                    )

                if response.status_code == 200:
                    st.success("Resume processed successfully!")
                    data = response.json()

                    recommendation = data.get("recommendation", "Unknown")
                    if recommendation in ["Strong Hire", "Hire"]:
                        st.success(f"**Recommendation:** {recommendation}")
                    elif recommendation == "Maybe":
                        st.warning(f"**Recommendation:** {recommendation}")
                    else:
                        st.error(f"**Recommendation:** {recommendation}")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Overall Score", f"{data.get('overall_score', 0):.1f}")
                    with col2:
                        st.metric("Skill Match", f"{data.get('skill_match_score', 0):.1f}")
                    with col3:
                        st.metric("Experience Fit", f"{data.get('experience_fit_score', 0):.1f}")

                    st.write("**Candidate:**", data.get("candidate_name", "Unknown"))
                    st.write("**Confidence:**", data.get("confidence", "Unknown"))
                    st.write("**Summary:**", data.get("summary", ""))

                    strengths = data.get("strengths", [])
                    if strengths:
                        st.write("**Strengths:**")
                        for s in strengths:
                            st.write(f"- {s}")

                    gaps = data.get("gaps", [])
                    if gaps:
                        st.write("**Gaps:**")
                        for g in gaps:
                            st.write(f"- {g}")

                    st.write("**Compliance:**", data.get("compliance_status", ""))

                    next_steps = data.get("next_steps", [])
                    if next_steps:
                        st.write("**Next Steps:**")
                        for step in next_steps:
                            st.write(f"- {step}")

                    with st.expander("Detailed Reasoning"):
                        st.write(data.get("reasoning", ""))

                else:
                    st.error(f"Error processing resume: {response.text}")

            except httpx.ConnectError:
                st.error("Could not connect to API. Is the backend running?")
            except httpx.TimeoutException:
                st.error("Request timed out. The server may be overloaded.")
            except Exception as e:
                st.error(f"Unexpected error: {e}")
