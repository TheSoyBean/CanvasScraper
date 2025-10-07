# CanvasScraper

A CLI tool to download and parse Canvas course assignment data.

## Features
- Parse assignments from Canvas modules/assignments/grades page
- **Support for Modules pages** - extracts module items (assignments, quizzes, pages)
- Export assignment list to CSV with type metadata
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

### Quick Start

1. **Download your Canvas page as HTML**:
   - Go to Canvas → Your Course → Modules (or Assignments)
   - Right-click → "Save As" → "Webpage, Complete"
   - Save to `courses/` directory

2. **Run the script**:
   ```bash
   python3 canvas_scraper.py
   ```

3. **Choose your workflow**:
   - **Option 1**: Auto-download and parse (requires cookie)
   - **Option 2**: Just create CSV (download manually later)

### What the script does

1. ✓ Parses HTML and extracts all module/assignment links
2. ✓ Creates `assignments.csv` with URLs and metadata
3. ✓ Downloads each URL as HTML (with authentication)
4. ✓ Parses each HTML for detailed content:
   - Title, Description, Due Date, Points
   - Submission types, Availability dates
   - Attached files, Rubric info
   - Item type (assignment/quiz/page)
5. ✓ Saves everything to `course_content.json`

### Clear all courses

To delete all course folders and start fresh:
```bash
python3 canvas_scraper.py --clear
# or
python3 canvas_scraper.py -c
```

This will:
- Delete all course folders (e.g., `Chinese_1/`, `CE_Algor_Data_Struct/`)
- Delete all loose HTML files in `courses/`
- Delete all support folders (`*_files/`)
- Prompt for confirmation before deletion

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
4. Copy its value (long string)
5. Paste when the script prompts for cookie
6. Script will attempt to download all assignments

**📖 Detailed Cookie Instructions**: See [COOKIE_GUIDE.md](COOKIE_GUIDE.md) for step-by-step screenshots and troubleshooting.

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
