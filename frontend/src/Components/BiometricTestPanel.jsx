// src/Components/BiometricTestPanel.jsx
import React, { useRef, useState } from "react";
import SignatureCanvas from "react-signature-canvas";
import axios from "axios";

export default function BiometricTestPanel() {
  const sigCanvas = useRef(null);
  const [userId, setUserId] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const clearSignature = () => {
    if (sigCanvas.current) sigCanvas.current.clear();
  };

  const analyzeSignature = async () => {
    if (!userId) {
      alert("⚠ يرجى إدخال معرف المستخدم أولاً");
      return;
    }
    if (!sigCanvas.current || sigCanvas.current.isEmpty()) {
      alert("⚠ الرجاء رسم توقيعك داخل المربع أولاً");
      return;
    }

    const points = sigCanvas.current.toData();
    const signatureData = {
      points: points,
      timestamps: points.map((p, i) => i * 0.1), // مثال: توليد طوابع زمنية بسيطة
    };

    setLoading(true);
    try {
      const res = await axios.post("http://127.0.0.1:8000/api/biometric/process/", {
        user_id: userId,
        modalities: { signature: signatureData },   // ملاحظ: backend المتوقع الآن يستعمل "modalities"
        context: { device_type: "browser", location: "frontend_test" },
      }, { timeout: 10000 });
      setResult(res.data);
    } catch (err) {
      console.error(err);
      alert("حدث خطأ أثناء الاتصال بالـ API — راجعي الكونسول للمزيد من التفاصيل");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="bg-white shadow-lg rounded-2xl p-6 w-full max-w-xl space-y-4 border border-gray-200">
        <h1 className="text-2xl font-bold text-center text-indigo-700">🧠 Smart Biometric Analyzer</h1>

        <input
          type="text"
          placeholder="أدخل معرف المستخدم (User ID)"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          className="w-full border rounded-xl px-4 py-2 focus:ring focus:ring-indigo-300"
        />

        <div className="border-2 border-dashed rounded-2xl bg-gray-100 p-2">
          <SignatureCanvas
            ref={sigCanvas}
            penColor="black"
            backgroundColor="white"
            canvasProps={{ width: 650, height: 220, className: "rounded-xl shadow-inner" }}
          />
        </div>

        <div className="flex justify-between">
          <button onClick={clearSignature} className="px-4 py-2 rounded-xl bg-gray-300 hover:bg-gray-400 text-sm">🧹 مسح</button>
          <button
            onClick={analyzeSignature}
            disabled={loading}
            className="px-4 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 text-sm"
          >
            {loading ? "⏳ جاري التحليل..." : "🔍 تحليل التوقيع الحيوي"}
          </button>
        </div>

        {result && (
          <div className="mt-4 border-t pt-4 text-sm">
            <h2 className="font-bold text-gray-700 mb-2">🔎 نتائج التحليل:</h2>
            <pre className="bg-gray-50 border rounded-xl p-2 overflow-auto text-gray-700 max-h-64">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}