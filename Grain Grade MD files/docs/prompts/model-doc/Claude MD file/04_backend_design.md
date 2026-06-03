# Backend Design (FastAPI)

**Stack:** Python, FastAPI, Uvicorn/Gunicorn.

## API Endpoints

- **POST `/analyze`** – Analyze an image.  
  - *Request:* JSON with `image: "<base64 JPEG data>"`.  
  - *Response:* JSON graded output (as per schema above).  
- **GET `/health`** – Health check (returns 200 OK).

**Example Request (JSON):**  

```json
POST /analyze
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD..."
}
```

**Example Response (JSON):**  

```json
{
  "grade": "B",
  "quality_score": 78.3,
  "foreign_matter_pct": 1.5,
  "broken_grains_pct": 3.2,
  "insect_damage_pct": 0,
  "fungus_detected": false,
  "confidence": 0.88,
  "remarks": "Minor stone content detected; otherwise good."
}
```

## Core Modules

- `api/`: FastAPI routes (`/analyze`, `/health`).
- `services/ai_service.py`: Handles image preprocessing and calls Gemma 4 model API.
- `schemas/`: Pydantic models for requests and responses.
- `utils/`: Helper functions (image decoding, validation).

## Request Processing Flow

1. **Receive Request:** Validate JSON, extract base64 image.
2. **Preprocessing:** Decode base64 to image array, check resolution.
3. **Call AI:** Forward image to Gemma 4 (via HTTP/SDK).  

   ```python
   result = gemma_client.analyze(image_array)
   ```

4. **Postprocessing:** Parse model’s JSON, apply any business rules (e.g. clamp values).
5. **Respond:** Return JSON to client.

## Sample Code Snippet

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import base64, cv2
from services.ai_service import GemmaClient

app = FastAPI()
client = GemmaClient(model_endpoint_url)

class AnalyzeRequest(BaseModel):
    image: str

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    try:
        # Decode image
        header, img_data = req.image.split(",", 1)
        img_bytes = base64.b64decode(img_data)
        img = cv2.imdecode(np.frombuffer(img_bytes, np.uint8), cv2.IMREAD_COLOR)
        # Call Gemma 4 model
        result = await client.analyze_image(img)
        return result  # already JSON serializable dict
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```

*(This is a high-level sketch; actual code will include async handling, logging, and error checks.)*

## Error Handling

- **400 Bad Request:** Invalid JSON or corrupt image.
- **422 Unprocessable:** Validation failures.
- **500 Internal Error:** Model timeouts or unexpected errors.
- All exceptions logged for monitoring.

## Security

- Validate image size (e.g., max 5MB).
- Sanitize inputs to prevent injection.
- (If needed) API key or OAuth token check.

---
