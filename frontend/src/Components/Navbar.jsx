// src/components/Navbar.jsx
import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Navbar() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <nav className="fixed top-0 left-0 z-50 w-full border-b shadow-lg backdrop-blur-xl bg-white/10 border-white/20">
      <div className="flex items-center justify-between px-6 py-4 mx-auto max-w-7xl">
        {/* Logo */}
        <Link to="/">
          <h1 className="text-2xl font-extrabold tracking-wide text-white md:text-3xl">
            <span className="text-blue-300">Skill</span>
            <span className="text-purple-300">Swap</span> AI ⚡
          </h1>
        </Link>

        {/* Links - تظهر فقط للمستخدم المسجل */}
        <div className="hidden space-x-6 text-sm font-semibold text-white uppercase md:flex">
          <Link to="/" className="transition duration-300 hover:text-yellow-300">
            Home
          </Link>
          {isAuthenticated && (
            <>
              <Link to="/dashboard" className="transition duration-300 hover:text-yellow-300">
                Dashboard
              </Link>
              <Link to="/contracts" className="transition duration-300 hover:text-yellow-300">
                Contracts
              </Link>
              <Link to="/chat/testroom" className="transition duration-300 hover:text-yellow-300">
                Chat
              </Link>
              <Link to="/profile" className="transition duration-300 hover:text-yellow-300">
                Profile
              </Link>
            </>
          )}
        </div>

        {/* Auth Buttons */}
        <div className="flex gap-3">
          {isAuthenticated ? (
            <>
              <span className="px-4 py-2 text-white">
                👋 {user?.username}
              </span>
              <button
                onClick={handleLogout}
                className="px-4 py-2 text-white transition duration-300 border border-white rounded-full hover:bg-white hover:text-blue-700"
              >
                Logout
              </button>
            </>
          ) : (
            <>
              <Link
                to="/login"
                className="px-4 py-2 font-bold text-black transition duration-300 transform rounded-full shadow-lg bg-gradient-to-r from-yellow-400 via-yellow-300 to-yellow-500 hover:scale-105 hover:shadow-xl"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="px-4 py-2 text-white transition duration-300 border border-white rounded-full hover:bg-white hover:text-blue-700"
              >
                Register
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
