// src/pages/Register.jsx
import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { FiUser, FiMail, FiLock, FiKey } from "react-icons/fi";
import api from "../api/axiosConfig";
import BiometricEnrollModal from "../components/BiometricEnrollModal";

export default function Register() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    username: "",
    email: "",
    password: "",
    confirmPassword: "",
    pin: "",           // ✅ PIN (8 أرقام)
    confirmPin: "",    // ✅ تأكيد PIN
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [newUserId, setNewUserId] = useState(null);

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // ✅ التحقق من PIN (أرقام فقط، حد أقصى 8)
    if (name === 'pin' || name === 'confirmPin') {
      if (value === '' || /^\d*$/.test(value)) {
        setFormData({ ...formData, [name]: value });
      }
    } else {
      setFormData({ ...formData, [name]: value });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match!");
      return;
    }
    
    // ✅ التحقق من PIN
    if (formData.pin.length !== 8) {
      setError("PIN must be exactly 8 digits!");
      return;
    }
    
    if (formData.pin !== formData.confirmPin) {
      setError("PINs do not match!");
      return;
    }
    
    setLoading(true);
    setError("");
    
    try {
      // 1. تسجيل المستخدم مع PIN
      const registerResponse = await api.post("/register/", {
        username: formData.username,
        email: formData.email,
        password: formData.password,
        pin: formData.pin,  // ✅ إرسال PIN
      });
      
      // 2. تسجيل الدخول تلقائياً
      const loginRes = await api.post("/token/", {
        username: formData.username,
        password: formData.password,
      });
      
      // 3. حفظ التوكن
      localStorage.setItem("access_token", loginRes.data.access);
      localStorage.setItem("refresh_token", loginRes.data.refresh);
      localStorage.setItem("user_email", formData.email);
      
      console.log("API baseURL:", api.defaults.baseURL);
      console.log("Full URL:", api.defaults.baseURL + "users/me/");
      
      // 4. جلب بيانات المستخدم
      const userRes = await api.get("/users/me/");
      localStorage.setItem("user", JSON.stringify(userRes.data));
      
      // 5. فتح نافذة تسجيل البصمة
      setNewUserId(userRes.data.id);
      setShowEnrollModal(true);
      
    } catch (err) {
      setError(err.response?.data?.error || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 via-purple-500 to-pink-500 animate-gradientBackground">
      {/* ====== Navbar ====== */}
      <nav className="fixed top-0 left-0 z-50 w-full border-b shadow-lg backdrop-blur-xl bg-white/10 border-white/20">
        <div className="flex items-center justify-between px-6 py-4 mx-auto max-w-7xl">
          <h1 className="text-2xl font-extrabold tracking-wide text-white md:text-3xl">
            <span className="text-blue-300">Skill</span>
            <span className="text-purple-300">Swap</span> AI ⚡
          </h1>

          <div className="hidden space-x-6 text-sm font-semibold text-white uppercase md:flex">
            <Link to="/" className="transition duration-300 hover:text-yellow-300">Home</Link>
            <Link to="/dashboard" className="transition duration-300 hover:text-yellow-300">Dashboard</Link>
            <Link to="/contracts" className="transition duration-300 hover:text-yellow-300">Contracts</Link>
            <Link to="/chat/testroom" className="transition duration-300 hover:text-yellow-300">Chat</Link>
            <Link to="/profile" className="transition duration-300 hover:text-yellow-300">Profile</Link>
          </div>

          <div className="flex gap-3">
            <Link to="/login" className="px-4 py-2 font-bold text-black transition duration-300 transform rounded-full shadow-lg bg-gradient-to-r from-yellow-400 via-yellow-300 to-yellow-500 hover:scale-105 hover:shadow-xl">
              Sign In
            </Link>
            <Link to="/register" className="px-4 py-2 text-white transition duration-300 border border-white rounded-full hover:bg-white hover:text-blue-700">
              Register
            </Link>
          </div>
        </div>
      </nav>

      {/* ====== Register Form ====== */}
      <div className="flex items-center justify-center min-h-screen pt-20">
        <div className="w-full max-w-md p-10 border shadow-2xl bg-white/20 backdrop-blur-xl rounded-3xl border-white/20 animate-fadeIn">
          <h2 className="mb-8 text-4xl font-extrabold tracking-wide text-center text-white">
            Create Your Account
          </h2>

          {error && <p className="mb-4 text-center text-red-400">{error}</p>}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username */}
            <div className="relative">
              <FiUser className="absolute left-4 top-3.5 text-white/70" size={20} />
              <input
                type="text"
                name="username"
                value={formData.username}
                onChange={handleChange}
                placeholder="Username"
                required
                className="w-full py-3 pl-12 pr-4 text-white transition duration-300 border rounded-2xl border-white/30 bg-white/20 placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-yellow-300 focus:border-yellow-300"
              />
            </div>

            {/* Email */}
            <div className="relative">
              <FiMail className="absolute left-4 top-3.5 text-white/70" size={20} />
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Email Address"
                required
                className="w-full py-3 pl-12 pr-4 text-white transition duration-300 border rounded-2xl border-white/30 bg-white/20 placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-yellow-300 focus:border-yellow-300"
              />
            </div>

            {/* Password */}
            <div className="relative">
              <FiLock className="absolute left-4 top-3.5 text-white/70" size={20} />
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Password"
                required
                className="w-full py-3 pl-12 pr-4 text-white transition duration-300 border rounded-2xl border-white/30 bg-white/20 placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-yellow-300 focus:border-yellow-300"
              />
            </div>

            {/* Confirm Password */}
            <div className="relative">
              <FiLock className="absolute left-4 top-3.5 text-white/70" size={20} />
              <input
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleChange}
                placeholder="Confirm Password"
                required
                className="w-full py-3 pl-12 pr-4 text-white transition duration-300 border rounded-2xl border-white/30 bg-white/20 placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-yellow-300 focus:border-yellow-300"
              />
            </div>

            {/* ✅ PIN (8 digits) */}
            <div className="relative">
              <FiKey className="absolute left-4 top-3.5 text-white/70" size={20} />
              <input
                type="password"
                name="pin"
                value={formData.pin}
                onChange={handleChange}
                placeholder="8-digit Security PIN"
                maxLength="8"
                required
                className="w-full py-3 pl-12 pr-4 text-white transition duration-300 border rounded-2xl border-white/30 bg-white/20 placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-yellow-300 focus:border-yellow-300"
              />
            </div>

            {/* ✅ Confirm PIN */}
            <div className="relative">
              <FiKey className="absolute left-4 top-3.5 text-white/70" size={20} />
              <input
                type="password"
                name="confirmPin"
                value={formData.confirmPin}
                onChange={handleChange}
                placeholder="Confirm 8-digit PIN"
                maxLength="8"
                required
                className="w-full py-3 pl-12 pr-4 text-white transition duration-300 border rounded-2xl border-white/30 bg-white/20 placeholder-white/70 focus:outline-none focus:ring-2 focus:ring-yellow-300 focus:border-yellow-300"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 font-bold text-black transition duration-300 transform rounded-full shadow-lg bg-gradient-to-r from-yellow-400 via-yellow-300 to-yellow-500 hover:scale-105 hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed mt-6"
            >
              {loading ? "Registering..." : "Sign Up"}
            </button>
          </form>

          <p className="mt-6 text-center text-white">
            Already have an account?{" "}
            <Link to="/login" className="font-semibold text-blue-200 transition hover:text-yellow-300">
              Sign In
            </Link>
          </p>
        </div>
      </div>

      {/* نافذة تسجيل البصمة */}
      {showEnrollModal && (
        <BiometricEnrollModal
          onSuccess={() => navigate("/dashboard")}
          onClose={() => navigate("/dashboard")}
          userId={newUserId}
        />
      )}

      {/* Animations CSS */}
      <style>
        {`
          @keyframes gradientBackground {
            0% {background-position: 0% 50%;}
            50% {background-position: 100% 50%;}
            100% {background-position: 0% 50%;}
          }
          .animate-gradientBackground {
            background-size: 400% 400%;
            animation: gradientBackground 15s ease infinite;
          }
          @keyframes fadeIn {
            from {opacity: 0; transform: translateY(20px);}
            to {opacity: 1; transform: translateY(0);}
          }
          .animate-fadeIn {
            animation: fadeIn 0.8s ease forwards;
          }
        `}
      </style>
    </div>
  );
}

