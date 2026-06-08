import { useState } from "react";
import axios from "axios";
import { AlertCircle, Brain, FileUp, Loader2, Stethoscope } from "lucide-react";
import BASE_URL from "../api/api";

const initialForm = {
  patientName: "",
  age: "",
  gender: "",
  symptoms: "",
  temperature: "",
  bloodPressure: "",
  pulse: "",
  heartbeat: "",
  bloodGlucose: "",
  weight: "",
  height: "",
};

function RiskPredictPage() {
  const [form, setForm] = useState(initialForm);
  const [report, setReport] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const updateField = (event) => {
    const { name, value } = event.target;
    setForm((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");
    setResult(null);

    if (!report && !form.symptoms && !form.temperature && !form.bloodPressure && !form.bloodGlucose) {
      setError("Upload a report or enter health details before generating prediction.");
      return;
    }

    const payload = new FormData();
    Object.entries(form).forEach(([key, value]) => payload.append(key, value));

    if (report) {
      payload.append("report", report);
    }

    try {
      setLoading(true);
      const { data } = await axios.post(`${BASE_URL}/report/predict`, payload, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
    } catch (err) {
      setError(
        err.response?.data?.message ||
          "Prediction failed. Please make sure backend and ML server are running."
      );
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm(initialForm);
    setReport(null);
    setResult(null);
    setError("");
  };

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-blue-600 text-white">
            <Brain size={26} />
          </div>
          <div>
            <h1 className="text-2xl font-bold">AI Disease Prediction</h1>
            <p className="text-sm text-slate-600">
              Upload a report and enter patient details to generate a medical summary.
            </p>
          </div>
        </header>

        <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold">Patient Details</h2>

            <div className="grid gap-4 sm:grid-cols-2">
              <input name="patientName" value={form.patientName} onChange={updateField} placeholder="Patient name" className="rounded-md border border-slate-300 px-3 py-2" />
              <input name="age" value={form.age} onChange={updateField} placeholder="Age" className="rounded-md border border-slate-300 px-3 py-2" />
              <select name="gender" value={form.gender} onChange={updateField} className="rounded-md border border-slate-300 px-3 py-2">
                <option value="">Gender</option>
                <option value="Male">Male</option>
                <option value="Female">Female</option>
                <option value="Other">Other</option>
              </select>
              <input name="temperature" value={form.temperature} onChange={updateField} placeholder="Temperature, e.g. 98.6" className="rounded-md border border-slate-300 px-3 py-2" />
              <input name="bloodPressure" value={form.bloodPressure} onChange={updateField} placeholder="Blood pressure, e.g. 120/80" className="rounded-md border border-slate-300 px-3 py-2" />
              <input name="pulse" value={form.pulse} onChange={updateField} placeholder="Pulse, e.g. 72" className="rounded-md border border-slate-300 px-3 py-2" />
              <input name="heartbeat" value={form.heartbeat} onChange={updateField} placeholder="Heartbeat, e.g. 80" className="rounded-md border border-slate-300 px-3 py-2" />
              <input name="bloodGlucose" value={form.bloodGlucose} onChange={updateField} placeholder="Blood glucose, e.g. 110" className="rounded-md border border-slate-300 px-3 py-2" />
              <input name="weight" value={form.weight} onChange={updateField} placeholder="Weight kg, e.g. 70" className="rounded-md border border-slate-300 px-3 py-2" />
              <input name="height" value={form.height} onChange={updateField} placeholder="Height cm, e.g. 170" className="rounded-md border border-slate-300 px-3 py-2" />
            </div>

            <textarea
              name="symptoms"
              value={form.symptoms}
              onChange={updateField}
              placeholder="Symptoms or notes"
              rows={4}
              className="mt-4 w-full rounded-md border border-slate-300 px-3 py-2"
            />
          </section>

          <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold">Medical Report</h2>

            <label className="flex min-h-40 cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-center hover:border-blue-500">
              <FileUp className="mb-2 text-blue-600" size={30} />
              <span className="font-medium">{report ? report.name : "Upload PDF, JPG, JPEG, or PNG"}</span>
              <span className="mt-1 text-xs text-slate-500">Maximum size: 10 MB</span>
              <input
                type="file"
                accept=".pdf,.jpg,.jpeg,.png"
                onChange={(event) => setReport(event.target.files?.[0] || null)}
                className="hidden"
              />
            </label>

            {error && (
              <div className="mt-4 flex gap-2 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                <AlertCircle size={18} />
                <span>{error}</span>
              </div>
            )}

            <div className="mt-5 flex gap-3">
              <button
                type="submit"
                disabled={loading}
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-md bg-blue-600 px-4 py-3 font-semibold text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:bg-blue-300"
              >
                {loading ? <Loader2 className="animate-spin" size={20} /> : <Stethoscope size={20} />}
                {loading ? "Generating..." : "Generate Prediction"}
              </button>
              <button type="button" onClick={resetForm} className="rounded-md border border-slate-300 px-4 py-3 font-semibold text-slate-700 hover:bg-slate-100">
                Reset
              </button>
            </div>
          </section>
        </form>

        {result && (
          <section className="mt-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold">Prediction Result</h2>

            <div className="grid gap-4 md:grid-cols-3">
              <ResultBox label="Disease Prediction" value={result.disease_prediction || "N/A"} />
              <ResultBox label="Confidence Score" value={`${result.confidence_score ?? 0}%`} />
              <ResultBox label="Risk Level" value={result.risk_level || "N/A"} />
            </div>

            <ListBlock title="Suggestions" items={result.suggestions} />
            <ListBlock title="Recommendations" items={result.recommendations} />

            {result.summary && (
              <div className="mt-5">
                <h3 className="mb-2 font-semibold">Detailed Summary</h3>
                <pre className="whitespace-pre-wrap rounded-md bg-slate-50 p-4 text-sm leading-6 text-slate-700">
                  {result.summary}
                </pre>
              </div>
            )}
          </section>
        )}
      </div>
    </main>
  );
}

function ResultBox({ label, value }) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-lg font-bold text-slate-900">{value}</p>
    </div>
  );
}

function ListBlock({ title, items = [] }) {
  if (!items.length) return null;

  return (
    <div className="mt-5">
      <h3 className="mb-2 font-semibold">{title}</h3>
      <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
        {items.map((item, index) => (
          <li key={`${title}-${index}`}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

export default RiskPredictPage;
