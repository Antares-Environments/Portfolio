from flask import Flask, render_template
import os
import math
import requests
import markdown
import base64

app = Flask(__name__)

# --- PARSERS & HELPERS ---

def get_github_headers():
    """Fetches the GitHub token from environment variables to bypass rate limits."""
    token = os.environ.get('PORTFOLIO_API')
    if token:
        return {'Authorization': f'token {token}'}
    return {}

def fetch_readme_as_html(username, repo):
    """Fetches the README.md securely using the GitHub API."""
    url = f"https://api.github.com/repos/{username}/{repo}/readme"
    headers = get_github_headers()
    
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            # GitHub API returns base64 encoded content for the readme
            content = base64.b64decode(data['content']).decode('utf-8')
            return markdown.markdown(content, extensions=['fenced_code', 'tables'])
    except Exception:
        pass 

    # Clean fallback if it fails
    return f"<h3>Documentation Unavailable</h3><p>Could not find README.md for <b>{repo}</b>. Ensure the repository is initialized.</p>"

def find_repo_image(username, repo, default_branch="main"):
    """Scans the repository tree and strictly downloads the raw image bytes to bypass API limits and LFS pointers."""
    headers = get_github_headers()
    tree_url = f"https://api.github.com/repos/{username}/{repo}/git/trees/{default_branch}?recursive=1"
    
    try:
        response = requests.get(tree_url, headers=headers, timeout=5)
        if response.status_code == 200:
            tree = response.json().get('tree', [])
            png_files = [item['path'] for item in tree if item['path'].endswith('.png')]
            
            if png_files:
                best_match = png_files[0]
                for img in png_files:
                    img_lower = img.lower()
                    if 'logo' in img_lower or 'thumb' in img_lower or 'cover' in img_lower or 'icon' in img_lower:
                        best_match = img
                        break
                
                # Step 1: Ask the API for the file metadata
                blob_url = f"https://api.github.com/repos/{username}/{repo}/contents/{best_match}"
                blob_resp = requests.get(blob_url, headers=headers, timeout=5)
                
                if blob_resp.status_code == 200:
                    blob_data = blob_resp.json()
                    
                    # Step 2: Extract the direct download URL (handles LFS and large files)
                    download_url = blob_data.get('download_url')
                    
                    if download_url:
                        # Step 3: Download the raw image bytes and encode them
                        raw_img_resp = requests.get(download_url, headers=headers, timeout=5)
                        if raw_img_resp.status_code == 200:
                            img_base64 = base64.b64encode(raw_img_resp.content).decode('utf-8')
                            return f"data:image/png;base64,{img_base64}"
                            
    except Exception:
        pass 
            
    # Clean fallback
    return f"https://ui-avatars.com/api/?name={repo}&background=4CAF50&color=ffffff&size=250"

def parse_menu_file(filepath):
    """Parses the skillset custom schema txt file."""
    parsed_data = {}
    current_heading = None
    if not os.path.exists(filepath): return parsed_data
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line: continue
            if line.startswith('[') and line.endswith(']'):
                current_heading = line[1:-1]
                parsed_data[current_heading] = []
            elif current_heading is not None:
                parsed_data[current_heading].append(line)
    return parsed_data

def get_svg_path(start_angle, end_angle, cx=150, cy=150, r_in=70, r_out=130):
    """Calculates SVG path coordinates for the donut ring."""
    start_rad = math.radians(start_angle - 90)
    end_rad = math.radians(end_angle - 90)
    x1_out = cx + r_out * math.cos(start_rad)
    y1_out = cy + r_out * math.sin(start_rad)
    x2_out = cx + r_out * math.cos(end_rad)
    y2_out = cy + r_out * math.sin(end_rad)
    x1_in = cx + r_in * math.cos(end_rad)
    y1_in = cy + r_in * math.sin(end_rad)
    x2_in = cx + r_in * math.cos(start_rad)
    y2_in = cy + r_in * math.sin(start_rad)
    large_arc = 1 if (end_angle - start_angle) > 180 else 0
    return f"M {x1_out} {y1_out} A {r_out} {r_out} 0 {large_arc} 1 {x2_out} {y2_out} L {x1_in} {y1_in} A {r_in} {r_in} 0 {large_arc} 0 {x2_in} {y2_in} Z"

