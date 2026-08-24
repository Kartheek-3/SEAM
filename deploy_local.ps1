# deploy_local.ps1
# Helper script to run SEAM backend and frontend locally

Write-Host "Starting SEAM Local Deployment..." -ForegroundColor Green

# 1. Start the FastAPI Backend
Write-Host "Starting FastAPI Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\.venv\Scripts\Activate.ps1; uvicorn backend.main:app --reload --port 8000"

# 2. Start the Vite Frontend
Write-Host "Starting Vite Frontend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Deployment started! Check the newly opened windows for logs." -ForegroundColor Green
Write-Host "Backend API: http://localhost:8000/api/v1/health"
Write-Host "Frontend: http://localhost:5173"
