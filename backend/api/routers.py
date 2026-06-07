from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from services.rag_service import generate_review, generate_summary, ingest_document, get_all_memory
import json
import time

router = APIRouter(prefix="/api/v1/reviews", tags=["Reviews"])

class PRRequest(BaseModel):
    pr_url: str

class ReviewItem(BaseModel):
    file: str
    line: int
    type: str
    message: str

class FileDiffItem(BaseModel):
    filename: str
    original_code: str
    modified_code: str

class AnalyzeResponse(BaseModel):
    summary: str = ""
    files: List[FileDiffItem]
    reviews: List[ReviewItem]

class IngestRequest(BaseModel):
    text: str
    source: str

from services.github_service import fetch_pr_files

@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_pr(request: PRRequest):
    """
    Fetches the PR diff via GitHub API, iterates over changed files,
    and generates reviews for each file snippet.
    """
    try:
        # Fetch files from the real PR (Capped at 3 to stay under Groq's strict 6k TPM limit)
        pr_files = fetch_pr_files(request.pr_url, max_files=6)
        
        all_reviews = []
        file_diffs = []
        full_diff_text = ""
        
        valid_files = [f for f in pr_files if f.get("patch")]
        
        for file in valid_files:
            # Accumulate the patch for the full PR summary
            full_diff_text += f"\n--- {file['filename']} ---\n{file['patch']}\n"
                
            # Add to file diffs for the frontend
            file_diffs.append(FileDiffItem(
                filename=file["filename"],
                original_code=file["original_code"],
                modified_code=file["modified_code"]
            ))

        for file in valid_files:
            review_json_str = generate_review(file["patch"], file["filename"])
            
            if review_json_str.startswith("```json"):
                review_json_str = review_json_str.replace("```json\n", "").replace("```", "").strip()
            elif review_json_str.startswith("```"):
                review_json_str = review_json_str.replace("```\n", "").replace("```", "").strip()
                
            try:
                review_data = json.loads(review_json_str)
                if isinstance(review_data, dict):
                    review_data = [review_data]
                    
                for item in review_data:
                    if "file" not in item or not item["file"]:
                        item["file"] = file["filename"]
                        
                all_reviews.extend(review_data)
            except json.JSONDecodeError:
                print(f"Failed to parse LLM output for {file['filename']}: {review_json_str}")
                
            # Add a 5 second delay to allow the Groq token bucket to replenish and avoid 413 Rate Limit errors
            time.sleep(5)

        # Generate the high-level PR summary
        pr_summary = generate_summary(full_diff_text) if full_diff_text else "No textual code changes found to summarize."

        return AnalyzeResponse(summary=pr_summary, files=file_diffs, reviews=all_reviews)

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate review: {str(e)}")

@router.get("/memory")
async def fetch_memory():
    """
    Returns all the documents currently stored in the ChromaDB RAG memory bank.
    """
    try:
        memories = get_all_memory()
        return {"status": "success", "count": len(memories), "data": memories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch memory: {str(e)}")

@router.post("/ingest")
async def ingest_guideline(request: IngestRequest):
    """
    Endpoint to ingest a team standard or historical PR comment into the vector store.
    """
    metadata = {"source": request.source}
    ingest_document(request.text, metadata)
    return {"status": "success", "message": f"Ingested content from {request.source}"}

class RepoIngestRequest(BaseModel):
    repo_url: str
    limit: int = 10

from services.ingestion_service import ingest_repo_history

@router.post("/ingest-history")
async def ingest_historical_prs(request: RepoIngestRequest):
    """
    Triggers the scraping of past PR comments from the provided GitHub repo URL
    and ingests them into the RAG vector store.
    """
    try:
        count = ingest_repo_history(request.repo_url, request.limit)
        return {"status": "success", "message": f"Successfully ingested {count} historical PR comments into ChromaDB."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest historical PRs: {str(e)}")
