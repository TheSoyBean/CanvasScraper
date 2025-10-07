import webbrowser
import requests
import sys
import os
from urllib.parse import urlparse, parse_qs


REDIRECT_URI = "http://localhost:8080/"

# Step 1: Get OAuth2 authorization code
def get_auth_code(canvas_base_url, client_id):
    auth_url = f"{canvas_base_url}/login/oauth2/auth?client_id={client_id}&response_type=code&redirect_uri={REDIRECT_URI}"
    print("Opening browser for Canvas login...")
    webbrowser.open(auth_url)
    print("After logging in, paste the full redirected URL here:")
    redirected_url = input("Redirected URL: ").strip()
    parsed = urlparse(redirected_url)
    code = parse_qs(parsed.query).get('code')
    if not code:
        print("Error: No code found in URL.")
        sys.exit(1)
    return code[0]

# Step 2: Exchange code for access token
def get_access_token(canvas_base_url, client_id, auth_code):
    token_url = f"{canvas_base_url}/login/oauth2/token"
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "code": auth_code
    }
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        print("Error getting access token:", response.text)
        sys.exit(1)
    return response.json()["access_token"]

if __name__ == "__main__":
    print("CanvasScraper CLI - Modules HTML Workflow")
    course_url = input("Paste your Canvas course/modules URL: ").strip()
    print(f"Course URL received: {course_url}")

    modules_html_path = input("Download the modules page as HTML, then enter the path to the HTML file: ").strip()
    if not os.path.exists(modules_html_path):
        print("Error: File not found.")
        sys.exit(1)

    # Parse modules HTML for assignment links
    from bs4 import BeautifulSoup
    with open(modules_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    # Find assignment links (simple example: look for <a> tags with 'assignments' in href)
    assignment_links = []
    for a in soup.find_all("a", href=True):
        if "assignments" in a["href"]:
            assignment_links.append(a["href"])

    print(f"Found {len(assignment_links)} assignment links.")
    # Next: Prompt user to upload each assignment HTML file
