## Run locally
1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Start Redis (if available locally):
   ```bash
   redis-server
   ```
3. Launch the API:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Open a WebSocket client to:
   ```text
   ws://127.0.0.1:8000/ws/demo-room
   ```

## Test
```bash
pytest -q