@echo off
echo Setting up RAG Document Assistant...

:: Rename file
if exist fixedapp.py (
    ren fixedapp.py app.py
    echo Renamed fixedapp.py to app.py
)

:: Create folders
mkdir templates 2>nul
mkdir data\docs 2>nul
mkdir data\images 2>nul
mkdir data\audio 2>nul

:: Create .gitkeep files
echo. > data\docs\.gitkeep
echo. > data\images\.gitkeep
echo. > data\audio\.gitkeep

:: Create .gitignore
(
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo env/
echo venv/
echo ENV/
echo env.bak/
echo venv.bak/
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo .DS_Store
echo Thumbs.db
echo data/docs/*.pdf
echo data/images/*
echo data/audio/*
echo .whisper/
echo .cache/
echo *.log
echo myenv/
) > .gitignore

echo Setup complete!
echo Run: git init
echo Run: git add .
echo Run: git commit -m "Initial commit"
pause