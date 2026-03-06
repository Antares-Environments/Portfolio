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
    """Fetches the README.md, checking both main and master branches."""
    branches = ['main', 'master']
    headers = get_github_headers()
    
    for branch in branches:
        url = f"https://raw.githubusercontent.com/{username}/{repo}/{branch}/README.md"
        try:
            response = requests.get(url, headers=headers, timeout=5)
            if response.status_code == 200:
                # Converts markdown to HTML with support for code blocks and tables
                return markdown.markdown(response.text, extensions=['fenced_code', 'tables'])
        except requests.exceptions.RequestException:
            pass # Silently fail and try the next branch

    # Fallback if it fails both branches
    return f"<h3>Documentation Unavailable</h3><p>Could not find README.md on 'main' or 'master' for <b>{repo}</b>. Ensure the repository is public and the file exists.</p>"

def find_repo_image(username, repo):
    """Scans the repository tree for a .png file to use as a thumbnail."""
    headers = get_github_headers()
    for branch in ['main', 'master']:
        tree_url = f"https://api.github.com/repos/{username}/{repo}/git/trees/{branch}?recursive=1"
        try:
            response = requests.get(tree_url, headers=headers, timeout=5)
            if response.status_code == 200:
                tree = response.json().get('tree', [])
                
                # Filter the tree for anything ending in .png
                png_files = [item['path'] for item in tree if item['path'].endswith('.png')]
                
                if png_files:
                    # Smart selection: prioritize files named logo, thumb, or cover
                    best_match = png_files[0]
                    for img in png_files:
                        img_lower = img.lower()
                        if 'logo' in img_lower or 'thumb' in img_lower or 'cover' in img_lower:
                            best_match = img
                            break
                    
                    return f"https://raw.githubusercontent.com/{username}/{repo}/{branch}/{best_match}"
        except Exception:
            pass 
            
    # Clean fallback if absolutely no .png files exist in the repo
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

def get_github_projects(username, repo_names):
    """Fetches repository data and dynamically locates image files."""
    projects = []
    headers = get_github_headers()
    
    for repo in repo_names:
        api_url = f"https://api.github.com/repos/{username}/{repo}"
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            
            # Triggers the new scanner to find a .png in the repo
            image_url = find_repo_image(username, repo)
            
            projects.append({
                'name': data['name'],
                'description': data['description'],
                'image_url': image_url,
                'html_content': fetch_readme_as_html(username, repo)
            })
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
                # Added 'org' key to the dictionary
                current_event = {'title': line[1:-1], 'org': '', 'description': [], 'cert_url': ''}
            elif current_event is not None:
                if line.startswith('CERT:'):
                    current_event['cert_url'] = line.replace('CERT:', '').strip()
                elif line.startswith('ORG:'):
                    # Captures the new organization tag
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
    
    # Automating fetching for Monarch-of-Florence repositories
    github_projects = get_github_projects("Monarch-of-Florence", ["welt-vx", "data-cellar"])
    
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