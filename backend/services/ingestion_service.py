from services.github_service import fetch_historical_pr_comments
from services.rag_service import ingest_document

def ingest_repo_history(repo_url: str, limit: int = 10):
    """
    Scrapes the historical PR comments of a repository and ingests them into the RAG vector store.
    """
    # Clean the repo URL if the user pastes the full link (e.g. https://github.com/owner/repo)
    repo_full_name = repo_url.replace("https://github.com/", "").strip("/")
    
    comments = fetch_historical_pr_comments(repo_full_name, limit)
    
    ingested_count = 0
    for c in comments:
        # Create a rich text representation of the comment to serve as RAG context
        context_document = f"""
Historical Pull Request Comment
Repository: {repo_full_name}
PR: {c['pr_url']}
File: {c['file_path']}
Author: {c['author']}

Code Diff Hunk:
{c['diff_hunk']}

Reviewer Comment / Decision:
{c['comment_body']}
"""
        # Metadata to attach to the vector
        metadata = {
            "source": c['pr_url'],
            "type": "historical_pr_comment",
            "file": c['file_path']
        }
        
        # Ingest into ChromaDB
        ingest_document(context_document, metadata)
        ingested_count += 1
        
    return ingested_count
