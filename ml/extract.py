import easyocr
import numpy as np
import cv2
import joblib

reader = easyocr.Reader(["en"])

# Load model
model = joblib.load("model.pkl")

def extract_fields(image_path):
    img = cv2.imread(image_path)
    result = reader.readtext(img, detail=0)

    # Create dict of extracted fields
    fields = {
        "text": " ".join(result)
    }
    return fields

def predict_disease(fields):
    text = fields["text"]

    # Convert text into model input (dummy example)
    X = np.array([len(text)])  # <-- Replace with your real preprocessing

    prediction = model.predict([X])[0]
    return prediction
