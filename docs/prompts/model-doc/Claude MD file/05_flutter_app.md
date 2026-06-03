
# Flutter App Specification

## Overview & UX

The Flutter app will run on Android/iOS and provide:

1. **Home Screen:** Brief instructions; “Capture Grain Image” button.
2. **Camera Screen:** Live camera view with overlay box guiding the user. Capture button.
3. **Results Screen:** Displays Grade, Score, defect details, and optional annotated image.
4. **History Screen:** List of past analysis with date/score.

**Flow:**  
User opens app ▶ taps **Capture** ▶ takes photo of ragi on solid background ▶ app uploads to API ▶ awaits result ▶ displays results.

## Camera & Image Settings

- **Resolution:** Recommend ≥ 1920×1080 (full-HD) to resolve tiny grains.  
- **Lighting:** Diffused natural or indoor lighting. Avoid shadows/glare.  
- **Background:** Plain (white or dark matte) to contrast grains.  
- **Distance:** Keep consistent (~20–30 cm from sample).  
- **Focus:** Fixed focus or macro mode for clarity.

**Image Capture Checklist:**  

| Requirement        | Recommendation                 |
|--------------------|--------------------------------|
| Resolution         | ≥ 1920×1080 (1080p) or higher  |
| Lighting           | Even, diffuse (no glare/shadow)|
| Background         | Solid color (white/black)      |
| Framing            | Grains fill most of image area |
| Format             | JPEG/PNG, minimal compression  |

The camera screen may include a grid or overlay to center the sample and a “Confirm” button after capture.

## API Integration

The app sends the captured image to the backend:

```dart
var bytes = await capturedImage.toByteData(format: ImageByteFormat.png);
String base64Image = base64Encode(bytes.buffer.asUint8List());
var response = await http.post(
  Uri.parse("https://api.example.com/analyze"),
  headers: {"Content-Type": "application/json"},
  body: jsonEncode({"image": "data:image/png;base64,$base64Image"})
);
var result = jsonDecode(response.body);
```

Then parse `result["grade"]`, `result["quality_score"]`, etc., to display.

## UI/UX Notes

- Show a loading spinner during analysis.
- Provide clear error messages (e.g., “Image too blurry” or “Network error”).
- Present results with icons (e.g.  for good,  for caution).
- Allow copying/sharing results (for record-keeping).

---
