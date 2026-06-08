const mongoose = require("mongoose");

const predictionSchema = new mongoose.Schema(
  {
    patientName: String,
    age: String,
    gender: String,
    symptoms: String,
    healthDetails: {
      temperature: String,
      bloodPressure: String,
      pulse: String,
      heartbeat: String,
      bloodGlucose: String,
      weight: String,
      height: String,
    },
    reportFile: {
      originalName: String,
      mimetype: String,
      size: Number,
    },
    result: {
      diseasePrediction: String,
      confidenceScore: Number,
      riskLevel: String,
      suggestions: [String],
      recommendations: [String],
      summary: String,
      raw: mongoose.Schema.Types.Mixed,
    },
  },
  { timestamps: true }
);

module.exports = mongoose.model("Prediction", predictionSchema);
