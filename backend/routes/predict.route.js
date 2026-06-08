const express = require('express');
const router = express.Router();
const axios = require("axios");
const multer = require("multer");
const FormData = require("form-data");
const Prediction = require("../models/prediction.model");

const upload = multer({
  storage: multer.memoryStorage(),
  limits: {
    fileSize: 10 * 1024 * 1024,
  },
  fileFilter: (req, file, cb) => {
    const allowedTypes = [
      "application/pdf",
      "image/jpeg",
      "image/png",
      "image/jpg",
    ];

    if (!allowedTypes.includes(file.mimetype)) {
      return cb(new Error("Only PDF, JPG, JPEG, and PNG reports are allowed"));
    }

    cb(null, true);
  },
});

const ML_SERVER_URL = process.env.ML_SERVER_URL || "http://127.0.0.1:8001";

// Report Analysis Endpoint
router.post("/analyze", async (req, res) => {
  try {
    const { fileUrl } = req.body;

    console.log("📥 File URL received:", fileUrl);

    const response = await axios.post(
      "https://smart-digital-healthcare-system-service.onrender.com/analyze",
      { fileUrl }
    );

    return res.json({
      success: true,
      risk_level: response.data.risk_level,
      abnormal_parameters: response.data.abnormal_parameters,
      report_analysis: response.data.report_analysis,
      specialist_suggestion: response.data.specialist_suggestion,
      doctor_suggestion: response.data.doctor_suggestion
    });

  } catch (error) {
    console.error("❌ Report analyzer error:");

    if (error.response) {
      console.error("Status:", error.response.status);
      console.error("Data:", error.response.data);
    } else {
      console.error("Message:", error.message);
    }

    return res.status(500).json({
      success: false,
      message: "Error analyzing report"
    });
  }
});

router.post("/predict", upload.single("report"), async (req, res) => {
  try {
    const {
      patientName = "",
      age = "",
      gender = "",
      symptoms = "",
      temperature = "",
      bloodPressure = "",
      pulse = "",
      heartbeat = "",
      bloodGlucose = "",
      weight = "",
      height = "",
    } = req.body || {};

    if (!req.file && !symptoms && !temperature && !bloodPressure && !bloodGlucose) {
      return res.status(400).json({
        success: false,
        message: "Please upload a report or enter health details for prediction",
      });
    }

    const form = new FormData();
    form.append("patientName", patientName);
    form.append("age", age);
    form.append("gender", gender);
    form.append("symptoms", symptoms);
    form.append("temperature", temperature);
    form.append("bloodPressure", bloodPressure);
    form.append("pulse", pulse);
    form.append("heartbeat", heartbeat);
    form.append("bloodGlucose", bloodGlucose);
    form.append("weight", weight);
    form.append("height", height);

    if (req.file) {
      form.append("report", req.file.buffer, {
        filename: req.file.originalname,
        contentType: req.file.mimetype,
      });
    }

    const mlResponse = await axios.post(`${ML_SERVER_URL}/predict`, form, {
      headers: form.getHeaders(),
      maxBodyLength: Infinity,
      timeout: 120000,
    });

    const mlData = mlResponse.data;

    const savedPrediction = await Prediction.create({
      patientName,
      age,
      gender,
      symptoms,
      healthDetails: {
        temperature,
        bloodPressure,
        pulse,
        heartbeat,
        bloodGlucose,
        weight,
        height,
      },
      reportFile: req.file
        ? {
            originalName: req.file.originalname,
            mimetype: req.file.mimetype,
            size: req.file.size,
          }
        : undefined,
      result: {
        diseasePrediction: mlData.disease_prediction,
        confidenceScore: mlData.confidence_score,
        riskLevel: mlData.risk_level,
        suggestions: mlData.suggestions || [],
        recommendations: mlData.recommendations || [],
        summary: mlData.summary,
        raw: mlData,
      },
    });

    return res.status(200).json({
      success: true,
      predictionId: savedPrediction._id,
      disease_prediction: mlData.disease_prediction,
      confidence_score: mlData.confidence_score,
      risk_level: mlData.risk_level,
      suggestions: mlData.suggestions || [],
      recommendations: mlData.recommendations || [],
      summary: mlData.summary,
      extracted_fields: mlData.extracted_fields || {},
    });
  } catch (error) {
    console.error("Prediction API error:", error.message);

    if (error.response) {
      return res.status(error.response.status || 500).json({
        success: false,
        message: error.response.data?.detail || "ML server prediction failed",
      });
    }

    return res.status(500).json({
      success: false,
      message: "Prediction failed. Please check backend and ML server logs.",
    });
  }
});



// Export the router
module.exports = router;
