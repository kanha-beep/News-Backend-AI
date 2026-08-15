# Hindi translation service

This Python service translates English news fields into Hindi for the Node API.

## Run

```bash
cd python-services
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8010
```

## Run on Windows with the local virtual environment

```powershell
cd D:\study\Coding\JS\Projects_Company\News\python-services
.\.venv\Scripts\Activate.ps1
python -m uvicorn app:app --host 0.0.0.0 --port 8010
```

Or without activating the environment:

```powershell
cd D:\study\Coding\JS\Projects_Company\News\python-services
.\.venv\Scripts\python.exe -m uvicorn app:app --host 0.0.0.0 --port 8010
```

## Environment variables

```bash
TRANSLATION_SERVICE_API_KEY=your-shared-secret
CLIENT_APP_URL=http://localhost:5173
SERVER_API_URL=http://localhost:3000
TRANSLATION_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

## Node API environment variables

Add these to the server `.env`:

```bash
TRANSLATION_SERVICE_URL=http://127.0.0.1:8010
TRANSLATION_SERVICE_API_KEY=your-shared-secret
TRANSLATION_SERVICE_TIMEOUT_MS=8000
```

## Flow

1. News is fetched from RSS and saved in MongoDB in English.
2. User enables Hindi by calling `PUT /api/auth/preferences/language` with `{ "language": "hi" }`.
3. Client requests `/api/news` or `/api/news/article`.
4. Node checks the user preference or `language=hi` override.
5. Node sends article title, description, category, subcategory, and tags to the Python service.
6. Python translates the text and returns Hindi content.
7. Node merges the Hindi fields into the response JSON and sends it to the client.

## Notes

- MongoDB still keeps the original English article, which avoids data loss.
- If the Python service is down, the API falls back to English safely.
"# News-Backend-P" 
"# News-Backend-AI" 
