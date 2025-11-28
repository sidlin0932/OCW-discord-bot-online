# Build & Packaging Guide

雖然本專案目前是 Python 腳本，不需要編譯，但為了未來的擴充性（如打包成執行檔或 Docker 化），在此記錄相關流程。

## 1. Python Environment

建議使用虛擬環境：

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

## 2. Docker Build (Future)

若未來要容器化，可使用以下 `Dockerfile` 範本：

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

建置指令：
```bash
docker build -t ocw-discord-bot .
```

## 3. PyInstaller (Executable)

若要打包成單一執行檔：

```bash
pip install pyinstaller
pyinstaller --onefile bot.py
```
產物將位於 `dist/bot.exe`。
