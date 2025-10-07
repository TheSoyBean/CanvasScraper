# CanvasScraper

A CLI tool to download and parse Canvas course assignment data.

## Features
- Parse assignments from Canvas modules/assignments/grades page
- Export assignment list to CSV
- Download assignment pages automatically (with authentication)
- Parse assignment content into structured JSON

## Requirements
- Python 3
- Required packages: `beautifulsoup4`, `requests`

Install dependencies:
```bash
pip install beautifulsoup4 requests
# or
pip install -r requirements.txt
```

## Usage

### Step 1: Download the assignments page
1. Go to your Canvas course
2. Navigate to Assignments, Modules, or Grades page
3. Right-click → "Save As" → Save as HTML (complete page)
4. Save the file in the `courses/` directory

### Step 2: Run the script
```bash
python3 canvas_scraper.py
```

### Step 3: Choose your workflow

The script will:
1. Parse the HTML file and extract all assignment links
2. Create `assignments.csv` with assignment metadata
3. Optionally download each assignment page
4. Parse assignment content and save to `course_content_[course_name].json`

### Authentication (for downloads)

Canvas requires authentication to download assignment pages. You have two options:

**Option A: Manual download (recommended)**
- Select "n" when asked to download
- Manually download each assignment page from Canvas
- Save files as `assignment_[ID].html` in `courses/[Course_Name]/` directory
- Re-run the script and choose to parse existing files

**Option B: Automatic download with cookie**
1. Open Canvas in your browser while logged in
2. Press F12 → Application/Storage → Cookies
3. Find `_legacy_normandy_session` cookie
4. Copy its value
5. Paste when the script prompts for cookie
6. Script will attempt to download all assignments

## Output Files

All files are organized in a course-specific folder:

```
courses/
└── Course_Name/
    ├── Assignments_ Course Name.html      # Original downloaded page
    ├── assignments.csv                    # List of all assignments
    ├── assignment_[ID].html               # Individual assignment pages
    └── course_content.json                # Structured assignment data
```

### File descriptions:

- `assignments.csv` - List of all assignments with metadata (ID, title, URL, due date, points)
- `assignment_[ID].html` - Individual assignment HTML files
- `course_content.json` - Structured assignment data in JSON format

## Example JSON Output

```json
{
  "course_name": "Chinese 1",
  "assignments": [
    {
      "id": "22550830",
      "title": "Week 8 Participation",
      "url": "https://...",
      "description": "...",
      "due_date": "Oct 7 at 11:59pm",
      "points_possible": "10"
    }
  ]
}
```
