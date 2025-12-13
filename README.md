# CS492 Bookstore App

Local development & quick run instructions

Prerequisites:

- Python 3.8+ (a virtual environment is recommended)

- Node.js/npm (optional, only needed for frontend tooling)

Run the app (opens the HTML UI in your default browser):

```powershell
& ".venv\Scripts\Activate.ps1"   # (Windows PowerShell) activate your venv
python Bookstore_Management_System.py
```

Or open `Bookstore_Management_System.html` directly in a browser.

Frontend notes:

- A small Node.js `package.json` exists; `npm ci` will install dev dependencies. There are no unit tests defined by default.

What I changed in this branch (`chore/fix-lint`):

- Fixed accessibility on form inputs across HTML files (added labels, placeholders, titles, aria-labels).
- Cleaned duplicate GitHub Actions workflow file content.
- Added client-side receipt generation with print and PDF export (uses `html2canvas` + `jsPDF` via CDN).
- Replaced visual `---` separators with `<hr>` elements and moved inline receipt styles into CSS classes.

How to commit & push these local changes:

```bash
git checkout -b chore/fix-lint
git add .
git commit -m "chore: fix lint/accessibility, add receipt PDF and README"
git push -u origin chore/fix-lint

# Create a PR with GitHub CLI (optional):
gh pr create --base main --head chore/fix-lint --fill
```
