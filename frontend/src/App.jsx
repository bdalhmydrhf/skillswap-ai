import React from "react";
import { Routes, Route, NavLink, useLocation, useNavigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute"; 
import { motion } from "framer-motion";
import { LogOut } from "lucide-react";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Contracts from "./pages/Contracts";
import ChatPage from "./pages/ChatPage";
import Profile from "./pages/Profile";
import Dashboard from "./pages/Dashboard";
import Skills from "./pages/Skills";
import BiometricTestPanel from "./Components/BiometricTestPanel";
import DeviceCapabilitiesTest from "./Components/DeviceCapabilitiesTest";
import ContractSignPage from "./pages/ContractSignPage";
import ContractDetailsPage from './pages/ContractDetailsPage';
import IdentityVerification from './pages/IdentityVerification'; 
import SkillPostDetail from "./pages/SkillPostDetail"; 

export default function App() {
  const location = useLocation();
  const navigate = useNavigate();

  const getNavbarColor = () => {
    switch (location.pathname) {
      case "/":
        return "bg-gradient-to-r from-blue-900 via-blue-800 to-blue-700";
      case "/contracts":
        return "bg-gradient-to-r from-purple-700 via-purple-600 to-purple-500";
      case "/dashboard":
        return "bg-gradient-to-r from-gray-800 via-gray-700 to-gray-600";
      case "/skills":
        return "bg-gradient-to-r from-cyan-700 via-cyan-600 to-cyan-500";
      case "/chat/testroom":
        return "bg-gradient-to-r from-teal-700 via-teal-600 to-teal-500";
      case "/profile":
        return "bg-gradient-to-r from-indigo-700 via-indigo-600 to-indigo-500";
      default:
        return "bg-[#1f3c5a]";
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user_email");
    localStorage.removeItem("user");
    navigate("/login");
  };

  const navItems = [
    { to: "/", label: "Home" },
    { to: "/dashboard", label: "Dashboard" },
    { to: "/skills", label: "Skills" },
    { to: "/contracts", label: "Contracts" },
    { to: "/chat/testroom", label: "Chat" },
    { to: "/profile", label: "Profile" },
  ];

  const isAuthenticated = !!localStorage.getItem("access_token");

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <nav className={`fixed top-0 left-0 w-full z-50 ${getNavbarColor()} backdrop-blur-xl border-b border-white/20 shadow-lg transition-all duration-700`}>
        <div className="max-w-7xl mx-auto px-8 py-5 flex items-center justify-between">
          <motion.h1
            className="text-3xl font-extrabold tracking-wider text-white drop-shadow-lg flex items-center gap-2"
            initial={{ opacity: 0, y: -15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7 }}
          >
            SkillSwap AI ⚡
          </motion.h1>

          <div className="hidden md:flex space-x-6 items-center">
            {navItems.map((item) => (
              <motion.div
                key={item.to}
                whileHover={{ scale: 1.12, y: -2, boxShadow: "0 0 16px rgba(255, 255, 255, 0.6)" }}
                transition={{ type: "spring", stiffness: 250 }}
              >
                <NavLink
                  to={item.to}
                  className={({ isActive }) =>
                    `relative px-6 py-2.5 text-sm font-semibold uppercase rounded-full transition-all duration-300 ${
                      isActive
                        ? "bg-white text-[#1f3c5a] shadow-md"
                        : "text-white border border-white/30 hover:text-white/90 hover:border-white/50"
                    }`
                  }
                >
                  {item.label}
                </NavLink>
              </motion.div>
            ))}
{isAuthenticated && (
  <motion.div
    whileHover={{ scale: 1.12, y: -2, boxShadow: "0 0 16px rgba(255, 255, 255, 0.6)" }}
    transition={{ type: "spring", stiffness: 250 }}
  >
    <NavLink
      to="/login"
      onClick={handleLogout}
      className={({ isActive }) =>
        `relative px-6 py-2.5 text-sm font-semibold uppercase rounded-full transition-all duration-300 ${
          isActive
            ? "bg-white text-[#1f3c5a] shadow-md"
            : "text-white border border-white/30 hover:text-white/90 hover:border-white/50"
        }`
      }
    >
      Logout
    </NavLink>
  </motion.div>
)}
          </div>
        </div>
      </nav>

      <main className="flex-1 pt-36 px-4 text-gray-900 transition-all duration-700">
        <Routes>
          {/* الصفحات العامة */}
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/biometric-test" element={<BiometricTestPanel />} />
          <Route path="/device-test" element={<DeviceCapabilitiesTest />} />

          {/* الصفحات المحمية */}
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/contracts" element={<ProtectedRoute><Contracts /></ProtectedRoute>} />
          <Route path="/chat/:roomName" element={<ProtectedRoute><ChatPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/skills" element={<ProtectedRoute><Skills /></ProtectedRoute>} />
          
          {/* ✅ صفحة توقيع العقد */}
          <Route path="/contracts/:contractId/sign" element={<ProtectedRoute><ContractSignPage /></ProtectedRoute>} />
          
          {/* ✅ صفحة تفاصيل العقد */}
          <Route path="/contracts/:contractId/details" element={<ProtectedRoute><ContractDetailsPage /></ProtectedRoute>} />
          <Route path="/skillpost/:id" element={<SkillPostDetail />} />
          {/* ✅✅✅ صفحة التحقق من الهوية بالوثائق ✅✅✅ */}
          <Route path="/verify-identity" element={<ProtectedRoute><IdentityVerification /></ProtectedRoute>} />

        </Routes>
      </main>
    </div>
  );
}
