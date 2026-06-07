import os
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
import chromadb
from dotenv import load_dotenv

load_dotenv()
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from chromadb import HttpClient
from dotenv import load_dotenv

load_dotenv()

# Embedding model (local)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# Setup Chroma Client connecting to our docker container
chroma_client = chromadb.PersistentClient(path="./chroma_db")
vectorstore = Chroma(
    client=chroma_client,
    collection_name="pr_reviews",
    embedding_function=embeddings
)

# LLM setup - using Groq API
# The user needs to set GROQ_API_KEY in their environment/dotenv
llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.2,
    max_tokens=1024
)

review_prompt = PromptTemplate(
    input_variables=["context", "code_snippet"],
    template="""You are an expert code reviewer acting on behalf of the engineering team.
You are reviewing a new pull request. Use the team's historical review context and guidelines provided below to inform your review.

Historical Context / Guidelines:
{context}

Code Snippet to Review:
{code_snippet}

Please provide a structured code review highlighting any stylistic, architectural, or security issues based strictly on the provided context.
Output the review in JSON format with keys: 'file', 'line', 'type' (CRITICAL, WARNING, INFO), and 'message'.
"""
)

def generate_review(code_snippet: str, filename: str) -> str:
    """
    Retrieves context and generates a review.
    """
    # Truncate code snippet to fit within token limits (~2000 tokens)
    if len(code_snippet) > 8000:
        code_snippet = code_snippet[:8000] + "\n...[Diff Truncated]..."
        
    # 1. Retrieve relevant past comments/guidelines
    docs = vectorstore.similarity_search(code_snippet, k=2)
    context_text = "\n\n".join([doc.page_content for doc in docs])
    
    # Truncate context text to fit within token limits (~1000 tokens)
    if len(context_text) > 4000:
        context_text = context_text[:4000] + "\n...[Context Truncated]..."
    
    # 2. Generate review
    chain = review_prompt | llm
    response = chain.invoke({"context": context_text, "code_snippet": code_snippet})
    content = response.content
    if isinstance(content, list):
        # Extract text from blocks if it's a list (newer langchain versions)
        content = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content])
    return str(content)

summary_prompt = PromptTemplate(
    input_variables=["diff_text"],
    template="""You are an expert software engineer.
Below is the unified diff of all files changed in a new pull request.
Please provide a concise, high-level summary of the overall changes introduced by this pull request.
Focus on the 'what' and 'why' rather than listing every single line change.

Diff:
{diff_text}

Summary:
"""
)

def generate_summary(diff_text: str) -> str:
    """
    Generates a high-level summary of the entire PR based on all diffs.
    """
    # Truncate total diff text to fit within token limits (~3000 tokens)
    if len(diff_text) > 12000:
        diff_text = diff_text[:12000] + "\n...[Diff Truncated]..."
        
    chain = summary_prompt | llm
    response = chain.invoke({"diff_text": diff_text})
    content = response.content
    if isinstance(content, list):
        content = "".join([block.get("text", "") if isinstance(block, dict) else str(block) for block in content])
    return str(content)

def ingest_document(text: str, metadata: dict):
    """
    Helper to chunk and ingest a document/PR comment into the vector store.
    """
    # For a real implementation, we'd chunk this using LangChain's RecursiveCharacterTextSplitter.
    # We will expand on this when setting up the ingestion pipeline.
    vectorstore.add_texts(texts=[text], metadatas=[metadata])

def get_all_memory():
    """
    Returns all documents currently stored in the RAG vector store.
    """
    # vectorstore.get() fetches all stored documents from the collection
    data = vectorstore.get()
    
    memories = []
    if data and "documents" in data and "metadatas" in data:
        for idx in range(len(data["documents"])):
            memories.append({
                "id": data["ids"][idx] if "ids" in data else str(idx),
                "document": data["documents"][idx],
                "metadata": data["metadatas"][idx]
            })
            
    return memories
