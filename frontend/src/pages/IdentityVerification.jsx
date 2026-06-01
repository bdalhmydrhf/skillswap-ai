// src/pages/IdentityVerification.jsx
import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  Shield, Camera, Upload, CheckCircle, XCircle, 
  Loader2, ArrowLeft, FileText, UserCheck
} from "lucide-react";
import api from "../api/axiosConfig";

const BACKEND_URL = "http://127.0.0.1:8001";

export default function IdentityVerification() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [documentFront, setDocumentFront] = useState(null);
  const [documentFrontPreview, setDocumentFrontPreview] = useState(null);
  const [documentBack, setDocumentBack] = useState(null);
  const [documentBackPreview, setDocumentBackPreview] = useState(null);
  const [selfie, setSelfie] = useState(null);
  const [selfiePreview, setSelfiePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [method, setMethod] = useState("national_id");

  const handleDocumentFrontChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setDocumentFront(file);
      setDocumentFrontPreview(URL.createObjectURL(file));
    }
  };

  const handleDocumentBackChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setDocumentBack(file);
      setDocumentBackPreview(URL.createObjectURL(file));
    }
  };

  const handleSelfieChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setSelfie(file);
      setSelfiePreview(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async () => {
    if (!documentFront || !selfie) {
      alert("Please upload both document front and selfie");
      return;
    }

    // ✅ التحقق من الوجه الخلفي للهوية الوطنية
    if (method === 'national_id' && !documentBack) {
      alert("Please upload back side of your National ID");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("document_front", documentFront);
    formData.append("selfie_photo", selfie);
    formData.append("verification_method", method);
    
    // ✅ إضافة الوجه الخلفي إذا موجود
    if (documentBack) {
      formData.append("document_back", documentBack);
    }

    try {
      const response = await api.post("/verification/submit/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
      setStep(3);
      
      if (response.data.status === "approved") {
        setTimeout(() => {
          navigate("/profile");
        }, 2000);
      }
    } catch (error) {
      console.error(error);
      alert(error.response?.data?.error || "Verification failed");
      setResult({ status: "failed", error: error.response?.data?.error });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900 pt-24 pb-12 px-6">
      <div className="max-w-2xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate(-1)}
          className="mb-6 flex items-center gap-2 text-white/60 hover:text-white transition"
        >
          <ArrowLeft size={20} /> Back
        </button>

        {/* Main Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 overflow-hidden"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600/30 to-pink-600/30 p-6 border-b border-white/10">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                <Shield size={24} className="text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Identity Verification</h1>
                <p className="text-white/50 text-sm">Verify your identity to increase trust score</p>
              </div>
            </div>
          </div>

          {/* Steps */}
          <div className="p-6">
            <div className="flex items-center justify-between mb-8">
              {[1, 2, 3].map((s) => (
                <div key={s} className="flex items-center">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center font-bold ${
                      step >= s
                        ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white"
                        : "bg-white/20 text-white/40"
                    }`}
                  >
                    {step > s ? <CheckCircle size={20} /> : s}
                  </div>
                  {s < 3 && (
                    <div
                      className={`w-16 h-0.5 mx-2 ${
                        step > s ? "bg-purple-500" : "bg-white/20"
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>

            {/* Step 1: Choose Method */}
            {step === 1 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <h2 className="text-xl font-semibold text-white">Choose Document Type</h2>
                
                <div className="grid grid-cols-2 gap-4">
                  {[
                    { id: "national_id", label: "National ID", icon: <FileText size={24} /> },
                    { id: "passport", label: "Passport", icon: <FileText size={24} /> },
                    { id: "driving_license", label: "Driving License", icon: <FileText size={24} /> },
                  ].map((opt) => (
                    <button
                      key={opt.id}
                      onClick={() => setMethod(opt.id)}
                      className={`p-4 rounded-xl border-2 transition-all ${
                        method === opt.id
                          ? "border-purple-500 bg-purple-500/20"
                          : "border-white/20 hover:border-white/40"
                      }`}
                    >
                      <div className="flex flex-col items-center gap-2 text-white">
                        {opt.icon}
                        <span className="text-sm">{opt.label}</span>
                      </div>
                    </button>
                  ))}
                </div>

                <button
                  onClick={() => setStep(2)}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:shadow-lg transition"
                >
                  Continue
                </button>
              </motion.div>
            )}

            {/* Step 2: Upload Documents */}
            {step === 2 && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="space-y-6"
              >
                <h2 className="text-xl font-semibold text-white">Upload Documents</h2>
                
                {/* Document Front */}
                <div>
                  <label className="block text-white/70 text-sm mb-2">
                    Front Side of Document
                  </label>
                  <div
                    onClick={() => document.getElementById("documentFront")?.click()}
                    className="border-2 border-dashed border-white/30 rounded-xl p-6 text-center cursor-pointer hover:border-purple-500 transition"
                  >
                    {documentFrontPreview ? (
                      <img
                        src={documentFrontPreview}
                        alt="Document Front"
                        className="max-h-48 mx-auto rounded-lg"
                      />
                    ) : (
                      <div className="flex flex-col items-center gap-2 text-white/50">
                        <Upload size={32} />
                        <p>Click to upload front side</p>
                      </div>
                    )}
                  </div>
                  <input
                    id="documentFront"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleDocumentFrontChange}
                  />
                </div>

                {/* ✅ Document Back (يظهر فقط للهوية الوطنية ورخصة السياقة) */}
                {method !== 'passport' && (
                  <div>
                    <label className="block text-white/70 text-sm mb-2">
                      Back Side of Document {method === 'national_id' && '(required for National ID)'}
                    </label>
                    <div
                      onClick={() => document.getElementById("documentBack")?.click()}
                      className="border-2 border-dashed border-white/30 rounded-xl p-6 text-center cursor-pointer hover:border-purple-500 transition"
                    >
                      {documentBackPreview ? (
                        <img
                          src={documentBackPreview}
                          alt="Document Back"
                          className="max-h-48 mx-auto rounded-lg"
                        />
                      ) : (
                        <div className="flex flex-col items-center gap-2 text-white/50">
                          <Upload size={32} />
                          <p>Click to upload back side</p>
                        </div>
                      )}
                    </div>
                    <input
                      id="documentBack"
                      type="file"
                      accept="image/*"
                      className="hidden"
                      onChange={handleDocumentBackChange}
                    />
                  </div>
                )}

                {/* Selfie */}
                <div>
                  <label className="block text-white/70 text-sm mb-2">
                    Selfie Photo (Face visible)
                  </label>
                  <div
                    onClick={() => document.getElementById("selfiePhoto")?.click()}
                    className="border-2 border-dashed border-white/30 rounded-xl p-6 text-center cursor-pointer hover:border-purple-500 transition"
                  >
                    {selfiePreview ? (
                      <img
                        src={selfiePreview}
                        alt="Selfie"
                        className="max-h-48 mx-auto rounded-lg"
                      />
                    ) : (
                      <div className="flex flex-col items-center gap-2 text-white/50">
                        <Camera size={32} />
                        <p>Click to upload selfie</p>
                      </div>
                    )}
                  </div>
                  <input
                    id="selfiePhoto"
                    type="file"
                    accept="image/*"
                    className="hidden"
                    onChange={handleSelfieChange}
                  />
                </div>

                <button
                  onClick={handleSubmit}
                  disabled={loading || !documentFront || !selfie}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:shadow-lg transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  {loading ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    <>
                      <Shield size={20} />
                      Submit Verification
                    </>
                  )}
                </button>
              </motion.div>
            )}

            {/* Step 3: Result */}
            {step === 3 && result && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="text-center py-8"
              >
                {result.status === "approved" ? (
                  <>
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-green-500/20 flex items-center justify-center">
                      <CheckCircle size={40} className="text-green-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-green-400">Verification Approved!</h2>
                    <p className="text-white/60 mt-2">
                      Your identity has been verified. Trust score increased!
                    </p>
                    <div className="mt-4 p-4 bg-white/5 rounded-xl">
                      <div className="flex justify-between text-sm">
                        <span>Face Match Score:</span>
                        <span className="text-green-400">{Math.round((result.face_match_score || 0.85) * 100)}%</span>
                      </div>
                      <div className="flex justify-between text-sm mt-2">
                        <span>Overall Score:</span>
                        <span className="text-green-400">{Math.round((result.overall_score || 0.85) * 100)}%</span>
                      </div>
                    </div>
                    <p className="text-white/40 text-sm mt-4">
                      Redirecting to profile...
                    </p>
                  </>
                ) : result.status === "pending" ? (
                  <>
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-yellow-500/20 flex items-center justify-center">
                      <Loader2 size={40} className="text-yellow-400 animate-spin" />
                    </div>
                    <h2 className="text-2xl font-bold text-yellow-400">Under Review</h2>
                    <p className="text-white/60 mt-2">
                      Your verification is being processed. You will be notified soon.
                    </p>
                  </>
                ) : (
                  <>
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                      <XCircle size={40} className="text-red-400" />
                    </div>
                    <h2 className="text-2xl font-bold text-red-400">Verification Failed</h2>
                    <p className="text-white/60 mt-2">
                      {result.error || "Please try again with clearer images"}
                    </p>
                    <button
                      onClick={() => {
                        setStep(2);
                        setResult(null);
                      }}
                      className="mt-4 px-6 py-2 bg-purple-500 rounded-lg hover:bg-purple-600 transition"
                    >
                      Try Again
                    </button>
                  </>
                )}
              </motion.div>
            )}
          </div>
        </motion.div>

        {/* Benefits */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-6 bg-white/5 backdrop-blur-sm rounded-xl p-4 border border-white/10"
        >
          <h3 className="text-white font-semibold mb-3 flex items-center gap-2">
            <UserCheck size={18} />
            Benefits of Verification
          </h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="flex items-center gap-2 text-white/60">
              <CheckCircle size={14} className="text-green-400" />
              Increased trust score
            </div>
            <div className="flex items-center gap-2 text-white/60">
              <CheckCircle size={14} className="text-green-400" />
              Verified badge on profile
            </div>
            <div className="flex items-center gap-2 text-white/60">
              <CheckCircle size={14} className="text-green-400" />
              Higher contract limits
            </div>
            <div className="flex items-center gap-2 text-white/60">
              <CheckCircle size={14} className="text-green-400" />
              Priority support
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
