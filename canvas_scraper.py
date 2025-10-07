import sys
import os
import csv
import json
import re
import time
import argparse
import shutil
from urllib.parse import urlparse
from bs4 import BeautifulSoup

try:
    import requests
except ImportError:
    print("Error: requests module not found. Install with: pip install requests")
    sys.exit(1)

def extract_course_name(soup, filename=None):
    """Extract course name from HTML"""
    # Try title tag first
    title = soup.find("title")
    if title:
        text = title.get_text().strip()
        
        # Skip JavaScript warning
        if "javascript" in text.lower():
            pass  # Fall through to other methods
        # Pattern: "Course Modules: Chinese 1" or "Assignments: Chinese 1"
        elif re.search(r'(?:Modules|Assignments|Grades):', text):
            match = re.search(r'(?:Modules|Assignments|Grades):\s*(.+?)(?:\s*\||$)', text)
            if match:
                return match.group(1).strip()
        # If title is clean and not too long, use it
        elif len(text) < 100 and text:
            return text
    
    # Try breadcrumbs navigation
    breadcrumbs = soup.find("nav", {"aria-label": "breadcrumbs"})
    if breadcrumbs:
        links = breadcrumbs.find_all("a")
        # Usually the course name is the second or third link
        for link in links[1:]:
            text = link.get_text(strip=True)
            if text and text.lower() not in ['dashboard', 'my dashboard', 'home']:
                return text
    
    # Try filename as fallback
    if filename:
        # Remove common patterns and extension
        name = filename.replace('.html', '')
        # Remove patterns like "Assignments_ " or "Course Modules_ "
        name = re.sub(r'^(Assignments?|Grades?|Modules?)[_:\s]+', '', name, flags=re.IGNORECASE)
        if name and len(name) > 3:
            return name
    
    # Last resort: try page heading (but skip JavaScript warnings)
    heading = soup.find("h1")
    if heading:
        text = heading.get_text(strip=True)
        if "javascript" not in text.lower() and len(text) < 100:
            return text
    
    return "Unknown_Course"

