import streamlit as st
from compliance_lib import fetch_text, run_check, generate_report, RULES
import textwrap, json, datetime, os

st.set_page_config(page_title="anupalankarta – Compliance Checker",
                   layout="wide")

st.title("🛡️ anupalankarta (अनुपालंकर्ता) – unified compliance self-check")

# --- sidebar ---------------------------------------------------------------
with st.sidebar:
    st.header("📑 Input options")
    mode = st.radio("Choose data source:",
                    ("Paste text", "URL of public policy", "Upload file"))
    if mode == "Paste text":
        raw_text = st.text_area("Paste your policy / procedures here")
    elif mode == "URL of public policy":
        url = st.text_input("Public URL (HTTPS)")
        raw_text = fetch_text(url) if url else ""
    else:
        up = st.file_uploader("Upload .txt, .md or .pdf", type=["txt", "md", "pdf"])
        raw_text = up.read().decode("utf-8", errors="ignore") if up else ""

    st.markdown("---")
    selected_fw = st.multiselect(
        "Frameworks to check",
        list(RULES.keys()),
        default=list(RULES.keys())
    )
    run_btn = st.button("Run compliance check")

# --- main body --------------------------------------------------------------
if run_btn and raw_text.strip():
    with st.spinner("Running rule-based checks…"):
        results = run_check(raw_text)
    st.subheader("📊 Checklist results")
    for fw in selected_fw:
        passed = sum(1 for _, ok in results[fw] if ok)
        total = len(results[fw])
        st.write(f"**{fw}: {passed}/{total} items passed**")
        st.progress(passed / total)
        for label, ok in results[fw]:
            st.write(("✅" if ok else "❌") + "  " + label)
        st.markdown("---")

    # --- AI report section --------------------------------------------------
    st.subheader("📝 Generate narrative report")
    if st.button("Generate AI report via Hugging Face model"):
        with st.spinner("Calling model… this may take ~30 s"):
            bullet = "\n".join(
                f"- {fw}: {sum(ok for _, ok in results[fw])}/{len(results[fw])} passed"
                for fw in selected_fw
            )
            prompt = textwrap.dedent(f"""
                You are a compliance consultant. Summarize the following checklist
                outcomes and give prioritized next steps. Use clear headings, bullet
                points and be brief. Results:

                {bullet}

                Write the report for a technical audience.
            """)
            report = generate_report(prompt)
        st.markdown("#### Draft report")
        st.code(report, language="markdown")
        st.download_button("⬇️ Download .md",
                           report.encode("utf-8"),
                           file_name="anupalankarta_report.md",
                           mime="text/markdown")
else:
    st.info("Awaiting input…")
