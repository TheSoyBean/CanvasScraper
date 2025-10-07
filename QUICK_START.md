# Quick Start Guide

## Step-by-Step: Download Course Assignments

### 1. Get the Modules/Assignments Page
- Go to Canvas → Your Course → Modules (or Assignments)
- Right-click on the page → "Save As"
- Choose "Webpage, Complete" or "HTML Only"
- Save to: `CanvasScraper/courses/`

### 2. Run the Script
```bash
cd CanvasScraper
source venv/bin/activate  # On Windows: venv\Scripts\activate
python3 canvas_scraper.py
```

### 3. Choose Download Method

#### Option A: Manual (Easier, No Cookie Needed)
```
Download assignments? (y/n): n
```
Then:
1. Open the generated `assignments.csv` in Excel/Sheets
2. Visit each URL manually in your browser
3. For each page: Right-click → Save As → "assignment_[ID].html"
4. Save in: `courses/[CourseName]/`
5. Re-run script to parse them

#### Option B: Automatic (Need Cookie)
```
Download assignments? (y/n): y
Cookie value (or press Enter to try without): [PASTE COOKIE HERE]
```

**To get cookie:**
- In Canvas: Press `F12`
- Go to: Application tab → Cookies → your Canvas site
- Find: `_legacy_normandy_session`
- Copy the Value (long string starting with `eyJ...`)
- Paste into the script

### 4. View Results

Files created in `courses/[CourseName]/`:
- `assignments.csv` - List of all assignments
- `assignment_[ID].html` - Downloaded assignment pages
- `course_content.json` - Parsed assignment data

## Common Issues

**"Found 0 assignments"**
- Make sure you downloaded a Modules or Assignments page, not just a single assignment
- The page should list multiple items

**"400 Bad Request" when downloading**
- Cookie expired or invalid
- Get a fresh cookie (logout and login to Canvas, then get new cookie)
- Or use manual download method

**Cookie not working**
- Try without cookie first (press Enter when prompted)
- Some Canvas sites work without authentication
- Otherwise use manual download

## Need Help?

See detailed guides:
- [COOKIE_GUIDE.md](COOKIE_GUIDE.md) - Detailed cookie instructions
- [README.md](README.md) - Full documentation
