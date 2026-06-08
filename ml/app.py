import os  
import re 
import joblib  # to load trained ML model
import easyocr  # for OCR extraction from reports
import gradio as gr
import numpy as np  # numerical operations
from PIL import Image # image handling

# User-friendly summary generator
def generate_user_friendly_summary(labels, fields=None, risk_level=None):
    """
    Professional bullet + explanation summary (Option 3) — includes NORMAL values.
    - labels: list of detected conditions (strings) from classifiers + ML
    - fields: optional dict with numeric fields: temp, systolic, diastolic,
              pulse, heartbeat, glucose, bmi, age
    Returns a multi-line string (suitable for 'details' box).
    """
    # Ensure labels is a list
    labels = labels or []
    labels = [str(x) for x in labels]

    # Fields may be None; safe-extract values
    f = fields or {}
    temp = f.get("temp")
    systolic = f.get("systolic")
    diastolic = f.get("diastolic")
    pulse = f.get("pulse")
    heartbeat = f.get("heartbeat")
    glucose = f.get("glucose")
    bmi = f.get("bmi")
    age = f.get("age")

    # Helper to format values cleanly
    def fmt(v, dec=1):
        try:
            return f"{float(v):.{dec}f}"
        except Exception:
            return "N/A"

    lines = []
    lines.append("🩺 Health Summary:")

    # TEMPERATURE: use classifier for descriptive label
    temp_state = classify_fever_fahrenheit(temp)
    if temp_state:
        lines.append(f"- 🌡️ Temperature: **{temp_state}** — value: {fmt(temp)} °F. "
                     f"{_explain_temperature(temp_state)}")
    else:
        # if numeric but no label then normal
        if temp is not None:
            lines.append(f"- 🌡️ Temperature: **Normal** — value: {fmt(temp)} °F.")
        else:
            lines.append(f"- 🌡️ Temperature: **Not provided**.")

    # BLOOD PRESSURE: use systolic + diastolic if available
    bp_state = classify_bp_stage(systolic)
    if bp_state:
        lines.append(f"- 💓 Blood Pressure: **{bp_state}** — systolic: {fmt(systolic)}, diastolic: {fmt(diastolic)}. "
                     f"{_explain_bp(bp_state)}")
    else:
        if systolic is not None or diastolic is not None:
            if systolic is None: s_text = "N/A"
            else: s_text = fmt(systolic)
            if diastolic is None: d_text = "N/A"
            else: d_text = fmt(diastolic)
            lines.append(f"- 💓 Blood Pressure: **Normal** — systolic: {s_text}, diastolic: {d_text}.")
        else:
            lines.append(f"- 💓 Blood Pressure: **Not provided**.")

    # HEART RATE / PULSE
    hr_state = classify_heart_rate(pulse, heartbeat)
    if hr_state:
        lines.append(f"- ❤️ Heart Rate: **{hr_state}** — pulse: {fmt(pulse)}, heartbeat: {fmt(heartbeat)}. "
                     f"{_explain_heart_rate(hr_state)}")
    else:
        if pulse is not None or heartbeat is not None:
            lines.append(f"- ❤️ Heart Rate: **Normal** — pulse: {fmt(pulse)}, heartbeat: {fmt(heartbeat)}.")
        else:
            lines.append(f"- ❤️ Heart Rate: **Not provided**.")

    # GLUCOSE
    gl_state = classify_glucose(glucose)
    if gl_state:
        lines.append(f"- 🩸 Blood Glucose: **{gl_state}** — value: {fmt(glucose)} mg/dL. "
                     f"{_explain_glucose(gl_state)}")
    else:
        if glucose is not None:
            lines.append(f"- 🩸 Blood Glucose: **Normal** — value: {fmt(glucose)} mg/dL.")
        else:
            lines.append(f"- 🩸 Blood Glucose: **Not provided**.")

    # BMI
    bmi_state = classify_bmi(bmi, age)
    if bmi_state:
        lines.append(f"- ⚖️ BMI: **{bmi_state}** — BMI: {fmt(bmi)}. {_explain_bmi(bmi_state)}")
    else:
        if bmi is not None:
            lines.append(f"- ⚖️ BMI: **Normal** — BMI: {fmt(bmi)}.")
        else:
            lines.append(f"- ⚖️ BMI: **Not provided**.")

    # AI/ML detected labels (extra)
    used_identifiers = []
    # detect which labels are already represented to avoid repeats
    for lab in labels:
        ll = str(lab).lower()
        if any(k in ll for k in ["fever", "hypothermia"]):
            used_identifiers.append(lab)
        elif any(k in ll for k in ["hypertensive", "hypertension", "elevated bp", "crisis"]):
            used_identifiers.append(lab)
        elif any(k in ll for k in ["tachycardia", "bradycardia", "severe", "high tachycardia"]):
            used_identifiers.append(lab)
        elif any(k in ll for k in ["diabetes", "prediabetes", "low glucose", "very high"]):
            used_identifiers.append(lab)
        elif lab in ["Underweight", "Overweight", "Obesity"]:
            used_identifiers.append(lab)
    extra = [str(x) for x in labels if str(x) not in used_identifiers]

    if extra:
        lines.append("\n🤖 AI / ML Detected Additional Conditions:")
        for e in extra:
            lines.append(f"- {e}")

    # Recommendations: concise, condition-linked 
    lines.append("\n✅ Recommended Actions:")
    # Temperature advice
    if temp_state:
        lines.append("- Drink fluids, rest, monitor temperature every 4 hours.")
        if "very high" in temp_state.lower() or "high fever" in temp_state.lower() or "very high fever" in temp_state.lower():
            lines.append("- ⚠️ High fever: seek urgent medical help (possible emergency).")

    # Glucose advice
    if gl_state:
        gl_low = "low" in gl_state.lower()
        gl_high = any(w in gl_state.lower() for w in ["diabetes", "very high", "prediabetes"])
        if gl_low:
            lines.append("- Hypoglycemia: take fast-acting carbohydrate (juice, glucose) and recheck.")
        elif gl_high:
            lines.append("- High glucose: reduce carbohydrate intake and contact healthcare provider; urgent care if very high.")

    # BP advice
    if bp_state:
        if "crisis" in bp_state.lower():
            lines.append("- ⚠️ Hypertensive crisis: seek emergency care immediately.")
        elif "stage 2" in bp_state.lower():
            lines.append("- Stage 2 hypertension: medical therapy likely needed; consult a doctor.")
        elif "stage 1" in bp_state.lower():
            lines.append("- Stage 1 hypertension: lifestyle changes recommended and monitor frequently.")
        else:
            lines.append("- Monitor BP twice daily and reduce salt & stress.")

    # HR advice
    if hr_state:
        if "severe" in hr_state.lower():
            lines.append("- ⚠️ Severe abnormal heart rate: seek urgent medical attention.")
        else:
            lines.append("- Avoid heavy exercise today; rest and re-evaluate heart rate.")

    # BMI advice
    if bmi_state:
        if bmi_state == "Underweight":
            lines.append("- Consider nutrition support and consult a dietitian.")
        elif bmi_state == "Overweight":
            lines.append("- Start mild exercise and portion control.")
        else:
            lines.append("- Medical weight management and lifestyle program recommended.")

    lines.append("\nℹ️ Note: This is an automated assessment. For medical advice, consult a healthcare professional.")

    return "\n".join(lines)


