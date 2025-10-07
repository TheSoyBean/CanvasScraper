import sys
import os
import csv
import json
import re
import time
from urllib.parse import urlparse
from bs4 import BeautifulSoup

try:
    import requests
except ImportError:
    print("Error: requests module not found. Install with: pip install requests")
    sys.exit(1)

def extract_course_name(soup):
    """Extract course name from HTML"""
    # Try title tag
    title = soup.find("title")
    if title:
        text = title.get_text()
        # Pattern: "Course Modules: Chinese 1" or "Assignments: Chinese 1"
        match = re.search(r'(?:Modules|Assignments|Grades):\s*(.+?)(?:\s*\||$)', text)
        if match:
            return match.group(1).strip()
    
    # Fallback: try page heading
    heading = soup.find("h1")
    if heading:
        return heading.get_text(strip=True)
    
    return "Unknown_Course"

def parse_assignments_list(html_path):
    """Parse assignments list page and extract assignment info"""
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    course_name = extract_course_name(soup)
    
    # Find main content area
    main_content = soup.find("div", id="not_right_side") or soup.find("div", class_="ic-app-main-content")
    if not main_content:
        main_content = soup
    
    assignments = []
    
    # Find assignment links
    for a in main_content.find_all("a", href=True):
        href = a["href"]
        if "/assignments/" in href and href.startswith("http"):
            parts = href.split("/assignments/")
            if len(parts) > 1 and parts[1]:
                id_part = parts[1].split("?")[0].split("#")[0].split("/")[0]
                if id_part.isdigit():
                    clean_url = href.split("?")[0].split("#")[0]
                    title = a.get_text(strip=True)
                    
                    # Try to find due date and points
                    due_date = ""
                    points = ""
                    parent = a.find_parent("div", class_="ig-row")
                    if parent:
                        details = parent.find("div", class_="ig-details")
                        if details:
                            detail_text = details.get_text()
                            # Extract due date
                            due_match = re.search(r'Due([^-]+)', detail_text)
                            if due_match:
                                due_date = due_match.group(1).strip()
                            # Extract points
                            points_match = re.search(r'([\d.]+)\s*pts', detail_text)
                            if points_match:
                                points = points_match.group(1)
                    
                    assignments.append({
                        "id": id_part,
                        "title": title,
                        "url": clean_url,
                        "due_date": due_date,
                        "points": points
                    })
    
    return course_name, assignments

def download_assignment_html(url, output_path, session=None):
    """Download assignment HTML page"""
    try:
        if session:
            response = session.get(url, timeout=30)
        else:
            response = requests.get(url, timeout=30)
        
        response.raise_for_status()
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        
        return True
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False

def parse_assignment_content(html_path):
    """Parse individual assignment HTML and extract content"""
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    content = {}
    
    # Extract title
    title_elem = soup.find("h1", class_="title")
    if title_elem:
        content["title"] = title_elem.get_text(strip=True)
    
    # Extract description/instructions
    description_elem = soup.find("div", class_="description")
    if description_elem:
        content["description"] = description_elem.get_text(strip=True)
    
    # Extract due date
    due_elem = soup.find("div", class_="due")
    if due_elem:
        content["due_date"] = due_elem.get_text(strip=True)
    
    # Extract points
    points_elem = soup.find("div", class_="points_possible")
    if points_elem:
        content["points_possible"] = points_elem.get_text(strip=True)
    
    # Extract submission types
    submission_elem = soup.find("div", class_="submission_types")
    if submission_elem:
        content["submission_types"] = submission_elem.get_text(strip=True)
    
    return content


