import streamlit as st
from analyzer import analyze_resume

st.set_page_config(
    page_title="Smart ARS | Resume Screener",
    page_icon="📄",
    layout="wide",
)

# Sidebar Configuration
with st.sidebar:
    st.title("Settings")
    api_key = st.text_input("Gemini API Key", type="password", help="Get a free key from Google AI Studio")
    output_lang = st.selectbox("Report Language / زبان گزارش", ["Persian", "English"])
    st.markdown("---")
    st.caption("Supports both Persian & English PDF resumes.")

# Apply RTL styling when Persian is selected for the report
is_rtl = output_lang == "Persian"
direction = "rtl" if is_rtl else "ltr"
align = "right" if is_rtl else "left"

st.markdown(
    f"""
    <style>
        .report-box {{
            direction: {direction};
            text-align: {align};
            padding: 1.2rem;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            background-color: #fafafa;
            color: #1f1f1f;
            margin-bottom: 1rem;
        }}
        .report-box h4 {{
            margin-top: 0;
            color: #111111;
        }}
    </style>
    """,
    unsafe_allow_html=True,
)

# Main Header
st.title("Smart ARS — Automated Resume Screening")
st.write("Upload a candidate's resume (PDF) and paste the Job Description to get an instant structured evaluation.")

# Input Columns
col1, col2 = st.columns([1.2, 1])

with col1:
    job_description = st.text_area(
        "Job Description (شرح شغل)",
        height=260,
        placeholder="Paste the job requirements, responsibilities, and desired skills here...",
    )

with col2:
    uploaded_file = st.file_uploader("Candidate Resume (PDF)", type=["pdf"])
    st.markdown("<br>", unsafe_allow_html=True)
    analyze_btn = st.button("Analyze Resume", type="primary", use_container_width=True)

# Execution & Results
if analyze_btn:
    if not api_key:
        st.error("Please enter your Gemini API Key in the sidebar.")
    elif not job_description.strip():
        st.warning("Please enter a Job Description.")
    elif not uploaded_file:
        st.warning("Please upload a PDF resume.")
    else:
        with st.spinner("Analyzing resume against job description..."):
            try:
                pdf_bytes = uploaded_file.read()
                result = analyze_resume(api_key, pdf_bytes, job_description, output_lang)

                st.markdown("---")

                # Top Metrics
                m1, m2 = st.columns([1, 2])
                with m1:
                    st.metric(label="Match Score", value=f"{result.match_score}%")
                    st.progress(result.match_score / 100)
                with m2:
                    st.markdown(
                        f"""
                        <div class="report-box">
                            <h4>{result.verdict}</h4>
                            <p>{result.summary}</p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Skills Breakdown
                s1, s2 = st.columns(2)
                matched_html = "".join(f"<li>{skill}</li>" for skill in result.matched_skills)
                missing_html = "".join(f"<li>{skill}</li>" for skill in result.missing_skills)

                with s1:
                    title_matched = "مهارت‌های منطبق" if is_rtl else "Matched Skills"
                    st.markdown(
                        f"""
                        <div class="report-box">
                            <h4>✅ {title_matched}</h4>
                            <ul>{matched_html}</ul>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with s2:
                    title_missing = "مهارت‌های مورد نیاز (کمبودها)" if is_rtl else "Missing Skills / Gaps"
                    st.markdown(
                        f"""
                        <div class="report-box">
                            <h4>⚠️ {title_missing}</h4>
                            <ul>{missing_html}</ul>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Interview Questions
                questions_html = "".join(f"<li>{q}</li>" for q in result.interview_questions)
                title_q = "سوالات پیشنهادی برای مصاحبه" if is_rtl else "Suggested Interview Questions"
                st.markdown(
                    f"""
                    <div class="report-box">
                        <h4>💬 {title_q}</h4>
                        <ol>{questions_html}</ol>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")