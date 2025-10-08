from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response
import os, joblib, time, json, threading
from typing import Dict, Any

MODEL_PATH = os.getenv("MODEL_PATH", "model/artifacts/model.pkl")
ENCODER_PATH = os.getenv("ENCODER_PATH", "model/artifacts/encoder.pkl")
REQUEST_LOG = os.getenv("REQUEST_LOG", "ops/data/live_requests.jsonl")

REQUEST_COUNT = Counter("inference_requests_total", "Total inference requests")
REQUEST_LATENCY = Histogram("inference_latency_seconds", "Inference latency in seconds")

app = FastAPI(title="MLOps Capstone API", version="0.2.0")

class Features(BaseModel):
    features: Dict[str, Any]

def load_artifacts():
    model = joblib.load(MODEL_PATH)
    encoder = joblib.load(ENCODER_PATH)
    return model, encoder

model, encoder = load_artifacts()

@app.middleware("http")
async def add_metrics(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    REQUEST_LATENCY.observe(time.time() - start)
    return response

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/predict")
def predict(payload: Features, request: Request):
    REQUEST_COUNT.inc()
    try:
        X = encoder.transform([payload.features])
        y = model.predict_proba(X)[0, 1]
        # async-ish write to log
        rec = {"ts": time.time(), "features": payload.features, "prediction": float(y)}
        def _write():
            os.makedirs(os.path.dirname(REQUEST_LOG), exist_ok=True)
            with open(REQUEST_LOG, "a") as f:
                f.write(json.dumps(rec) + "\n")
        threading.Thread(target=_write, daemon=True).start()
        return {"probability_over_50k": float(y)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def root():
    return {"message": "MLOps Capstone API. See /docs."}
