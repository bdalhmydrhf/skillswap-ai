// src/pages/Exchange.jsx
import React, { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Search, Code, Briefcase, Layers } from "lucide-react";
import api from "../api/axiosConfig";

export default function Exchange() {
  const [skills, setSkills] = useState([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSkills = async () => {
      try {
        const res = await api.get("/skills/");
        setSkills(res.data);
      } catch (err) {
        console.error("Error fetching skills:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSkills();
  }, []);

  const filteredSkills = skills.filter((skill) =>
    skill.name.toLowerCase().includes(query.toLowerCase())
  );

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">جاري تحميل المهارات...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 py-20 px-8">
      {/* 🔹 العنوان الرئيسي */}
      <motion.h1
        className="text-5xl font-extrabold text-center mb-10 text-indigo-700 drop-shadow-md"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        💡 Explore Skills Marketplace
      </motion.h1>

      {/* 🔹 مربع البحث */}
      <div className="flex justify-center mb-12">
        <div className="relative w-full max-w-lg">
          <Search className="absolute left-3 top-3 text-gray-500" />
          <input
            type="text"
            placeholder="Search for a skill..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-2xl border border-indigo-300 shadow-sm focus:ring-2 focus:ring-indigo-400 outline-none"
          />
        </div>
      </div>

      {/* 🔹 عرض المهارات */}
      <motion.div
        className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8"
        initial="hidden"
        animate="visible"
        variants={{
          hidden: {},
          visible: { transition: { staggerChildren: 0.1 } },
        }}
      >
        {filteredSkills.map((skill, index) => (
          <motion.div
            key={skill.id || index}
            className="bg-white shadow-lg rounded-2xl p-6 hover:shadow-xl transition duration-300 border border-indigo-100 relative overflow-hidden"
            whileHover={{ scale: 1.04, rotate: 0.5 }}
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0 },
            }}
          >
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-blue-500"></div>

            {/* 🔸 أيقونة عشوائية لكل مهارة */}
            <div className="flex justify-center mb-4">
              {index % 3 === 0 ? (
                <Code className="text-indigo-500 w-10 h-10" />
              ) : index % 3 === 1 ? (
                <Briefcase className="text-indigo-500 w-10 h-10" />
              ) : (
                <Layers className="text-indigo-500 w-10 h-10" />
              )}
            </div>

            <h3 className="text-xl font-bold text-indigo-700 text-center mb-2">
              {skill.name}
            </h3>
            <p className="text-sm text-gray-600 text-center mb-3">
              {skill.category || "General"}
            </p>
            <p className="text-gray-700 text-center text-sm line-clamp-3">
              {skill.description || "No description available."}
            </p>

            <div className="flex justify-center mt-4">
              <button className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-2 rounded-xl transition">
                View Posts
              </button>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {filteredSkills.length === 0 && (
        <p className="text-center text-gray-500 mt-20">
          No skills found. Try another search 🔍
        </p>
      )}
    </div>
  );
}