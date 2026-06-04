# Infrastructure, CI/CD & Monitoring

## Cloud Infrastructure

- **Model Hosting:** We plan to use Google Cloud:
  - **Vertex AI** or **Cloud Run** (with NVIDIA GPUs) to host Gemma. Vertex offers managed scaling【41†L102-L111】. Cloud Run (serverless) can run Gemma on-demand【41†L130-L139】.
  - **Backend/API:** Deploy FastAPI on Cloud Run or Cloud Run Jobs (for autoscale).
  - **Storage:** Cloud Storage or Firestore for storing analysis results/history.
- **Cost Estimate (ballpark/month):**  
  - GPU inference (Cloud Run): ~$1–3 per hour (depending on GPU).  
  - API hosting (Cloud Run): ~$0.10 per CPU-hour.  
  - Storage: negligible for small JSON records.
  - **Total:** ~$100–300/month for moderate usage (1000 analyses/month), plus Flutter Play Store fee ($25 one-time).

## CI/CD Pipeline

- **Code Repository:** GitHub.
- **CI/CD Tool:** GitHub Actions or Cloud Build.
  - On commit to `main`: run unit tests, lint checks.
  - Build Docker image for backend and push to registry.
  - Deploy to Cloud Run / Vertex AI via scripts.
- **Flutter App:**
  - Use [GitHub Actions Flutter](https://github.com/marketplace/actions/flutter-action) to run `flutter test`, build APK/IPA.
  - (Manual store release if needed).
  
## Monitoring & Logging

- **Logging:** Use Cloud Logging (Stackdriver) for backend logs (errors, request logs).  
- **Error Tracking:** Integrate Sentry or Firebase Crashlytics in Flutter and backend for uncaught exceptions.
- **Metrics:** Track API latency, error rates, invocation counts (via Cloud Monitoring).
- **Alerts:** Set alerts on error rate spikes or high latency.

## Disaster Recovery

- Use multiple zones for API (GCP multi-zone).
- Regular backups of any persistent data (e.g. Firestore backups).
- Automated health checks (Cloud Run auto-restart).

---