def parse_assignments_list(html_path):
    """Parse assignments list page and extract assignment info"""
    with open(html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    # Extract course name, passing filename as fallback
    filename = os.path.basename(html_path)
    course_name = extract_course_name(soup, filename)
    
    # Find main content area
    main_content = soup.find("div", id="not_right_side") or soup.find("div", class_="ic-app-main-content")
    if not main_content:
        main_content = soup
    
    assignments = []
    seen_urls = set()
    
    # Find assignment links - both direct assignments and module items
    for a in main_content.find_all("a", href=True):
        href = a["href"]
        
        # Handle direct assignment links
        if "/assignments/" in href and href.startswith("http"):
            parts = href.split("/assignments/")
            if len(parts) > 1 and parts[1]:
                id_part = parts[1].split("?")[0].split("#")[0].split("/")[0]
                if id_part.isdigit():
                    clean_url = href.split("?")[0].split("#")[0]
                    if clean_url in seen_urls:
                        continue
                    seen_urls.add(clean_url)
                    
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
        
        # Handle module item links (these redirect to assignments, pages, quizzes, etc.)
        elif "/modules/items/" in href or "/module_item_redirect/" in href:
            if not href.startswith("http"):
                continue
            
            clean_url = href.split("?")[0].split("#")[0]
            if clean_url in seen_urls:
                continue
            
            # Extract ID from module item URL
            item_parts = href.split("/modules/items/")
            if len(item_parts) < 2:
                item_parts = href.split("/module_item_redirect/")
            
            if len(item_parts) > 1:
                item_id = item_parts[1].split("?")[0].split("#")[0].split("/")[0]
                if item_id.isdigit():
                    seen_urls.add(clean_url)
                    title = a.get_text(strip=True)
                    
                    # Try to detect if it's an assignment/quiz (these should be downloaded)
                    # Skip pure content pages unless we can't tell
                    item_type = "unknown"
                    
                    # Check for type indicators in the link or parent
                    parent = a.find_parent("div", class_="context_module_item") or a.find_parent("li")
                    if parent:
                        # Check for icons
                        icon = parent.find("i", class_=True)
                        if icon:
                            classes = " ".join(icon.get("class", []))
                            if "icon-assignment" in classes or "icon-quiz" in classes:
                                item_type = "assignment"
                            elif "icon-document" in classes or "icon-page" in classes:
                                item_type = "page"
                    
                    # Include all module items (assignments, quizzes, pages, etc.)
                    # User can filter later if needed
                    assignments.append({
                        "id": f"module_{item_id}",
                        "title": title,
                        "url": clean_url,
                        "due_date": "",
                        "points": "",
                        "type": item_type
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
    
    # Extract title - try multiple selectors
    title_elem = soup.find("h1", class_="title") or soup.find("h1") or soup.find("h2", class_="page-title")
    if title_elem:
        content["title"] = title_elem.get_text(strip=True)
    
    # Extract description/instructions - try multiple selectors
    description_elem = (soup.find("div", class_="description") or 
                       soup.find("div", class_="user_content") or
                       soup.find("div", id="assignment_description"))
    if description_elem:
        # Get clean text without too much whitespace
        desc_text = description_elem.get_text(separator="\n", strip=True)
        # Limit description length to avoid huge JSON files
        content["description"] = desc_text[:2000] if len(desc_text) > 2000 else desc_text
    
    # Extract due date - multiple attempts
    due_elem = soup.find("div", class_="due") or soup.find("span", class_="due_date_display")
    if due_elem:
        content["due_date"] = due_elem.get_text(strip=True)
    else:
        # Try to find in table or other formats
        due_row = soup.find("tr", class_="due_date_display")
        if due_row:
            content["due_date"] = due_row.get_text(strip=True)
    
    # Extract points possible
    points_elem = (soup.find("div", class_="points_possible") or 
                   soup.find("span", class_="points_possible") or
                   soup.find("div", string=re.compile(r'Points?', re.I)))
    if points_elem:
        points_text = points_elem.get_text(strip=True)
        # Extract just the number
        points_match = re.search(r'([\d.]+)', points_text)
        if points_match:
            content["points_possible"] = points_match.group(1)
        else:
            content["points_possible"] = points_text
    
    # Extract submission types
    submission_elem = soup.find("div", class_="submission_types")
    if submission_elem:
        content["submission_types"] = submission_elem.get_text(strip=True)
    
    # Extract available from/until dates
    availability = {}
    available_from = soup.find("span", class_="available_from_date")
    if available_from:
        availability["from"] = available_from.get_text(strip=True)
    
    available_until = soup.find("span", class_="available_until_date")
    if available_until:
        availability["until"] = available_until.get_text(strip=True)
    
    if availability:
        content["availability"] = availability
    
    # Extract any attached files/resources
    attachments = []
    for link in soup.find_all("a", class_="instructure_file_link"):
        file_name = link.get_text(strip=True)
        file_url = link.get("href", "")
        if file_name and file_url:
            attachments.append({"name": file_name, "url": file_url})
    
    if attachments:
        content["attachments"] = attachments
    
    # Extract rubric if present
    rubric_elem = soup.find("div", class_="rubric")
    if rubric_elem:
        rubric_text = rubric_elem.get_text(strip=True)
        if rubric_text:
            content["has_rubric"] = True
            content["rubric_summary"] = rubric_text[:500]  # First 500 chars
    
    return content


def clear_courses(courses_dir):
    """Clear all course directories and files"""
    if not os.path.exists(courses_dir):
        print(f"No courses directory found at {courses_dir}")
        return
    
    # List all items in courses directory
    items = os.listdir(courses_dir)
    course_folders = [d for d in items if os.path.isdir(os.path.join(courses_dir, d)) and not d.endswith('_files')]
    html_files = [f for f in items if f.endswith('.html') and os.path.isfile(os.path.join(courses_dir, f))]
    support_folders = [d for d in items if d.endswith('_files') and os.path.isdir(os.path.join(courses_dir, d))]
    
    if not course_folders and not html_files and not support_folders:
        print("No courses to clear.")
        return
    
    print("\nFound items to clear:")
    if course_folders:
        print(f"  - {len(course_folders)} course folder(s): {', '.join(course_folders[:3])}")
        if len(course_folders) > 3:
            print(f"    ... and {len(course_folders) - 3} more")
    if html_files:
        print(f"  - {len(html_files)} HTML file(s)")
    if support_folders:
        print(f"  - {len(support_folders)} support folder(s) (_files)")
    
    confirm = input("\nAre you sure you want to delete all courses? (yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("Cancelled.")
        return
    
    # Delete course folders
    deleted_count = 0
    for folder in course_folders:
        folder_path = os.path.join(courses_dir, folder)
        try:
            shutil.rmtree(folder_path)
            print(f"✓ Deleted: {folder}/")
            deleted_count += 1
        except Exception as e:
            print(f"✗ Error deleting {folder}: {e}")
    
    # Delete loose HTML files
    for file in html_files:
        file_path = os.path.join(courses_dir, file)
        try:
            os.remove(file_path)
            print(f"✓ Deleted: {file}")
            deleted_count += 1
        except Exception as e:
            print(f"✗ Error deleting {file}: {e}")
    
    # Delete support folders
    for folder in support_folders:
        folder_path = os.path.join(courses_dir, folder)
        try:
            shutil.rmtree(folder_path)
            print(f"✓ Deleted: {folder}/")
            deleted_count += 1
        except Exception as e:
            print(f"✗ Error deleting {folder}: {e}")
    
    print(f"\nCleared {deleted_count} item(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='CanvasScraper - Download and parse Canvas course assignments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 canvas_scraper.py              # Normal operation
  python3 canvas_scraper.py --clear      # Clear all courses
  python3 canvas_scraper.py -c           # Clear all courses (short form)
        """
    )
    parser.add_argument('--clear', '-c', action='store_true',
                        help='Clear all course directories and files')
    
    args = parser.parse_args()
    
    courses_dir = os.path.join(os.path.dirname(__file__), "courses")
    
    # Handle clear command
    if args.clear:
        print("CanvasScraper - Clear Courses")
        print("=" * 50)
        clear_courses(courses_dir)
        sys.exit(0)
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
    print(f"Found {len(assignments)} items")
    
    # Create assignments.csv in course directory
    csv_path = os.path.join(course_dir, "assignments.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "title", "url", "due_date", "points", "type"], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(assignments)
    
    print(f"\n✓ Created {safe_course_name}/assignments.csv")
    
    # Ask if user wants to download and parse
    print("\nOptions:")
    print("1. Download all items and parse to JSON (requires authentication)")
    print("2. Just create CSV and exit (download manually later)")
    choice = input("\nChoose option (1 or 2): ").strip()
    
    if choice != '1':
        print(f"\nCSV created with {len(assignments)} items.")
        print(f"To download later, visit each URL in the CSV and save as 'assignment_[id].html'")
        sys.exit(0)
    
    # Get authentication cookie
    print("\nFor authenticated downloads, provide your Canvas session cookie:")
    print("(Press F12 in Canvas → Application → Cookies → copy '_legacy_normandy_session' value)")
    print("Or press Enter to try without authentication (may fail)")
    cookie_value = input("\nCookie value: ").strip()
    
    session = requests.Session()
    if cookie_value:
        session.cookies.set("_legacy_normandy_session", cookie_value)
    
    # Set user agent to look like a browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Download and parse all assignments
    course_content = {
        "course_name": course_name,
        "assignments": []
    }
    
    print(f"\nDownloading and parsing {len(assignments)} items...")
    successful_downloads = 0
    
    for i, assignment in enumerate(assignments, 1):
        print(f"\n[{i}/{len(assignments)}] {assignment['title'][:60]}")
        
        # Determine filename from ID
        html_filename = f"assignment_{assignment['id']}.html"
        html_path = os.path.join(course_dir, html_filename)
        
        # Download if not exists
        if os.path.exists(html_path):
            print(f"  ✓ Already exists: {html_filename}")
        else:
            success = download_assignment_html(assignment['url'], html_path, session)
            if success:
                print(f"  ✓ Downloaded: {html_filename}")
                successful_downloads += 1
                time.sleep(1)  # Be polite to the server
            else:
                print(f"  ✗ Failed to download - skipping")
                continue
        
        # Parse content if file exists
        if os.path.exists(html_path):
            print(f"  📄 Parsing content...")
            content = parse_assignment_content(html_path)
            
            # Add metadata from CSV
            content["id"] = assignment["id"]
            content["url"] = assignment["url"]
            
            # Add CSV data if not found in HTML
            if "title" not in content or not content["title"]:
                content["title"] = assignment["title"]
            if "due_date" not in content and assignment.get("due_date"):
                content["due_date"] = assignment["due_date"]
            if "points_possible" not in content and assignment.get("points"):
                content["points_possible"] = assignment["points"]
            if assignment.get("type"):
                content["type"] = assignment["type"]
            
            course_content["assignments"].append(content)
            print(f"  ✓ Parsed")
        else:
            print(f"  ⊘ File not found: {html_filename}")
    
    # Save to JSON in course directory
    json_filename = f"course_content.json"
    json_path = os.path.join(course_dir, json_filename)
    
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(course_content, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print(f"✓ Created {safe_course_name}/course_content.json")
    print(f"✓ Downloaded {successful_downloads} new files")
    print(f"✓ Parsed {len(course_content['assignments'])} items total")
    print(f"\nAll files saved in: courses/{safe_course_name}/")
    print(f"{'='*60}")