# -------------------------
# Small helper explanation functions (used inside summary)

def _explain_temperature(state):
    s = state.lower() if state else ""
    if "very high" in s or "er" in s or "high fever" in s:
        return "Body temperature is substantially elevated and may require urgent care."
    if "high fever" in s:
        return "High fever — monitor closely and seek care if other worrying signs appear."
    if "fever" in s:
        return "Fever detected — often due to infection; rest and fluids recommended."
    if "low-grade" in s:
        return "Low-grade fever — monitor and recheck."
    if "hypothermia" in s:
        return "Low body temperature — keep warm and seek assessment."
    return ""

def _explain_bp(state):
    s = state.lower() if state else ""
    if "crisis" in s:
        return "Very high blood pressure requiring immediate emergency care."
    if "stage 2" in s:
        return "Stage 2 hypertension — usually requires medication and follow-up."
    if "stage 1" in s:
        return "Stage 1 hypertension — lifestyle changes and monitoring recommended."
    if "elevated" in s:
        return "Systolic is elevated above optimal but below hypertension threshold."
    return ""

def _explain_heart_rate(state):
    s = state.lower() if state else ""
    if "severe" in s or "high" in s:
        return "Heart rate is significantly elevated (tachycardia) — may need evaluation."
    if "tachycardia" in s:
        return "Faster than normal heart rate — could be due to fever, dehydration, or cardiac issue."
    if "bradycardia" in s:
        return "Slower than normal heart rate — evaluate symptoms like dizziness or syncope."
    return ""

def _explain_glucose(state):
    s = state.lower() if state else ""
    if "very high" in s or "diabetes" in s:
        return "High glucose levels — may indicate diabetes; urgent consultation advised if very high."
    if "prediabetes" in s:
        return "Borderline elevated glucose — lifestyle changes and follow-up testing recommended."
    if "low" in s:
        return "Low glucose can cause dizziness and needs quick carbohydrate intake."
    return ""