if __name__ == "__main__":
    print("CanvasScraper - Canvas Course Content Downloader")
    print("=" * 50)
    print("\nInstructions:")
    print("1. Download your Canvas assignments/modules/grades page as HTML")
    print("2. Save it in the 'courses' directory")
    print("3. The script will extract all assignments and download them\n")
    
    courses_dir = os.path.join(os.path.dirname(__file__), "courses")
    if not os.path.exists(courses_dir):
        os.makedirs(courses_dir)
    
    # List HTML files in courses directory
    html_files = [f for f in os.listdir(courses_dir) 
                  if f.endswith('.html') and os.path.isfile(os.path.join(courses_dir, f)) 
                  and not f.startswith('assignment_')]
    
    if not html_files:
        print(f"Error: No HTML files found in '{courses_dir}' directory.")
        print("Please download the assignments/modules page as HTML.")
        sys.exit(1)
    
    if len(html_files) == 1:
        source_file = html_files[0]
        print(f"Found HTML file: {source_file}")
    else:
        print("Multiple HTML files found. Select the assignments/modules page:")
        for i, f in enumerate(html_files, 1):
            print(f"{i}. {f}")
        choice = int(input("Select file number: ")) - 1
        source_file = html_files[choice]
    
    source_path = os.path.join(courses_dir, source_file)
    
    # Parse assignments list
    print("\nParsing assignments list...")
    course_name, assignments = parse_assignments_list(source_path)
    
    # Create course-specific directory
    safe_course_name = re.sub(r'[^\w\s-]', '', course_name).strip().replace(' ', '_')
    course_dir = os.path.join(courses_dir, safe_course_name)
    if not os.path.exists(course_dir):
        os.makedirs(course_dir)
        print(f"Created course directory: {safe_course_name}/")
    
    # Move source file to course directory if not already there
    new_source_path = os.path.join(course_dir, source_file)
    if source_path != new_source_path:
        import shutil
        shutil.move(source_path, new_source_path)
        source_path = new_source_path
        print(f"Moved {source_file} to {safe_course_name}/")
    
    if not assignments:
        print("No assignments found in the HTML file.")
        sys.exit(0)
    
    print(f"Course: {course_name}")
    print(f"Found {len(assignments)} assignments")
    
    # Create assignments.csv in course directory
    csv_path = os.path.join(course_dir, "assignments.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "url", "due_date", "points"])
        writer.writeheader()
        writer.writerows(assignments)
    
    print(f"\n✓ Created {safe_course_name}/assignments.csv")
    
    # Check for existing assignment HTML files in course directory
    existing_assignments = [f for f in os.listdir(course_dir) 
                           if f.startswith('assignment_') and f.endswith('.html')]
    
    if existing_assignments:
        print(f"\nFound {len(existing_assignments)} existing assignment HTML files")
        choice = input("Parse existing files? (y/n): ").strip().lower()
        if choice == 'y':
            download_mode = False
        else:
            download_mode = True
    else:
        download_mode = True
    
    session = None
    if download_mode:
        # Ask if user wants to download assignments
        print("\nDo you want to download all assignment pages?")
        print("Note: This may require authentication for some Canvas sites.")
        choice = input("Download assignments? (y/n): ").strip().lower()
        
        if choice != 'y':
            print("Skipping download. You can manually download assignments and place them in 'courses' directory.")
            sys.exit(0)
        
        # Check if we can download (need authentication)
        print("\nFor authenticated Canvas sites, you can provide a session cookie:")
        print("(Open Canvas in browser, press F12, go to Application/Storage > Cookies)")
        print("Find '_legacy_normandy_session' or similar cookie and paste its value")
        cookie_value = input("Cookie value (or press Enter to try without): ").strip()
        
        session = requests.Session()
        if cookie_value:
            session.cookies.set("_legacy_normandy_session", cookie_value)
        
        # Set user agent to look like a browser
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    # Download or parse assignments
    course_content = {
        "course_name": course_name,
        "assignments": []
    }
    
    if download_mode:
        print(f"\nDownloading {len(assignments)} assignments...")
    else:
        print(f"\nParsing {len(existing_assignments)} existing assignment files...")
    
    for i, assignment in enumerate(assignments, 1):
        print(f"[{i}/{len(assignments)}] {assignment['title']}")
        
        # Download HTML if in download mode
        html_filename = f"assignment_{assignment['id']}.html"
        html_path = os.path.join(course_dir, html_filename)
        
        if download_mode:
            if os.path.exists(html_path):
                print(f"  ✓ Already exists: {html_filename}")
            else:
                success = download_assignment_html(assignment['url'], html_path, session)
                if success:
                    print(f"  ✓ Downloaded: {html_filename}")
                    time.sleep(1)  # Be polite to the server
                else:
                    print(f"  ✗ Failed to download")
                    continue
        
        # Parse content if file exists
        if os.path.exists(html_path):
            content = parse_assignment_content(html_path)
            content["id"] = assignment["id"]
            content["url"] = assignment["url"]
            if "title" not in content:
                content["title"] = assignment["title"]
            
            course_content["assignments"].append(content)
        else:
            print(f"  ⊘ File not found: {html_filename}")
    
    # Save to JSON in course directory
    json_filename = f"course_content.json"
    json_path = os.path.join(course_dir, json_filename)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(course_content, f, indent=2, ensure_ascii=False)
    
    print(f"\n✓ Created {safe_course_name}/course_content.json")
    print(f"\nDone! Processed {len(course_content['assignments'])} assignments.")
    print(f"All files saved in: courses/{safe_course_name}/")

