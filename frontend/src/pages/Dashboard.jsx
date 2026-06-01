// src/pages/Dashboard.jsx
import React, { useEffect, useState, useCallback } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import {
  ChartPie,
  UserCheck,
  FileSignature,
  MessageSquare,
  Bell,
  Shield,
  Globe,
} from "lucide-react";
import Particles from "@tsparticles/react";
import { loadSlim } from "@tsparticles/slim";
import api from "../api/axiosConfig";

const BACKEND_URL = "http://127.0.0.1:8001";

export default function Dashboard() {
  const [user, setUser] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);
  
  // ✅ State for FAISS section
  const [faissData, setFaissData] = useState(null);
  const [faissLoading, setFaissLoading] = useState(false);

  // ✅ State for Session Activity section
  const [locationData, setLocationData] = useState({ city: null, country: null, type: 'home' });
  const [loginTime, setLoginTime] = useState('');
  const [sessionDuration, setSessionDuration] = useState('00:00:00');

  // ✅ Fetch data function
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch user data
      const userRes = await api.get("/users/me/");
      let userData = userRes.data;
      
      if (userData.profile_image && !userData.profile_image.startsWith('http')) {
        userData.profile_image = `${BACKEND_URL}${userData.profile_image}`;
      }
      if (userData.cover_image && !userData.cover_image.startsWith('http')) {
        userData.cover_image = `${BACKEND_URL}${userData.cover_image}`;
      }
      
      setUser(userData);
      
      // Fetch contracts
      const contractsRes = await api.get("/contracts/");
      console.log("Contracts response:", contractsRes.data);
      
      let contractsData = [];
      if (Array.isArray(contractsRes.data)) {
        contractsData = contractsRes.data;
      } else if (contractsRes.data && Array.isArray(contractsRes.data.results)) {
        contractsData = contractsRes.data.results;
      } else if (contractsRes.data && typeof contractsRes.data === 'object') {
        console.log("⚠️ API returned object instead of array:", contractsRes.data);
        contractsData = [];
      }
      
      setContracts(contractsData);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      setContracts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // ✅ Fetch FAISS data function
  const fetchFaissData = useCallback(async () => {
    setFaissLoading(true);
    try {
      const response = await api.get("/faiss-demo/");
      setFaissData(response.data);
    } catch (error) {
      console.error("Error fetching FAISS data:", error);
      setFaissData(null);
    } finally {
      setFaissLoading(false);
    }
  }, []);

  // ✅ Fetch location data function
  const fetchLocationData = async () => {
    try {
      const response = await fetch('https://ipapi.co/json/');
      const data = await response.json();
      setLocationData({
        city: data.city,
        country: data.country_name,
        type: 'home'
      });
    } catch (error) {
      console.error("Error fetching location:", error);
    }
  };

  // ✅ useEffect to fetch data on initial load and refreshKey change
  useEffect(() => {
    document.title = "SkillSwap AI Dashboard";
    fetchData();
    fetchFaissData();
    fetchLocationData();
    
    // Login time
    const loginTimestamp = localStorage.getItem('login_timestamp');
    if (loginTimestamp) {
      const date = new Date(parseInt(loginTimestamp));
      setLoginTime(date.toLocaleTimeString('en-US'));
    } else {
      const now = new Date();
      setLoginTime(now.toLocaleTimeString('en-US'));
      localStorage.setItem('login_timestamp', now.getTime().toString());
    }
  }, [fetchData, fetchFaissData, refreshKey]);

  // ✅ Timer to calculate session duration
  useEffect(() => {
    const interval = setInterval(() => {
      const loginTimeMs = parseInt(localStorage.getItem('login_timestamp') || Date.now().toString());
      const durationMs = Date.now() - loginTimeMs;
      const hours = Math.floor(durationMs / 3600000);
      const minutes = Math.floor((durationMs % 3600000) / 60000);
      const seconds = Math.floor((durationMs % 60000) / 1000);
      setSessionDuration(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    }, 1000);
    
    return () => clearInterval(interval);
  }, []);

  // ✅ Auto-refresh when a new contract is signed (localStorage)
  useEffect(() => {
    const handleStorageChange = (e) => {
      if (e.key === 'dashboard-refresh') {
        console.log("🔄 Contract updated, refreshing...");
        setRefreshKey(prev => prev + 1);
      }
    };
    
    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-100 to-purple-100">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Loading data...</p>
        </div>
      </div>
    );
  }

  const profileImageUrl = user?.profile_image 
    ? `${user.profile_image}?t=${Date.now()}` 
    : "https://i.pravatar.cc/40";

  const trustLevel = user?.trust_score || 0;
  const activeContracts = Array.isArray(contracts) 
    ? contracts.filter((c) => c.status === "active" || c.status === "Active").length 
    : 0;
  const totalContracts = Array.isArray(contracts) ? contracts.length : 0;

  const pieData = [
    { name: "Trust", value: trustLevel },
    { name: "Remaining", value: 100 - trustLevel },
  ];
  const COLORS = ["#6366F1", "#E5E7EB"];

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      transition: { delay: i * 0.15, duration: 0.6, type: "spring", stiffness: 100 },
    }),
  };

  const particlesInit = async (main) => {
    await loadSlim(main);
  };

  const latestContracts = Array.isArray(contracts) ? contracts.slice(0, 5) : [];

  // ✅ Determine FAISS status
  const isFaissWorking = faissData?.success === true;

  return (
    <div className="relative min-h-screen overflow-hidden">
      <motion.div
        className="absolute inset-0 bg-gradient-to-tr from-indigo-400 via-purple-400 to-pink-400 animate-gradient-x"
        style={{ zIndex: -2 }}
      />
      <Particles
        id="tsparticles"
        init={particlesInit}
        options={{
          fullScreen: { enable: false },
          background: { color: { value: "transparent" } },
          fpsLimit: 60,
          interactivity: {
            events: { onHover: { enable: true, mode: "repulse" } },
            modes: { repulse: { distance: 100 } },
          },
          particles: {
            color: { value: "#ffffff" },
            links: { enable: true, color: "#ffffff", distance: 120 },
            move: { enable: true, speed: 1, outModes: "bounce" },
            number: { value: 50 },
            opacity: { value: 0.4 },
            size: { value: { min: 2, max: 4 } },
          },
        }}
        className="absolute inset-0 z-0"
      />

      <header className="flex items-center justify-between px-8 py-5 bg-white bg-opacity-70 backdrop-blur-lg shadow-xl rounded-b-2xl relative z-10">
        <h1 className="text-2xl md:text-3xl font-extrabold text-indigo-700 drop-shadow-md">
          🌟 SkillSwap AI Dashboard
        </h1>
        <div className="flex items-center gap-4">
          <motion.div whileHover={{ scale: 1.2 }} className="cursor-pointer">
            <Bell className="text-gray-500 hover:text-indigo-600 transition" />
          </motion.div>
          <Link to="/profile">
            <motion.img
              whileHover={{ scale: 1.15 }}
              src={profileImageUrl}
              alt={user?.username}
              className="w-10 h-10 rounded-full border-2 border-indigo-200 shadow-md cursor-pointer object-cover"
              onError={(e) => {
                console.error("❌ Image failed to load:", profileImageUrl);
                e.target.src = "https://i.pravatar.cc/40";
              }}
            />
          </Link>
        </div>
      </header>

      <main className="p-8 space-y-8 relative z-10">
        <div className="grid gap-6 md:grid-cols-3">
          {/* Trust Level Card */}
          <motion.div
            custom={0}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
            whileHover={{
              scale: 1.06,
              boxShadow: "0 20px 40px rgba(99,102,241,0.5)",
            }}
            className="p-6 bg-gradient-to-tr from-indigo-100 via-purple-100 to-pink-100 rounded-3xl shadow-xl flex flex-col items-center"
          >
            <div className="flex items-center justify-between w-full mb-2">
              <h2 className="font-semibold text-gray-700">AI Trust Level</h2>
              <Shield className="text-indigo-500" />
            </div>
            <div className="w-32 h-32 md:w-40 md:h-40">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={50}
                    outerRadius={70}
                    startAngle={90}
                    endAngle={-270}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
            </div>
            <motion.p
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.4, type: "spring", stiffness: 120 }}
              className="text-3xl md:text-4xl font-bold text-indigo-700 mt-2"
            >
              {trustLevel}%
            </motion.p>
            <p className="text-sm text-gray-500 mt-1 text-center">
              Analyzing user credibility and behavior
            </p>
          </motion.div>

          {/* Active Contracts Card */}
          <motion.div
            custom={1}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
            whileHover={{
              scale: 1.06,
              boxShadow: "0 20px 40px rgba(139,92,246,0.5)",
            }}
            className="p-6 bg-gradient-to-tr from-purple-100 via-purple-200 to-purple-300 rounded-3xl shadow-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-700">Active Contracts</h2>
              <FileSignature className="text-purple-500" />
            </div>
            <div className="w-full bg-purple-200 rounded-full h-5 overflow-hidden">
              <motion.div
                className="bg-purple-600 h-5 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: totalContracts > 0 ? `${(activeContracts / totalContracts) * 100}%` : "0%" }}
                transition={{ duration: 1.2, ease: "easeInOut" }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">
              {activeContracts} Active / {totalContracts} Total
            </p>
          </motion.div>

          {/* Total Contracts Card */}
          <motion.div
            custom={2}
            initial="hidden"
            animate="visible"
            variants={cardVariants}
            whileHover={{
              scale: 1.06,
              boxShadow: "0 20px 40px rgba(34,197,94,0.5)",
            }}
            className="p-6 bg-gradient-to-tr from-green-100 via-green-200 to-green-300 rounded-3xl shadow-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-gray-700">Total Contracts</h2>
              <ChartPie className="text-green-500" />
            </div>
            <p className="text-3xl md:text-4xl font-bold text-green-700">
              {totalContracts}
            </p>
            <p className="text-sm text-gray-500 mt-1">All registered contracts</p>
          </motion.div>
        </div>

        {/* ============================================================
            ✅✅✅ Current Session Activity Section (FIXED COLORS) ✅✅✅
            ============================================================ */}
        <div className="bg-white/20 backdrop-blur-lg rounded-2xl p-6 mb-6 border border-indigo-200">
          <h3 className="text-xl font-bold text-indigo-800 mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5 text-indigo-600" />
            Current Session Activity
          </h3>
          
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100">
              <p className="text-indigo-500 text-xs font-medium">Estimated Location</p>
              <p className="text-gray-700 font-semibold">
                {locationData?.city || "Detecting..."}, 
                {locationData?.country || ""}
              </p>
            </div>
            
            <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100">
              <p className="text-indigo-500 text-xs font-medium">Location Type</p>
              <p className="text-gray-700 font-semibold">
                {locationData?.type === 'home' ? '🏠 Home' : 
                 locationData?.type === 'work' ? '💼 Work' : '📍 Public'}
              </p>
            </div>
            
            <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100">
              <p className="text-indigo-500 text-xs font-medium">Login Time</p>
              <p className="text-gray-700 font-semibold">{loginTime}</p>
            </div>
            
            <div className="bg-indigo-50 rounded-xl p-3 border border-indigo-100">
              <p className="text-indigo-500 text-xs font-medium">Session Duration</p>
              <p className="text-gray-700 font-semibold">{sessionDuration}</p>
            </div>
          </div>
        </div>

        {/* ✅ FAISS AI Recommendations Card */}
        <motion.div
          custom={4}
          initial="hidden"
          animate="visible"
          variants={cardVariants}
          whileHover={{ scale: 1.02 }}
          className="p-6 bg-gradient-to-tr from-purple-100 via-pink-100 to-rose-100 rounded-3xl shadow-xl"
        >
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                <span className="text-white text-sm">🤖</span>
              </div>
              <h2 className="font-semibold text-gray-700">FAISS AI Recommendations</h2>
            </div>
            <div className={`px-2 py-1 text-xs rounded-full font-semibold ${
              isFaissWorking ? 'bg-green-500 text-white' : 'bg-yellow-500 text-white'
            }`}>
              {faissLoading ? 'Loading...' : (isFaissWorking ? '✅ ACTIVE' : '⏳ READY')}
            </div>
          </div>
          
          {faissLoading ? (
            <div className="text-center py-6">
              <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              <p className="text-sm text-gray-500">Loading AI recommendations...</p>
            </div>
          ) : isFaissWorking ? (
            <div>
              <div className="bg-white/50 rounded-xl p-4 mb-3">
                <p className="text-green-700 font-semibold text-center">
                  ✅ FAISS is WORKING!
                </p>
                <p className="text-xs text-gray-500 text-center mt-1">
                  Fast similarity search engine active
                </p>
              </div>
              {faissData?.recommendations && faissData.recommendations.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm text-gray-600 font-medium">🎯 Similar users found:</p>
                  {faissData.recommendations.slice(0, 3).map((rec, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-white/50 rounded-lg px-3 py-2">
                      <span className="text-gray-700 text-sm">User #{rec.user_id || rec.id}</span>
                      <span className="text-purple-600 text-xs font-semibold">Similarity: {rec.similarity || 'high'}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : (
            <div className="bg-white/50 rounded-xl p-4 text-center">
              <p className="text-gray-600">⚙️ FAISS engine is ready</p>
              <p className="text-xs text-gray-400 mt-1">Will activate as you interact with the platform</p>
            </div>
          )}
          
          <p className="text-xs text-gray-400 mt-3 text-center border-t border-white/30 pt-3">
            Powered by Facebook AI Similarity Search (FAISS) • {isFaissWorking ? 'Active' : 'Standby'} Mode
          </p>
        </motion.div>

        {/* Latest Contracts */}
        <motion.div
          custom={5}
          initial="hidden"
          animate="visible"
          variants={cardVariants}
          whileHover={{ scale: 1.02 }}
          className="p-6 bg-white rounded-3xl shadow-xl"
        >
          <h3 className="mb-4 text-xl md:text-2xl font-semibold text-gray-700">
            🧾 Latest Contracts
          </h3>
          {latestContracts.length === 0 ? (
            <p className="text-gray-500 text-center py-4">No contracts yet</p>
          ) : (
            <ul className="divide-y divide-gray-200">
              {latestContracts.map((c) => (
                <motion.li
                  key={c.id}
                  whileHover={{ scale: 1.03, backgroundColor: "#f3f4f6" }}
                  className="flex items-center justify-between py-3 rounded-lg px-2 transition-all"
                >
                  <span className="font-medium text-gray-700">{c.title}</span>
                  <span
                    className={`px-3 py-1 text-sm rounded-full font-semibold ${
                      c.status === "active" || c.status === "Active"
                        ? "bg-green-200 text-green-800"
                        : c.status === "pending"
                        ? "bg-yellow-200 text-yellow-800"
                        : "bg-gray-200 text-gray-800"
                    }`}
                  >
                    {c.status === "active" ? "Active" : c.status === "pending" ? "Pending" : c.status}
                  </span>
                </motion.li>
              ))}
            </ul>
          )}
        </motion.div>

        {/* Quick Links */}
        <div className="grid gap-6 md:grid-cols-3">
          <motion.div
            whileHover={{
              scale: 1.05,
              boxShadow: "0 15px 35px rgba(99,102,241,0.4)",
            }}
            className="p-6 bg-indigo-600 text-white rounded-3xl shadow-lg flex items-center justify-between transition-all animate-pulse"
          >
            <Link to="/contracts" className="w-full flex items-center justify-between">
              Manage Contracts <FileSignature />
            </Link>
          </motion.div>

          <motion.div
            whileHover={{
              scale: 1.05,
              boxShadow: "0 15px 35px rgba(139,92,246,0.4)",
            }}
            className="p-6 bg-purple-600 text-white rounded-3xl shadow-lg flex items-center justify-between transition-all animate-pulse"
          >
            <Link to="/chat/testroom" className="w-full flex items-center justify-between">
              Instant Chat <MessageSquare />
            </Link>
          </motion.div>

          <motion.div
            whileHover={{
              scale: 1.05,
              boxShadow: "0 15px 35px rgba(34,197,94,0.4)",
            }}
            className="p-6 bg-green-600 text-white rounded-3xl shadow-lg flex items-center justify-between transition-all animate-pulse"
          >
            <Link to="/profile" className="w-full flex items-center justify-between">
              Profile <UserCheck />
            </Link>
          </motion.div>
        </div>
      </main>
    </div>
  );
}