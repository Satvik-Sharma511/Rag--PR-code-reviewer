import os
from github import Github
from github import Auth
from urllib.parse import urlparse

def get_github_client():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
    auth = Auth.Token(token)
    return Github(auth=auth)

def parse_pr_url(pr_url: str):
    """
    Parses a GitHub PR URL to extract the repo owner, repo name, and PR number.
    Example: https://github.com/owner/repo/pull/123
    Returns: (owner/repo, pr_number)
    """
    try:
        parsed = urlparse(pr_url)
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 4 and parts[2] == "pull":
            repo_full_name = f"{parts[0]}/{parts[1]}"
            pr_number = int(parts[3])
            return repo_full_name, pr_number
        raise ValueError("Invalid PR URL format")
    except Exception as e:
        raise ValueError(f"Could not parse GitHub PR URL: {e}")

def fetch_pr_files(pr_url: str, max_files=3):
    """
    Fetches the files changed in a PR, up to max_files.
    Returns a list of dicts with file metadata, diff patch, and contents.
    """
    g = get_github_client()
    repo_name, pr_number = parse_pr_url(pr_url)
    
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    files = pr.get_files()
    
    file_data = []
    for idx, f in enumerate(files):
        if max_files is not None and idx >= max_files:
            break
            
        original_code = ""
        modified_code = ""
        
        # Fetch original code from the base branch (if not a new file)
        if f.status != "added":
            try:
                base_content = repo.get_contents(f.filename, ref=pr.base.sha)
                original_code = base_content.decoded_content.decode("utf-8")
            except Exception as e:
                print(f"Could not fetch base content for {f.filename}: {e}")
                
        # Fetch modified code from the head branch (if not a deleted file)
        if f.status != "removed":
            try:
                head_content = repo.get_contents(f.filename, ref=pr.head.sha)
                modified_code = head_content.decoded_content.decode("utf-8")
            except Exception as e:
                print(f"Could not fetch head content for {f.filename}: {e}")
                
        file_info = {
            "filename": f.filename,
            "status": f.status,
            "additions": f.additions,
            "deletions": f.deletions,
            "patch": f.patch, # This contains the unified diff snippet
            "original_code": original_code,
            "modified_code": modified_code
        }
        file_data.append(file_info)
        
    return file_data

def fetch_historical_pr_comments(repo_full_name: str, limit: int = 10):
    """
    Fetches the most recent review comments from the repository directly.
    Returns a list of dictionaries containing the comment body, diff hunk, and PR info.
    """
    g = get_github_client()
    repo = g.get_repo(repo_full_name)
    
    # Get the most recent review comments across the entire repository
    comments = repo.get_pulls_review_comments(sort='updated', direction='desc')
    
    extracted_comments = []
    count = 0
    
    for comment in comments:
        if count >= limit:
            break
            
        # We skip empty comments or comments without a diff hunk
        if not comment.body or not comment.diff_hunk:
            continue
            
        extracted_comments.append({
            "pr_number": int(comment.pull_request_url.split('/')[-1]),
            "pr_url": comment.html_url,
            "file_path": comment.path,
            "diff_hunk": comment.diff_hunk,
            "comment_body": comment.body,
            "author": comment.user.login if comment.user else "Unknown"
        })
        count += 1
        
    return extracted_comments

def post_pr_comment(pr_url: str, comment_body: str):
    """
    Posts a general issue comment to the given PR.
    """
    g = get_github_client()
    repo_name, pr_number = parse_pr_url(pr_url)
    
    repo = g.get_repo(repo_name)
    pr = repo.get_issue(pr_number) # We use get_issue here because PR general comments use the Issues API
    
    pr.create_comment(comment_body)
    return True
