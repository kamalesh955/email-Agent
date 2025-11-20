import streamlit as st
from utils import (
    load_json,
    save_json,
    call_llm,
    DEFAULT_PROMPTS,
    categorize_email,
    extract_actions,
    draft_reply,
    get_sample_inbox,
    run_ingestion_pipeline,
    collect_thread_context
)
import os
from datetime import datetime

# -------------------------
# Streamlit Page Config
# -------------------------
st.set_page_config(page_title="Email Productivity Agent", layout="wide")

# -------------------------
# Load or Initialize Data Files
# -------------------------
if not os.path.exists("prompts.json"):
    save_json("prompts.json", DEFAULT_PROMPTS)

if not os.path.exists("inbox.json"):
    save_json("inbox.json", get_sample_inbox())

if not os.path.exists("saved_results.json"):
    save_json("saved_results.json", {"drafts": [], "analyses": []})

prompts = load_json("prompts.json")
inbox = load_json("inbox.json")
results = load_json("saved_results.json")

# -------------------------
# Page Layout
# -------------------------
col1, col2, col3 = st.columns([2, 3, 2])


# ============================================================
# COLUMN 1 – INBOX VIEWER
# ============================================================
with col1:
    st.header("📬 Inbox")

    # Filter urgent/high-priority emails
    filter_urgent = st.checkbox("Show only emails with high priority", value=False)

    def inbox_label(i):
        e = inbox[i]
        tag = ""
        cat = e.get("category")

        if isinstance(cat, dict):
            if cat.get("priority"):
                tag = cat.get("priority")
            elif cat.get("labels"):
                tag = ", ".join(cat.get("labels")[:2])

        label_part = f" [{tag}]" if tag else ""
        return f"{e['from']} – {e['subject'][:40]} ({e['date']}){label_part}"

    indices = list(range(len(inbox)))

    # Apply filtering
    if filter_urgent:
        filtered = []
        for i in indices:
            email = inbox[i]
            cat = email.get("category")

            if isinstance(cat, dict):
                if cat.get("priority", "").lower() == "high":
                    filtered.append(i)
                elif "Important" in (cat.get("labels") or []):
                    filtered.append(i)
                elif "urgent" in email.get("subject", "").lower():
                    filtered.append(i)

        indices = filtered

    if not indices:
        st.info("No emails match the selected filter.")
        st.stop()

    selected_idx = st.selectbox(
        "Select an email",
        options=indices,
        format_func=inbox_label
    )

    email = inbox[selected_idx]
    st.subheader(email["subject"])
    st.write(f"From: **{email['from']}**")
    st.write(f"Date: {email['date']}")
    st.markdown("---")
    st.write(email["body"])

    st.markdown("---")
    if st.button("Archive email"):
        inbox[selected_idx]["archived"] = True
        save_json("inbox.json", inbox)
        st.success("Email archived.")
        st.rerun()


