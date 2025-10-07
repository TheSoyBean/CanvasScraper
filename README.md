# CanvasScraper

A simple CLI tool to help you collect assignment data from Canvas courses.

## Current Progress
- CLI prompts for Canvas modules URL.
- Prompts user to download and upload the modules HTML file.
- Parses the modules HTML for assignment links.
- Next steps: Prompt user to upload each assignment HTML file, parse them, and export all assignment data to a single JSON file.

## Next Steps
1. Run `python3 canvas_scraper.py`.
2. Paste your Canvas modules URL when prompted.
3. Download the modules page as HTML from your browser ("Save As"), then provide the file path when prompted.
4. The script will parse the modules HTML and list all assignment links it finds.
5. For each assignment link, download the assignment page as HTML and provide the file path when prompted.
6. The script will parse each assignment HTML and collect the data.
7. All assignment data will be exported to a single JSON file (e.g., `course-name.json`).

## Requirements
- Python 3
- `beautifulsoup4` package (`pip install beautifulsoup4`)

## Planned Improvements
- Automate assignment HTML file prompts and parsing.
- Allow user to specify output directory and filename.
- Improve assignment data extraction for more details.
# CanvasScraper
Scrapes courses on canvas if login granted