def _explain_bmi(state):
    s = state.lower() if state else ""
    if "underweight" in s:
        return "BMI is below recommended range for adults."
    if "overweight" in s:
        return "BMI above normal; lifestyle changes advised."
    if "obesity" in s:
        return "BMI indicates obesity; structured weight-loss program advised."
    return ""

# -------------------------
# Config / load model + OCR

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "multi_disease_model.pkl")
if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError("Model file missing: multi_disease_model.pkl")

model = joblib.load(MODEL_PATH)
reader = easyocr.Reader(["en"], gpu=False)

# -------------------------
# OCR extraction
# -------------------------
# Compile patterns once
_PATTERNS = {
    "name": re.compile(r"name[:\s]+([a-zA-Z ]{2,})"),
    "age": re.compile(r"age[:\s]+(\d{1,3})"),
    "gender": re.compile(r"gender[:\s]+(male|female|other)"),
    "address": re.compile(r"address[:\s]+([a-zA-Z0-9 ,.\-]+)"),
    "phone": re.compile(r"phone[:\s]+(\+?\d{7,15})"),
    "temp": re.compile(r"temp(?:erature)?[:\s]+([0-9]{1,3}\.?[0-9]*\s*[fFcC]?)"),
    "bp": re.compile(r"(?:bp|blood pressure)[:\s]+([\d]{2,3}\/\d{2,3})"),
    "pulse": re.compile(r"pulse[:\s]+(\d{1,3})"),
    "heartbeat": re.compile(r"heartbeat[:\s]+(\d{1,3})"),
    "blood_glucose": re.compile(r"(?:sugar|glucose)[:\s]+([0-9]{1,3}\.?[0-9]*)"),
    "weight": re.compile(r"weight[:\s]+([0-9]{1,4}\.?[0-9]*)"),
    "height": re.compile(r"height[:\s]+([0-9]{1,4}\.?[0-9]*)"),
}

def extract_fields(img):
    """
    Returns dictionary with keys:
    name, age, gender, address, phone, temp, bp, pulse, heartbeat, blood_glucose, weight, height
    """
    if img is None:
        return {}
    img = Image.fromarray(img).convert("RGB")
    texts = reader.readtext(np.array(img), detail=0)
    text = " ".join(texts).lower()

    extracted = {k: "" for k in ["name", "age", "gender", "address", "phone", "temp",
                                 "bp", "pulse", "heartbeat", "blood_glucose", "weight", "height"]}

    for k, regex in _PATTERNS.items():
        m = regex.search(text)
        if m:
            extracted[k] = m.group(1).strip()
    return extracted

# -------------------------
# Safe parsing helpers


def safe_num(v):
    """Return float or None; strips non-numeric except minus and dot."""
    try:
        if v is None or str(v).strip() == "":
            return None
        s = re.sub(r"[^\d.\-]", "", str(v))
        return float(s) if s != "" else None
    except Exception:
        return None

def parse_bp_systolic(bp):
    if not bp:
        return None
    nums = re.findall(r"\d+", str(bp))
    return float(nums[0]) if nums else None

def parse_bp_diastolic(bp):
    if not bp:
        return None
    nums = re.findall(r"\d+", str(bp))
    return float(nums[1]) if len(nums) > 1 else None

def calc_bmi_from_wh(weight, height):
    w = safe_num(weight)
    h = safe_num(height)
    if w is None or h is None or h == 0:
        return None
    return round(w / ((h/100)**2), 2)

def f_to_c(f):
    try:
        return (float(f) - 32.0) * 5.0/9.0
    except Exception:
        return None

def c_to_f(c):
    try:
        return (float(c) * 9.0/5.0) + 32.0
    except Exception:
        return None

# -------------------------
# Classifiers 
# -------------------------
def classify_fever_fahrenheit(t_f):
    if t_f is None:
        return None
    try:
        t = float(t_f)
    except:
        return None
    if t >= 105: return "Very High Fever (ER level)"
    if t >= 103: return "High Fever"
    if t >= 100.4: return "Fever"
    if t >= 99.1: return "Low-Grade Fever"
    if 97 <= t <= 99: return None
    if t < 95: return "Hypothermia"
    return None

def classify_glucose(g):
    if g is None: return None
    try:
        g = float(g)
    except:
        return None
    if g >= 200: return "Diabetes (very high)"
    if g >= 126: return "Diabetes"
    if g >= 100: return "Prediabetes"
    if g >= 70: return None
    return "Low Glucose"

