# 📧 Prompt-Driven Email Productivity Agent
An intelligent Streamlit-based Email Agent that processes a mock inbox, categorizes emails, extracts action items, drafts replies, and supports chat-based inbox interaction — fully driven by customizable prompts (“Prompt Brain”). This project fulfills all requirements of the assignment: *Development of a Prompt-Driven Email Productivity Agent*.

## 🚀 Features
- Email categorization (Important, Newsletter, Spam, To-Do)
- Automatic action-item extraction using LLM
- Auto-drafted replies with editable text
- Chat-based inbox interaction (summaries, tasks, reply help)
- Editable Prompt Brain (categorization, extraction, reply, chat prompts)
- High-priority filter
- Draft storage (never auto-sent)
- Draft Viewer (full draft history)
- JSON-backed persistent storage

## 📦 Project Structure
email-agent/
├── app.py
├── utils.py
├── inbox.json
├── prompts.json
├── saved_results.json
├── requirements.txt
└── README.md

shell
Copy code

## 🔧 Installation & Setup
### 1. Clone the repo
git clone https://github.com/kamalesh955/email-Agent.git
cd email-Agent

shell
Copy code
### 2. Install dependencies
pip install -r requirements.txt

graphql
Copy code
### 3. Set Google API key
**Windows:**
setx GOOGLE_API_KEY "YOUR_API_KEY"

makefile
Copy code
**Mac/Linux:**
export GOOGLE_API_KEY="YOUR_API_KEY"

shell
Copy code
### 4. Run the app
streamlit run app.py

markdown
Copy code

## 📥 Loading the Mock Inbox
The mock inbox is stored in `inbox.json` and contains 10–20 sample emails (meeting requests, newsletters, deadlines, invoices, project updates, etc.). If deleted, a new sample inbox is auto-generated.

## 🧠 Prompt Brain (Edit Prompts)
Prompt templates are stored in `prompts.json`. You can edit:
- Categorization Prompt
- Action Item Extraction Prompt
- Draft Reply Prompt
- Chat Prompt  
Changes are saved instantly and affect all future LLM behavior.

## ⚡ Ingestion Pipeline
Click **⚡ Run ingestion pipeline** to:
1. Load all emails  
2. Categorize using LLM  
3. Extract action items  
4. Save results into inbox.json  
5. Refresh UI  

## 🤖 Email Agent Actions
### ✔ Categorize  
Runs categorization prompt → updates inbox.json.
### ✔ Extract Action Items  
Runs extraction prompt → stores items.
### ✔ Draft Reply  
Generates reply → editable → saved to saved_results.json.
### ✔ Chat About Email  
Ask: summarize, tasks, urgency, reply help, or any question.

All results logged as `"analyses"` in saved_results.json.

## 📄 Draft Viewer
A full history of drafted replies is available under the Draft Viewer:
- Subject  
- Body  
- Metadata  
- Timestamp  
Drafts are **never sent**, only stored.

## 📊 Saved Results
App shows:
Saved Drafts: X
Saved Analyses: Y

markdown
Copy code
Drafts = reply drafts  
Analyses = categorize + extract + chat + pipeline logs

## 🎥 Demo Video Requirements
Your demo must show:
- Loading inbox
- Editing prompts
- Running ingestion pipeline
- Viewing results
- Chat with Email Agent
- Draft reply creation
- High-priority filter

## ✔ Evaluation Criteria Mapping
| Requirement | Status |
|------------|--------|
| Inbox ingestion | ✔ |
| Prompt-driven architecture | ✔ |
| Categorization | ✔ |
| Action extraction | ✔ |
| Draft generation | ✔ |
| Chat agent | ✔ |
| Prompt editor | ✔ |
| UI design | ✔ |
| Error handling | ✔ |
| Drafts stored (not sent) | ✔ |
| Mock inbox (10–20 emails) | ✔ |
| Code quality & separation | ✔ |
| Deployment | ✔ |

## 📝 Author
**Kamalesh S**

## 🎉 Final Notes
This project fully implements the prompt-driven Email Productivity Agent with categorization, action extraction, 
