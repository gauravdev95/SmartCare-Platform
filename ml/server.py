from io import BytesIO
from typing import Optional

import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image

import app as ml_app

api = FastAPI(title="SmartCare ML Prediction Server")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def _merge(form_value: str, extracted_value: str) -> str:
    return _clean(form_value) or _clean(extracted_value)


def _extract_from_report(report: Optional[UploadFile]) -> dict:
    if report is None:
        return {}

    content_type = report.content_type or ""
    if content_type == "application/pdf":
        return {
            "note": "PDF received. This ML endpoint uses typed health values and image OCR. For PDF text analysis, use the FastAPI report analyzer service.",
        }

    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported report type. Upload PDF, JPG, JPEG, or PNG.",
        )

    try:
        image_bytes = report.file.read()
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        return ml_app.extract_fields(np.array(image))
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Could not read uploaded report image: {exc}",
        )


def _confidence_from_fields(values: dict, prediction: str) -> float:
    usable_keys = ["temperature", "bloodPressure", "pulse", "heartbeat", "bloodGlucose", "weight", "height", "age"]
    filled_count = sum(1 for key in usable_keys if _clean(values.get(key)))

    if prediction.lower().startswith("data missing"):
        return 0.0

    confidence = 45 + filled_count * 6
    if values.get("reportWasUsed"):
        confidence += 7

    return min(float(confidence), 95.0)


def _recommendations_for_prediction(prediction: str, risk_level: str, symptoms: str) -> list:
    text = f"{prediction} {risk_level} {symptoms}".lower()
    recommendations = [
        "Consult a qualified doctor before making medical decisions.",
        "Keep your report and entered health values for the consultation.",
    ]

    if "diabetes" in text or "glucose" in text:
        recommendations.append("Monitor blood glucose and reduce high-sugar meals until reviewed by a clinician.")
    if "hypertension" in text or "bp" in text or "pressure" in text:
        recommendations.append("Recheck blood pressure after rest and avoid excess salt.")
    if "fever" in text:
        recommendations.append("Drink fluids, rest, and monitor temperature regularly.")
    if "critical" in text or "crisis" in text or "severe" in text:
        recommendations.insert(0, "Seek urgent medical care if symptoms are severe or worsening.")

    return recommendations


@api.get("/health")
def health_check():
    return {"success": True, "message": "ML server is running"}


@api.post("/predict")
async def predict(
    report: Optional[UploadFile] = File(default=None),
    patientName: str = Form(default=""),
    age: str = Form(default=""),
    gender: str = Form(default=""),
    symptoms: str = Form(default=""),
    temperature: str = Form(default=""),
    bloodPressure: str = Form(default=""),
    pulse: str = Form(default=""),
    heartbeat: str = Form(default=""),
    bloodGlucose: str = Form(default=""),
    weight: str = Form(default=""),
    height: str = Form(default=""),
):
    extracted = _extract_from_report(report)

    values = {
        "patientName": _clean(patientName),
        "age": _merge(age, extracted.get("age", "")),
        "gender": _merge(gender, extracted.get("gender", "")),
        "symptoms": _clean(symptoms),
        "temperature": _merge(temperature, extracted.get("temp", "")),
        "bloodPressure": _merge(bloodPressure, extracted.get("bp", "")),
        "pulse": _merge(pulse, extracted.get("pulse", "")),
        "heartbeat": _merge(heartbeat, extracted.get("heartbeat", "")),
        "bloodGlucose": _merge(bloodGlucose, extracted.get("blood_glucose", "")),
        "weight": _merge(weight, extracted.get("weight", "")),
        "height": _merge(height, extracted.get("height", "")),
        "reportWasUsed": report is not None,
    }

    prediction_text, summary = ml_app.combined_decision(
        values["temperature"],
        values["bloodPressure"],
        values["pulse"],
        values["heartbeat"],
        values["bloodGlucose"],
        values["weight"],
        values["height"],
        values["age"],
    )

    disease_prediction = prediction_text
    risk_level = "Unknown"
    if "| Risk:" in prediction_text:
        disease_prediction, risk_level = [part.strip() for part in prediction_text.split("| Risk:", 1)]

    suggestions = [item.strip() for item in disease_prediction.split(",") if item.strip()]

    return {
        "success": True,
        "patient_name": values["patientName"],
        "disease_prediction": disease_prediction,
        "confidence_score": _confidence_from_fields(values, prediction_text),
        "risk_level": risk_level,
        "suggestions": suggestions,
        "recommendations": _recommendations_for_prediction(disease_prediction, risk_level, values["symptoms"]),
        "summary": summary,
        "extracted_fields": extracted,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(api, host="127.0.0.1", port=8001)
