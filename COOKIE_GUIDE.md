# How to Get Canvas Cookie for Authentication

Canvas requires authentication to download assignment pages. Here's how to get your session cookie:

## Method 1: Chrome/Edge (Recommended)

1. **Open Canvas in your browser** and make sure you're logged in

2. **Open Developer Tools**:
   - Press `F12` OR
   - Right-click anywhere → "Inspect" OR
   - Menu → More Tools → Developer Tools

3. **Go to the Application tab**:
   - Click the "Application" tab at the top of Developer Tools
   - If you don't see it, click the `>>` icon to find it

4. **Navigate to Cookies**:
   - In the left sidebar, expand "Storage" → "Cookies"
   - Click on your Canvas URL (e.g., `https://canvas.instructure.com` or `https://dsd.instructure.com`)

5. **Find the session cookie**:
   - Look for a cookie named `_legacy_normandy_session`
   - Click on it to select it

6. **Copy the cookie value**:
   - In the "Value" column, you'll see a long string
   - Double-click the value to select it
   - Copy it (Ctrl+C or Cmd+C)
   - It will look something like: `eyJfcmFpbHMiOnsibWVzc2FnZSI6Ik...` (very long)

## Method 2: Firefox

1. **Open Canvas** and log in

2. **Open Developer Tools**:
   - Press `F12` OR
   - Right-click → "Inspect"

3. **Go to Storage tab**:
   - Click the "Storage" tab
   - If you don't see it, click the `⋯` icon

4. **Navigate to Cookies**:
   - In the left sidebar, expand "Cookies"
   - Click on your Canvas URL

5. **Find and copy**:
   - Look for `_legacy_normandy_session`
   - Double-click the Value field
   - Copy the entire value

## Using the Cookie

When the script asks:
```
Cookie value (or press Enter to try without):
```

Paste the copied cookie value and press Enter.

**Important Notes:**
- The cookie is LONG (hundreds of characters) - this is normal
- Don't include quotes around it, just paste the raw value
- The cookie expires after some time (usually hours/days)
- If downloads fail, you may need to get a fresh cookie

## Alternative: Manual Download (No Cookie Needed)

If you don't want to use cookies:

1. When the script asks "Download assignments? (y/n):", type `n`
2. The script will create `assignments.csv` with all URLs
3. Manually visit each URL in your browser and save as HTML:
   - Go to assignment URL
   - Right-click → "Save As"
   - Save as "Complete webpage"
   - Name it: `assignment_[ID].html` (ID from CSV)
   - Save in the course folder: `courses/[CourseName]/`
4. Re-run the script and choose to parse existing files

## Troubleshooting

### "400 Bad Request" or "401 Unauthorized"
- Your cookie may have expired
- Get a fresh cookie by following the steps above
- Make sure you copied the entire value

### Cookie not found
- Try looking for other cookie names:
  - `canvas_session`
  - `_normandy_session`
  - `_session_id`
- Your Canvas instance might use a different cookie name

### Still having issues?
- Use the manual download method instead
- Or try using a browser extension that exports cookies
- Make sure you're logged into Canvas before getting the cookie