def classify_bp_stage(s):
    if s is None: return None
    try:
        s = float(s)
    except:
        return None
    if s >= 180: return "Hypertensive Crisis"
    if s >= 140: return "Hypertension Stage 2"
    if s >= 130: return "Hypertension Stage 1"
    if s >= 120: return "Elevated BP"
    return None

def classify_heart_rate(pulse, hb):
    hr = hb if hb is not None else pulse
    if hr is None: return None
    try:
        hr = float(hr)
    except:
        return None
    if hr >= 140: return "Severe Tachycardia"
    if hr >= 120: return "High Tachycardia"
    if hr > 100: return "Tachycardia"
    if hr < 50: return "Bradycardia"
    return None

def classify_bmi(bmi, age_text):
    if bmi is None: return None
    try:
        bmi_v = float(bmi)
    except:
        return None
    try:
        age = int(age_text)
    except:
        age = None
    if age is None or age >= 18:
        if bmi_v < 18.5: return "Underweight"
        if bmi_v < 25: return None
        if bmi_v < 30: return "Overweight"
        return "Obesity"
    return None
    # app.py (PART 2 of 3)

# -------------------------
# High priority immediate alerts
# -------------------------
def high_priority_rule(fields):
    t = fields.get("temp")
    s = fields.get("systolic")
    g = fields.get("glucose")
    p = fields.get("pulse")
    hb = fields.get("heartbeat")

    if g is not None and g >= 200:
        return "Diabetes (very high)"
    if t is not None and t >= 105:
        return "Very High Fever (ER level)"
    if s is not None and s >= 180:
        return "Hypertensive Crisis"
    if (hb is not None and hb >= 140) or (p is not None and p >= 140):
        return "Severe Tachycardia"
    return None

# -------------------------
# Decision Logic 
# -------------------------
def combined_decision(temp_s, bp_s, pulse_s, hb_s, glu_s, weight_s, height_s, age_s):
    temp = safe_num(temp_s)
    systolic = parse_bp_systolic(bp_s)
    diastolic = parse_bp_diastolic(bp_s)
    pulse = safe_num(pulse_s)
    heartbeat = safe_num(hb_s)
    glucose = safe_num(glu_s)
    bmi = calc_bmi_from_wh(weight_s, height_s)

    fields = {
        "temp": temp,
        "systolic": systolic,
        "diastolic": diastolic,
        "pulse": pulse,
        "heartbeat": heartbeat,
        "glucose": glucose,
        "bmi": bmi,
        "age": age_s
    }

    # Immediate alerts
    hp = high_priority_rule(fields)
    if hp:
        risk_level = "🔴 Critical"

        summary = generate_user_friendly_summary([hp], fields, risk_level)
        summary = "🚑 EMERGENCY: Immediate medical attention required!\n\n" + summary

        return f"{hp} | Risk: {risk_level}", summary

    labels = []

    
    try:
        fl = classify_fever_fahrenheit(temp)
        if fl:
            labels.append(fl)
    except Exception:
        pass

    try:
        gl = classify_glucose(glucose)
        if gl:
            labels.append(gl)
    except Exception:
        pass

    try:
        bpl = classify_bp_stage(systolic)
        if bpl:
            labels.append(bpl)
    except Exception:
        pass

    try:
        hrl = classify_heart_rate(pulse, heartbeat)
        if hrl:
            labels.append(hrl)
    except Exception:
        pass

    try:
        bm = classify_bmi(bmi, age_s)
        if bm:
            labels.append(bm)
    except Exception:
        pass

    # ML prediction (best-effort)
    try:
        pred_input = [
            float(temp) if temp is not None else 0.0,
            float(systolic) if systolic is not None else 0.0,
            float(pulse) if pulse is not None else 0.0,
            float(heartbeat) if heartbeat is not None else 0.0,
            float(glucose) if glucose is not None else 0.0,
            float(bmi) if bmi is not None else 0.0
        ]
        ml = model.predict([pred_input])[0]
        if ml and str(ml) not in labels:
            labels.append(str(ml))
    except Exception:
        pass

    if not labels:
        return "Data missing", "No valid parameters available to predict. Please provide numeric values."

    # ✅ Calculate Risk Level
    risk_level = calculate_risk_level(fields, labels)

    # ✅ Generate summary (pass risk also if you updated function)
    summary = generate_user_friendly_summary(labels, fields, risk_level)

    # ✅ Add emergency alert
    if risk_level == "🔴 Critical":
        summary = "🚑 EMERGENCY: Immediate medical attention required!\n\n" + summary

    # ✅ Return result
    return f"{', '.join(labels)} | Risk: {risk_level}", summary

