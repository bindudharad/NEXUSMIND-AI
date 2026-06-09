$ErrorActionPreference = "Stop"

Push-Location backend
$Python = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }
& $Python -m pip install -r requirements.txt
& $Python -m compileall app
& $Python -m pytest -q
& $Python -m pip check
Pop-Location

Push-Location frontend
npm install
npm run type-check
npm run typecheck
npm run lint
npm run test
npm run audit:high
npm run build
Pop-Location
