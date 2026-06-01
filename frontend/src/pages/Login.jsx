// src/pages/Login.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Eye, EyeOff, Loader2 } from "lucide-react";
import api from "../api/axiosConfig";
import BiometricModal from "../components/BiometricModal";

export default function Login() {
  const navigate = useNavigate();
  const [emailOrUsername, setEmailOrUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showBiometric, setShowBiometric] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    
    // ✅ استخراج username من الإيميل (إذا كان إيميل) أو استخدام النص كما هو
    let usernameValue = emailOrUsername;
    if (emailOrUsername.includes('@')) {
      usernameValue = emailOrUsername.split('@')[0];
    }
    
    console.log("🔍 Input:", emailOrUsername);
    console.log("🔍 Username being sent:", usernameValue);
    console.log("🔍 BaseURL:", api.defaults.baseURL);
    console.log("🔍 Full URL:", api.defaults.baseURL + "token/");
    
    try {
      const response = await api.post("/token/", { 
        username: usernameValue, 
        password: password 
      });
      
      localStorage.setItem("access_token", response.data.access);
      localStorage.setItem("refresh_token", response.data.refresh);
      localStorage.setItem("user_email", emailOrUsername);
      
      // جلب بيانات المستخدم وحفظها
      const userRes = await api.get("/users/me/");
      localStorage.setItem("user", JSON.stringify(userRes.data));
      window.location.href = "/dashboard";
    
    } catch (err) {
      console.error("Login error:", err.response?.data);
      setError(err.response?.data?.detail || "فشل تسجيل الدخول");
    } finally {
      setLoading(false);
    }
  };

  const handleBiometricSuccess = (data) => {
    console.log("✅ Biometric data:", data); // للتأكد
    
    // حفظ التوكن
    if (data.access) {
      localStorage.setItem("access_token", data.access);
    }
    if (data.refresh) {
      localStorage.setItem("refresh_token", data.refresh);
    }
    
    // حفظ بيانات المستخدم
    if (data.user_id) {
      localStorage.setItem("user_id", data.user_id);
    }
    if (data.username) {
      localStorage.setItem("username", data.username);
    }
    
    localStorage.setItem("user_email", emailOrUsername);
    localStorage.setItem("user", JSON.stringify({ 
      id: data.user_id, 
      username: data.username || emailOrUsername.split('@')[0] 
    }));
    
    // ✅ استخدم navigate بدل window.location
    window.location.href = "/dashboard";
  };

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-gradient-to-br from-blue-700 via-indigo-600 to-purple-700 relative overflow-hidden text-white">
      {/* دوائر متحركة خفيفة بالخلفية */}
      <motion.div
        className="absolute w-96 h-96 bg-purple-400/30 rounded-full blur-3xl top-10 left-10"
        animate={{ x: [0, 60, -60, 0], y: [0, 40, -40, 0] }}
        transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute w-80 h-80 bg-blue-400/30 rounded-full blur-3xl bottom-10 right-10"
        animate={{ x: [0, -60, 60, 0], y: [0, -40, 40, 0] }}
        transition={{ duration: 18, repeat: Infinity, ease: "easeInOut" }}
      />

      {/* صندوق تسجيل الدخول */}
      <motion.div
        className="relative z-10 bg-white/10 backdrop-blur-md border border-white/20 rounded-2xl shadow-xl p-10 w-[90%] max-w-md text-center"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 1 }}
      >
        <h2 className="text-3xl font-bold mb-6">Welcome Back 👋</h2>

        {error && (
          <div className="mb-4 p-2 bg-red-500/20 border border-red-500 rounded-lg text-red-200 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-left text-sm text-blue-100 mb-1">Username or Email</label>
            <input
              type="text"
              value={emailOrUsername}
              onChange={(e) => setEmailOrUsername(e.target.value)}
              placeholder="Enter your username or email"
              className="w-full px-4 py-2 rounded-lg bg-white/20 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-300"
              required
            />
          </div>

          <div>
            <label className="block text-left text-sm text-blue-100 mb-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2 rounded-lg bg-white/20 text-white placeholder-white/60 focus:outline-none focus:ring-2 focus:ring-blue-300 pr-10"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2 text-white/70 hover:text-white"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-white text-blue-700 font-semibold py-2 rounded-lg hover:bg-blue-100 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="w-5 h-5 animate-spin" />}
            {loading ? "Logging in.." : "Sign In"}
          </button>
        </form>

        <div className="relative my-4">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-white/30"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-transparent text-gray-300">or</span>
          </div>
        </div>

        <button
          onClick={() => setShowBiometric(true)}
          className="w-full py-2 rounded-lg border border-white/30 text-white hover:bg-white/10 transition"
        >
          🔐Biometric Login
        </button>

        <p className="mt-5 text-sm text-blue-100">
          Don’t have an account?{" "}
          <Link to="/register" className="text-white font-semibold hover:underline">
            Register
          </Link>
        </p>
      </motion.div>

      {showBiometric && (
        <BiometricModal
          onSuccess={handleBiometricSuccess}
          onClose={() => setShowBiometric(false)}
          purpose="login"
        />
      )}
    </div>
  );
}
