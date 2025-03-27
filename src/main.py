import os
import json
import requests
from openai import OpenAI
from github import Github

def main():
    github_token = os.environ.get('GITHUB_TOKEN')
    if not github_token:
        raise ValueError("GITHUB_TOKEN environment variable is not set")
        
    openai_key = os.environ.get('OPENAI_API_KEY')
    if not openai_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
        
    template_path = os.environ.get('PR_TEMPLATE_PATH', '.github/pull_request_template.md')
    
    print(f"Using GitHub token: {'*' * 5 + github_token[-4:] if github_token else 'Not provided'}")
    print(f"Using OpenAI key: {'*' * 5 + openai_key[-4:] if openai_key else 'Not provided'}")
    print(f"Using template path: {template_path}")
    
    # Initialize GitHub client
    g = Github(github_token)
    openai = OpenAI(api_key=openai_key)
    
    # Get event data
    event_path = os.getenv('GITHUB_EVENT_PATH')
    if not event_path:
        raise ValueError("GITHUB_EVENT_PATH environment variable is not set")
        
    print(f"Reading event data from: {event_path}")
    with open(event_path) as f:
        event_data = json.load(f)
    
    repo_name = event_data['repository']['full_name']
    pr_number = event_data['pull_request']['number']
    
    print(f"Processing PR #{pr_number} in repository {repo_name}")
    
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    headers = {
        'Authorization': f'token {github_token}',
        'Accept': 'application/vnd.github.v3.diff'
    }
    diff_url = f"https://api.github.com/repos/{repo_name}/pulls/{pr_number}"
    diff_response = requests.get(diff_url, headers=headers)
    diff = diff_response.text
    
    template = ""
    try:
        template_file = repo.get_contents(template_path)
        template = template_file.decoded_content.decode()
        print(f"Successfully loaded PR template from {template_path}")
    except Exception as e:
        print(f"Warning: Could not find PR template at {template_path}: {e}")
    
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
    
    print("Sending request to OpenAI...")
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    ai_response = response.choices[0].message.content
    
    print("Adding comment to PR...")
    pr.create_issue_comment(
        f"🤖 AI PR Description Assistant:\n\n{ai_response}\n\n"
        "Please edit this description or reply with any additional information."
    )
    
    print("Successfully completed PR description generation")

if __name__ == "__main__":
    main()