# ============================================================
# COLUMN 2 – AGENT ACTIONS
# ============================================================
with col2:
    st.header("🤖 Email Agent")

    st.markdown("Process your inbox with LLM-powered tools.")

    # --------------------------
    # INGESTION PIPELINE BUTTON
    # --------------------------
    if st.button("⚡ Run ingestion pipeline (categorize + extract actions for ALL emails)"):
        with st.spinner("Processing all emails..."):
            inbox, ingestion_results = run_ingestion_pipeline(
                inbox, prompts, temperature=0.2, max_output_tokens=300
            )
            save_json("inbox.json", inbox)

            for r in ingestion_results:
                results["analyses"].append({
                    "time": str(datetime.utcnow()),
                    "type": "ingest_batch",
                    "result": r
                })
            save_json("saved_results.json", results)

        st.success("Inbox ingestion completed.")
        st.rerun()

    st.markdown("---")

    # --------------------------
    # Actions on selected email
    # --------------------------
    st.subheader("Email Actions")
    action = st.radio(
        "Select an action:",
        ["Categorize", "Extract Action Items", "Draft Reply", "Chat About Email"]
    )

    prompt_key = {
        "Categorize": "categorize",
        "Extract Action Items": "extract_actions",
        "Draft Reply": "draft_reply",
        "Chat About Email": "chat"
    }[action]

    prompt_template = prompts[prompt_key]["template"]

    temperature = st.slider("Temperature", 0.0, 1.0, 0.2, 0.05)
    max_tokens = st.slider("Max Output Tokens", 64, 2048, 300, 32)

    # Handle Chat About Email separately (outside Run Action button)
    if action == "Chat About Email":
        st.subheader("Chat With Email")
        
        # Initialize chat input in session state
        if "chat_input" not in st.session_state:
            st.session_state.chat_input = ""

        user_question = st.text_input(
            "Ask a question about this email:",
            key="chat_question_input"
        )

        if st.button("Ask Question"):
            if not user_question.strip():
                st.warning("Please enter a question.")
            else:
                with st.spinner("Getting answer..."):
                    prompt = (
                        prompt_template
                        + "\n\nEMAIL CONTENT:\n" + email["body"]
                        + "\n\nUSER QUESTION:\n" + user_question
                    )

                    out = call_llm(prompt, temperature, max_tokens)

                    st.subheader("Agent Response")
                    st.write(out)

                    # Save result
                    results["analyses"].append({
                        "time": str(datetime.utcnow()),
                        "type": "chat",
                        "email_idx": selected_idx,
                        "question": user_question,
                        "output": out
                    })
                    save_json("saved_results.json", results)
    
    # Handle other actions with Run Action button
    else:
        if st.button("Run Action"):
            with st.spinner("Running LLM..."):
                if action == "Categorize":
                    out = categorize_email(email, prompt_template, temperature, max_tokens)

                    # Save category into inbox.json
                    inbox[selected_idx]["category"] = out
                    save_json("inbox.json", inbox)

                    results["analyses"].append({
                        "time": str(datetime.utcnow()),
                        "type": "categorize",
                        "email_idx": selected_idx,
                        "output": out
                    })
                    save_json("saved_results.json", results)

                    st.subheader("Category Result")
                    st.json(out)

                elif action == "Extract Action Items":
                    out = extract_actions(email, prompt_template, temperature, max_tokens)

                    inbox[selected_idx]["action_items"] = out
                    save_json("inbox.json", inbox)

                    results["analyses"].append({
                        "time": str(datetime.utcnow()),
                        "type": "extract_actions",
                        "email_idx": selected_idx,
                        "output": out
                    })
                    save_json("saved_results.json", results)

                    st.subheader("Action Items")
                    if isinstance(out, list):
                        for i, item in enumerate(out, 1):
                            st.write(f"{i}. {item}")
                    else:
                        st.write(out)

                elif action == "Draft Reply":
                    thread_context = collect_thread_context(inbox, email.get("thread_id"))
                    out = draft_reply(
                        email, prompt_template, temperature, max_tokens, thread_context=thread_context
                    )

                    st.subheader("Draft Reply")
                    draft_text = st.text_area("Draft:", value=out, height=200)

                    # Save metadata
                    draft_record = {
                        "time": str(datetime.utcnow()),
                        "email_idx": selected_idx,
                        "subject": f"Re: {email['subject']}",
                        "body": draft_text,
                        "metadata": {
                            "category": email.get("category"),
                            "action_items": email.get("action_items")
                        }
                    }
                    results["drafts"].append(draft_record)
                    save_json("saved_results.json", results)
                    st.success("Draft saved.")


# ============================================================
# COLUMN 3 – PROMPT EDITOR + RESULTS
# ============================================================
with col3:
    st.header("🧠 Prompt Brain")

    prompt_names = list(prompts.keys())
    chosen_prompt = st.selectbox("Select Prompt Template:", prompt_names)

    text = st.text_area("Edit prompt template:", prompts[chosen_prompt]["template"], height=200)

    if st.button("Save Prompt"):
        prompts[chosen_prompt]["template"] = text
        save_json("prompts.json", prompts)
        st.success("Prompt updated.")

    st.markdown("---")
    st.header("📊 Saved Results")

    if st.button("Reload Data"):
        st.rerun()

    st.write(f"Saved Drafts: {len(results.get('drafts', []))}")
    st.write(f"Saved Analyses: {len(results.get('analyses', []))}")