# Stock Rotator Backend

Professional FastAPI backend for live CSV data rotation with Gemini AI trading assistant.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Configuration management
│   ├── models.py             # Pydantic models and schemas
│   ├── routes.py             # API route handlers
│   ├── csv_rotator.py        # CSV data management
│   ├── gemini_service.py     # Gemini AI integration
│   └── condition_service.py  # Trading condition logic
├── .env                      # Environment variables (not in git)
├── requirements.txt          # Python dependencies
├── backend_state.json        # State persistence (generated)
└── NIFTY_historical_data.csv # Data file
```

## Features

- **CSV Data Rotation**: Automatic rotation through CSV rows with configurable intervals
- **State Persistence**: Maintains row position across restarts
- **Gemini AI Integration**: Natural language trading condition parsing
- **Condition Evaluation**: Real-time monitoring and alerting
- **RESTful API**: Clean, documented endpoints
- **CORS Support**: Configured for local and production deployments

## API Endpoints

### GET /health
Health check endpoint.

**Response**: `{"status": "ok"}`

### GET /row
Get current CSV row with index.

**Response**:
```json
{
  "Date": "2023-01-01",
  "Open": "14000.00",
  "High": "14100.00",
  "Low": "13900.00",
  "Close": "14050.00",
  "index": 42
}
```

### POST /chat
Submit natural language trading command.

**Request**:
```json
{
  "message": "Alert me when Close is above 14050",
  "command_time": "2026-01-24T10:30:00Z"
}
```

**Response**:
```json
{
  "id": "uuid-here",
  "status": "pending",
  "message": "Alert me when Close is above 14050",
  "command_time": "2026-01-24T10:30:00Z",
  "parsed_time": "2026-01-24T10:30:01Z",
  "last_checked_time": "2026-01-24T10:30:01Z",
  "triggered_time": null,
  "assistant_message": "I'll alert you when Close exceeds 14050",
  "spec": {
    "field": "Close",
    "operator": ">",
    "value": "14050",
    "value_type": "number"
  }
}
```

### GET /conditions
Get all trading conditions sorted by creation time.

**Response**: Array of condition objects with full details.

## Configuration

Environment variables (`.env` file):

```env
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Optional
CSV_PATH=path/to/custom/data.csv
STATE_PATH=path/to/state.json
UPDATE_INTERVAL_SECONDS=60
GEMINI_MODEL=gemini-2.5-flash
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## Running the Application

### Development
```bash
uvicorn app.main:app --reload --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Architecture

### Separation of Concerns
- **config.py**: Centralized configuration management
- **models.py**: Data validation and serialization
- **routes.py**: HTTP request handling
- **csv_rotator.py**: Data source management
- **gemini_service.py**: AI integration
- **condition_service.py**: Business logic

### Thread Safety
- All shared state protected with locks
- Atomic operations for critical sections
- Callback pattern for loose coupling

### Error Handling
- HTTPException for API errors
- Graceful degradation on AI failures
- State persistence on crashes

## Development

### Adding New Endpoints
1. Add route handler to `routes.py`
2. Register in `main.py`
3. Update this README

### Adding New Services
1. Create service class in new file
2. Import and initialize in `main.py`
3. Inject via dependency or singleton

### Testing
```bash
# Test Gemini connection
python -c "from app.gemini_service import gemini_service; print(gemini_service._get_client())"

# Test condition evaluation
python -m app.condition_service
```

## Deployment

### Railway
Use provided `railway.toml` configuration.

### Docker
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## License

Proprietary - All Rights Reserved
