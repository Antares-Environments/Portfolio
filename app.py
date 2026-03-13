from flask import Flask, render_template
import os
import math
import requests
import markdown
import base64
import time

app = Flask(__name__)

_CACHE = {'projects': None, 'time': 0}

def get_github_headers():
    token = os.environ.get('PORTFOLIO_API')
    if token:
        return {'Authorization': f'token {token}'}
    return {}

def fetch_readme_as_html(username, repo):
    url = f"https://api.github.com/repos/{username}/{repo}/readme"
    headers = get_github_headers()
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            content = base64.b64decode(data['content']).decode('utf-8')
            return markdown.markdown(content, extensions=['fenced_code', 'tables'])
    except Exception:
        pass 
    return f"<h3>Documentation Unavailable</h3><p>Could not find README.md for <b>{repo}</b>. Ensure the repository is initialized.</p>"

def find_repo_image(username, repo, default_branch="main"):
    headers = get_github_headers()
    tree_url = f"https://api.github.com/repos/{username}/{repo}/git/trees/{default_branch}?recursive=1"
    
    valid_extensions = ('.png', '.jpg', '.jpeg', '.ico', '.webp')
    
    try:
        response = requests.get(tree_url, headers=headers, timeout=5)
        if response.status_code == 200:
            tree = response.json().get('tree', [])
            
            image_files = [item['path'] for item in tree if item['path'].lower().endswith(valid_extensions)]
            
            if image_files:
                best_match = image_files[0]
                for img in image_files:
                    img_lower = img.lower()
                    if any(x in img_lower for x in ['logo', 'thumb', 'cover', 'icon']):
                        best_match = img
                        break
                
                blob_url = f"https://api.github.com/repos/{username}/{repo}/contents/{best_match}"
                blob_resp = requests.get(blob_url, headers=headers, timeout=5)
                
                if blob_resp.status_code == 200:
                    blob_data = blob_resp.json()
                    download_url = blob_data.get('download_url')
                    
                    if download_url:
                        raw_img_resp = requests.get(download_url, timeout=5)
                        if raw_img_resp.status_code == 200:
                            ext = best_match.split('.')[-1].lower()
                            if ext == 'jpg': ext = 'jpeg'
                            elif ext == 'ico': ext = 'x-icon'
                            
                            img_base64 = base64.b64encode(raw_img_resp.content).decode('utf-8')
                            return f"data:image/{ext};base64,{img_base64}"
                            
    except Exception:
        pass 
            
    return f"https://ui-avatars.com/api/?name={repo}&background=4CAF50&color=ffffff&size=250"
    
def parse_menu_file(filepath):
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

def get_svg_path(start_angle, end_angle, cx=250, cy=250, r_in=140, r_out=230):
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
    global _CACHE
    if _CACHE['projects'] and (time.time() - _CACHE['time']) < 3600:
        return _CACHE['projects']
    headers = get_github_headers()
    username = "Antares-Environments" 
    if headers:
        try:
            user_resp = requests.get("https://api.github.com/user", headers=headers, timeout=5)
            if user_resp.status_code == 200:
                username = user_resp.json().get('login', username)
        except Exception:
            pass
    if headers:
        repos_url = "https://api.github.com/user/repos?visibility=all&affiliation=owner&sort=updated"
    else:
        repos_url = f"https://api.github.com/users/{username}/repos?type=owner&sort=updated"
    projects = []
    try:
        repo_resp = requests.get(repos_url, headers=headers, timeout=5)
        if repo_resp.status_code == 200:
            repos = repo_resp.json()
            repos = [r for r in repos if not r.get('fork')][:6]
            for repo in repos:
                repo_name = repo['name']
                default_branch = repo.get('default_branch', 'main')
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
    _CACHE['projects'] = projects
    _CACHE['time'] = time.time()
    return projects

def parse_events_file(filepath):
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

@app.route('/')
def home():
    skills_data = parse_menu_file('data/skills.txt')
    skill_segments = generate_svg_segments(skills_data, "skill")
    github_projects = get_github_projects()
    hackathon_list = parse_events_file('data/hackathons.txt')
    cert_list = parse_events_file('data/certifications.txt')
    return render_template(
        'index.html', 
        skill_segments=skill_segments,
        projects=github_projects,
        hackathons=hackathon_list,
        certs=cert_list
    )

@app.route('/research')
def research():
    papers = get_local_research()
    return render_template('research.html', papers=papers)

if __name__ == '__main__':
    app.run(debug=True)