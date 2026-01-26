@echo off
python -m PyInstaller --onefile --console --clean --icon=src/icon.ico --name="IVAO_statusbotdbautoclean" --exclude-module=tkinter --exclude-module=_tkinter src/main.py