with gr.Blocks() as demo:
    gr.Markdown("<h1 style='text-align:center;'>AI Health OCR Summary System</h1>")

    with gr.Row():
        with gr.Column():
            name = gr.Textbox(label="Name", placeholder="Enter full name")
            age = gr.Textbox(label="Age", placeholder="e.g., 25")
            gender = gr.Dropdown(label="Gender", choices=["Male", "Female", "Other"], value=None)

            address = gr.Textbox(label="Address", placeholder="House / Street / Area")
            phone = gr.Textbox(label="Phone", placeholder="e.g., 9876543210")

            temp = gr.Textbox(label="Temperature (°F)", placeholder="e.g., 98.6")
            bp = gr.Textbox(label="Blood Pressure (120/80)", placeholder="120/80")
            pulse = gr.Textbox(label="Pulse (bpm)", placeholder="e.g., 72")
            heartbeat = gr.Textbox(label="Heartbeat (bpm)", placeholder="e.g., 80")
            blood_glucose = gr.Textbox(label="Blood Glucose (mg/dL)", placeholder="e.g., 110")

            weight = gr.Textbox(label="Weight (kg)", placeholder="e.g., 70")
            height = gr.Textbox(label="Height (cm)", placeholder="e.g., 170")

        with gr.Column():
            img = gr.Image(type="numpy", label="Upload Medical Report (Image)")

    fill_btn = gr.Button("Extract From Image")
    predict_btn = gr.Button("Generate Summary")

    details = gr.Textbox(label="Detailed Summary", lines=18)

    # Wire Functions
    def _extract_to_fields(img_src):
        d = extract_fields(img_src)
        return [
            d.get("name", ""), d.get("age", ""), d.get("gender", ""), d.get("address", ""),
            d.get("phone", ""), d.get("temp", ""), d.get("bp", ""), d.get("pulse", ""),
            d.get("heartbeat", ""), d.get("blood_glucose", ""), d.get("weight", ""), d.get("height", "")
        ]

    fill_btn.click(
        _extract_to_fields,
        inputs=[img],
        outputs=[name, age, gender, address, phone, temp, bp, pulse, heartbeat, blood_glucose, weight, height]
    )

    def _predict_summary(temp_s, bp_s, pulse_s, hb_s, glu_s, weight_s, height_s, age_s):
        _, summary = combined_decision(temp_s, bp_s, pulse_s, hb_s, glu_s, weight_s, height_s, age_s)
        return summary

    predict_btn.click(
        _predict_summary,
        inputs=[temp, bp, pulse, heartbeat, blood_glucose, weight, height, age],
        outputs=details
    )

def calculate_risk_level(fields, labels):
    risk_score = 0

    temp = fields.get("temp")
    systolic = fields.get("systolic")
    # xedf = [fc]
    glucose = fields.get("glucose")
    pulse = fields.get("pulse")
    heartbeat = fields.get("heartbeat")
    bmi = fields.get("bmi")

    # 🔥 Temperature Risk
    if temp:
        if temp >= 105:
            risk_score += 4
        elif temp >= 103:
            risk_score += 3
        elif temp >= 100.4:
            risk_score += 2

    # 💓 BP Risk
    if systolic:
        if systolic >= 180:
            risk_score += 4
        elif systolic >= 140:
            risk_score += 3
        elif systolic >= 130:
            risk_score += 2

    # 🩸 Glucose Risk
    if glucose:
        if glucose >= 200:
            risk_score += 4
        elif glucose >= 126:
            risk_score += 3
        elif glucose >= 100:
            risk_score += 2

    # ❤️ Heart Rate Risk
    hr = heartbeat if heartbeat else pulse
    if hr:
        if hr >= 140:
            risk_score += 4
        elif hr >= 120:
            risk_score += 3
        elif hr > 100:
            risk_score += 2

    # ⚖️ BMI Risk
    if bmi:
        if bmi >= 30:
            risk_score += 3
        elif bmi >= 25:
            risk_score += 2
        elif bmi < 18.5:
            risk_score += 2

    # 🤖 ML / Labels Boost
    for lab in labels:
        l = lab.lower()
        if "crisis" in l or "severe" in l:
            risk_score += 4
        elif "stage 2" in l or "diabetes" in l:
            risk_score += 3
        elif "stage 1" in l or "prediabetes" in l:
            risk_score += 2

    # 🎯 Final Risk Level
    if risk_score >= 12:
        return "🔴 Critical"
    elif risk_score >= 8:
        return "🟠 High"
    elif risk_score >= 4:
        return "🟡 Medium"
    else:
        return "🟢 Low"




if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=7860, share=False)
