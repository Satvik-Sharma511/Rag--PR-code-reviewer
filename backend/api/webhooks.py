from fastapi import APIRouter, Request, BackgroundTasks
import json
from api.routers import analyze_pr, PRRequest
from services.github_service import post_pr_comment

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])

async def process_pr_and_comment(pr_url: str):
    """
    Background task to run the RAG analyzer and post the comment back to GitHub.
    """
    try:
        print(f"Starting automated PR review for {pr_url}...")
        # Re-use the existing analysis endpoint logic
        request = PRRequest(pr_url=pr_url)
        response = await analyze_pr(request)
        
        # Format the response into a nice markdown comment
        comment_body = f"## 🤖 RAG-Powered Code Review\n\n"
        
        if response.summary:
            comment_body += f"### 💡 PR Summary\n{response.summary}\n\n---\n\n"
            
        comment_body += "### 🔍 Automated Feedback\n\n"
        
        if not response.reviews:
            comment_body += "No critical or architectural issues found based on historical standards. Looks good! 🎉\n"
        else:
            for review in response.reviews:
                # Use emoji based on type
                emoji = "🔴" if review.type == "CRITICAL" else "🟡" if review.type == "WARNING" else "🔵"
                comment_body += f"- {emoji} **{review.file}** (Line {review.line}): {review.message}\n"
                
        # Post the comment
        post_pr_comment(pr_url, comment_body)
        print(f"Successfully posted automated review to {pr_url}")
        
    except Exception as e:
        print(f"Automated PR review failed for {pr_url}: {e}")

@router.post("/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives GitHub webhook events.
    """
    payload = await request.json()
    
    # We only care about pull request events
    if "pull_request" in payload:
        action = payload.get("action")
        # Trigger review when PR is opened or synchronized (new commits pushed)
        if action in ["opened", "synchronize"]:
            pr_url = payload["pull_request"]["html_url"]
            print(f"Received GitHub webhook for PR: {pr_url} (Action: {action})")
            
            # Run the heavy LLM analysis in the background so GitHub doesn't timeout the webhook
            background_tasks.add_task(process_pr_and_comment, pr_url)
            
            return {"status": "success", "message": f"PR {action} event received. Review queued."}
            
    return {"status": "ignored", "message": "Event ignored."}