def generate_svg_segments(parsed_data, id_prefix):
    """Generates the geometry for the interactive rings."""
    categories = list(parsed_data.keys())
    num_slices = len(categories)
    segments = []
    if num_slices > 0:
        angle_per_slice = 360 / num_slices
        for i, category in enumerate(categories):
            start_angle = i * angle_per_slice
            end_angle = (i + 1) * angle_per_slice
            path_d = get_svg_path(start_angle + 1, end_angle - 1)
            segments.append({
                'id': f"{id_prefix}-{i + 1}",
                'label': category,
                'items': parsed_data[category],
                'path': path_d
            })
    return segments

def get_github_projects():
    """Fully automated dynamic fetch of all user repositories (public and private)."""
    headers = get_github_headers()
    username = "Antares-Environments" 
    
    # 1. Ask the token exactly who it belongs to
    if headers:
        try:
            user_resp = requests.get("https://api.github.com/user", headers=headers, timeout=5)
            if user_resp.status_code == 200:
                username = user_resp.json().get('login', username)
        except Exception:
            pass

    # 2. Fetch ALL repositories if token exists, otherwise fallback to public
    if headers:
        repos_url = "https://api.github.com/user/repos?visibility=all&affiliation=owner&sort=updated"
    else:
        repos_url = f"https://api.github.com/users/{username}/repos?type=owner&sort=updated"
        
    projects = []
    
    try:
        repo_resp = requests.get(repos_url, headers=headers, timeout=5)
        if repo_resp.status_code == 200:
            repos = repo_resp.json()
            
            # Filter out forks and limit to the 6 most recent to keep page load lightning fast
            repos = [r for r in repos if not r.get('fork')][:6]
            
            for repo in repos:
                repo_name = repo['name']
                default_branch = repo.get('default_branch', 'main')
                
                # Dynamically fetch the image and readme based on the actual default branch
                image_url = find_repo_image(username, repo_name, default_branch)
                html_content = fetch_readme_as_html(username, repo_name)
                
                projects.append({
                    'name': repo_name,
                    'description': repo.get('description') or "No description provided.",
                    'image_url': image_url,
                    'html_content': html_content
                })
    except Exception:
        pass
        
    return projects

def parse_events_file(filepath):
    """Parses the events text file for descriptions, organizations, and certificates."""
    events_data = []
    current_event = None
    if not os.path.exists(filepath): return events_data
    with open(filepath, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if not line: continue
            
            if line.startswith('[') and line.endswith(']'):
                if current_event: events_data.append(current_event)
                current_event = {'title': line[1:-1], 'org': '', 'description': [], 'cert_url': ''}
            elif current_event is not None:
                if line.startswith('CERT:'):
                    current_event['cert_url'] = line.replace('CERT:', '').strip()
                elif line.startswith('ORG:'):
                    current_event['org'] = line.replace('ORG:', '').strip()
                else:
                    current_event['description'].append(line)
                    
        if current_event: events_data.append(current_event)
    return events_data

def get_local_research():
    """Scans the static/research folder for Markdown files and matching PDFs."""
    folder_path = os.path.join('static', 'research')
    research_papers = []
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        return research_papers

    for filename in os.listdir(folder_path):
        if filename.endswith('.md'):
            base_name = filename[:-3] 
            md_path = os.path.join(folder_path, filename)
            pdf_filename = f"{base_name}.pdf"
            pdf_path = os.path.join(folder_path, pdf_filename)

            with open(md_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            html_content = markdown.markdown(raw_text, extensions=['fenced_code', 'tables'])
            has_pdf = os.path.exists(pdf_path)

            research_papers.append({
                'id': base_name,
                'html_content': html_content,
                'has_pdf': has_pdf,
                'pdf_file': f"research/{pdf_filename}" if has_pdf else None
            })
            
    return research_papers

# --- ROUTES ---

@app.route('/')
def home():
    skills_data = parse_menu_file('data/skills.txt')
    skill_segments = generate_svg_segments(skills_data, "skill")
    
    # Fully automated array generation using the token
    github_projects = get_github_projects()
    
    events_list = parse_events_file('data/events.txt')
    
    return render_template(
        'index.html', 
        skill_segments=skill_segments,
        projects=github_projects,
        events=events_list
    )

@app.route('/research')
def research():
    papers = get_local_research()
    return render_template('research.html', papers=papers)

if __name__ == '__main__':
    app.run(debug=True)