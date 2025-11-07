import os
import requests
import re
from flask import request

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

VALID_EXTENSIONS = [".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".cpp", ".md"]

def extract_repo_info(url):
    match = re.match(r"https://github.com/([^/]+)/([^/]+)", url)
    if match:
        return match.group(1), match.group(2)
    return None, None

def fetch_file_list_recursive(owner, repo, path="", visited=None, depth=0, max_depth=10):
    if visited is None:
        visited = set()
    if path in visited or depth > max_depth:
        return []

    visited.add(path)
    api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    headers = {"Accept": "application/vnd.github.v3+json"}
    response = requests.get(api_url, headers=headers)

    if response.status_code != 200:
        print(f"[WARNING] Failed to fetch {path} — {response.status_code}")
        return []

    all_files = []
    for item in response.json():
        if item["type"] == "file":
            all_files.append(item)
        elif item["type"] == "dir":
            all_files.extend(fetch_file_list_recursive(owner, repo, item["path"], visited, depth + 1, max_depth))
    return all_files

def fetch_raw_content(file_info):
    if file_info.get("type") != "file":
        return None
    download_url = file_info.get("download_url")
    if not download_url:
        return None
    try:
        response = requests.get(download_url)
        return response.text
    except:
        return None

def generate_file_review(filename, content):
    prompt_text = f"""
You are a senior software reviewer.

Review the following file: `{filename}`

Code:
```{filename.split('.')[-1]}
{content}
```

Return a detailed review with:
1. Code quality (indentation, naming, logic)
2. Suggestions for improvement
3. Any potential bugs or issues
4. Overall file score out of 10
"""

    payload = {
        "contents": [
            {
                "parts": [
                    { "text": prompt_text }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            GEMINI_URL,
            headers={"Content-Type": "application/json"},
            json=payload
        )
        if response.status_code != 200:
            return f"Review failed: {response.status_code} - {response.text}"

        text = response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return text.strip()

    except Exception as e:
        return f"Review failed: {str(e)}"

def evaluate_github_project():
    body = request.json
    github_url = body.get("github_link")

    owner, repo = extract_repo_info(github_url)
    if not owner or not repo:
        return {"error": "Invalid GitHub link"}, 400

    files = fetch_file_list_recursive(owner, repo)
    reviews = []
    summary_comments = []
    total_score = 0
    count = 0

    for file in files:
        filename = file["path"]
        ext = "." + filename.split(".")[-1]
        if ext not in VALID_EXTENSIONS:
            continue
        content = fetch_raw_content(file)
        if not content or len(content) < 20:
            continue
        review = generate_file_review(filename, content)
        reviews.append({
            "file": filename,
            "review": review
        })
        score_match = re.search(r'score.*?(\d{1,2})\s*/?\s*10', review, re.IGNORECASE)
        if score_match:
            score = int(score_match.group(1))
            total_score += score
            count += 1
        summary_comments.append(review)

    final_score = round(total_score / count, 2) if count else 0

    return {
        "repo_url": github_url,
        "total_files_reviewed": len(reviews),
        "score": final_score,
        "comments": summary_comments[:3],
        "file_reviews": reviews
    }, 200
