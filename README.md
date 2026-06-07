# 🤖 RAG-Powered AI Code Reviewer

*🚀 **Quick Start**: You can immediately use this AI on your own GitHub repositories by adding `https://satvik-spidy-rag.hf.space/api/v1/webhooks/github` to your repo's Webhooks!*

An intelligent, full-stack application that acts as an automated, expert code reviewer for your GitHub Pull Requests. It reads your code diffs, cross-references them against your team's historical review patterns and guidelines using **Retrieval-Augmented Generation (RAG)**, and provides actionable, line-by-line feedback.

---

## 🎯 The Motive
Traditional code reviews are time-consuming and prone to human error. Often, team-specific styling guidelines, security best practices, and architectural decisions are buried in old PR comments or fragmented documentation. 

This tool was built to solve that problem. By indexing your repository's historical PR comments and explicitly provided guidelines into a **Vector Database**, the AI acts as an institutional memory bank. Whenever a new PR is opened, it retrieves the most relevant past feedback and uses an LLM to automatically review the new code—ensuring consistency, saving senior engineers' time, and catching critical bugs before they are merged.

---

## 🛠️ Tech Stack

### Frontend (User Interface)
- **React & Vite**: Lightning-fast frontend development.
- **Vanilla CSS**: Custom-built, glassmorphism-inspired modern UI components.
- **Axios**: Handling asynchronous API requests.

### Backend (API & AI Logic)
- **FastAPI**: High-performance asynchronous Python web framework.
- **LangChain**: Orchestrating the RAG pipeline and LLM prompts.
- **Groq API**: Blazing fast inference using `llama-3.1-8b-instant` for review generation.
- **ChromaDB**: Local vector database for storing and retrieving historical context via embeddings.
- **Hugging Face Sentence Transformers**: Generating dense vector embeddings locally (`all-MiniLM-L6-v2`) without relying on paid APIs.
- **PyGithub**: Interfacing with the GitHub API to fetch PR diffs and metadata.

---

## 🔗 Adding to a GitHub Webhook

This application exposes a dedicated webhook endpoint so that it can automatically review code the moment a Pull Request is opened or updated on GitHub.

### Step-by-Step Setup
1. **Deploy the Backend**: Ensure your FastAPI backend is running on a public URL (e.g., via Hugging Face Spaces, Railway, or ngrok/localtunnel for local testing).
2. **Navigate to GitHub Settings**: Go to your target GitHub repository, click **Settings**, and select **Webhooks** from the sidebar.
3. **Add Webhook**: Click the **Add webhook** button.
4. **Configure Payload URL**: Set the **Payload URL** to point to the backend's webhook endpoint:
   ```
   https://your-backend-url.com/api/v1/webhooks/github
   ```
5. **Content type**: Set this to `application/json`.
6. **Select Events**: Under "Which events would you like to trigger this webhook?", select **Let me select individual events**.
7. **Check Pull Requests**: Check the box for **Pull requests** (uncheck everything else).
8. **Save**: Click **Add webhook**.

Now, whenever a PR is created or updated, GitHub will automatically send a POST request to your backend, triggering the RAG AI to analyze the diff and generate a review instantly!