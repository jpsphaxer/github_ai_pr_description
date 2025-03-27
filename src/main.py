import os
import requests
from openai import OpenAI
from github import Github

def main():
    github_token = os.environ['GITHUB_TOKEN']
    openai_key = os.environ['OPENAI_API_KEY']
    template_path = os.environ.get('PR_TEMPLATE_PATH', '.github/pull_request_template.md')
    
    g = Github(github_token)
    openai = OpenAI(api_key=openai_key)
    
    event_path = os.getenv('GITHUB_EVENT_PATH')
    with open(event_path) as f:
        event_data = json.load(f)
    
    repo_name = event_data['repository']['full_name']
    pr_number = event_data['number']
    
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    diff_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    diff_response = requests.get(diff_url, headers=headers)
    diff = diff_response.text
    
    try:
        template_file = repo.get_contents(template_path)
        template = template_file.decoded_content.decode()
    except Exception as e:
        print(f"Warning: Could not find PR template at {template_path}")
        template = ""
    
    prompt = f"""You're a helpful assistant for writing excellent pull request descriptions. 
    Here's the diff for this PR:
    {diff}
    
    The repository has this PR template:
    {template}
    
    Please:
    1. Summarize the key changes in this PR
    2. Explain the motivation behind these changes
    3. Suggest a well-structured PR description following the template format
    4. Ask any clarifying questions if needed to improve the description"""
    
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    ai_response = response.choices[0].message.content
    
    pr.create_issue_comment(
        f"🤖 AI PR Description Assistant (Python):\n\n{ai_response}\n\n"
        "Please edit this description or reply with any additional information."
    )

if __name__ == "__main__":
    main()