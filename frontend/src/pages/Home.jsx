// src/pages/Home.jsx
import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Link } from "react-router-dom";
import { 
  Brain, 
  Zap, 
  Sparkles, 
  Users, 
  Rocket, 
  Star,
  Shield,
  Cpu,
  Globe,
  Target,
  Award,
  TrendingUp
} from "lucide-react";

export default function Home() {
  const [currentFeature, setCurrentFeature] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
    const interval = setInterval(() => {
      setCurrentFeature((prev) => (prev + 1) % 4);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const features = [
    {
      icon: Brain,
      title: "Neuro-Biometric AI",
      description: "Advanced neural pattern recognition for secure identity verification"
    },
    {
      icon: Shield,
      title: "Military-Grade Security",
      description: "Quantum-resistant encryption and blockchain technology"
    },
    {
      icon: Cpu,
      title: "Real-Time Processing",
      description: "Instant skill matching with <50ms response time"
    },
    {
      icon: Globe,
      title: "Global Network",
      description: "Connect with talents across 150+ countries"
    }
  ];

  const stats = [
    { value: "50K+", label: "Active Users", color: "from-cyan-400 to-blue-500" },
    { value: "99.9%", label: "Accuracy Rate", color: "from-green-400 to-emerald-500" },
    { value: "150+", label: "Countries", color: "from-purple-400 to-pink-500" },
    { value: "2.1M+", label: "Skills Exchanged", color: "from-orange-400 to-red-500" }
  ];

  return (
    <div className="w-full min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-violet-900 overflow-hidden relative font-sans">

      {/* 🔥 Dynamic Particle Background */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Animated Gradient Orbs */}
        <motion.div
          className="absolute w-[800px] h-[800px] bg-gradient-to-r from-cyan-500/10 to-blue-600/10 rounded-full blur-3xl top-[-300px] left-[-200px]"
          animate={{
            x: [0, 100, -80, 0],
            y: [0, 80, -60, 0],
            scale: [1, 1.2, 1],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "easeInOut" }}
        />
        <motion.div
          className="absolute w-[700px] h-[700px] bg-gradient-to-r from-purple-500/10 to-pink-600/10 rounded-full blur-3xl bottom-[-300px] right-[-200px]"
          animate={{
            x: [0, -100, 80, 0],
            y: [0, -80, 60, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{ duration: 25, repeat: Infinity, ease: "easeInOut" }}
        />

        {/* Floating Particles */}
        {[...Array(50)].map((_, i) => (
          <motion.div
            key={i}
            className="absolute w-2 h-2 bg-cyan-400/30 rounded-full"
            initial={{
              x: Math.random() * window.innerWidth,
              y: Math.random() * window.innerHeight,
            }}
            animate={{
              y: [0, -100, 0],
              opacity: [0, 1, 0],
            }}
            transition={{
              duration: Math.random() * 3 + 2,
              repeat: Infinity,
              delay: Math.random() * 2,
            }}
          />
        ))}

        {/* Grid Pattern */}
        <div className="absolute inset-0 bg-linear-gradient(rgba(255,255,255,0.03)_1px bg-transparent_1px) bg-linear-gradient(90deg,rgba(255,255,255,0.03)_1px bg-transparent_1px)bg-[size:50px_50px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,black,transparent)]" />
      </div>

      {/* 🚀 Main Content */}
      <div className="relative z-10">

        {/* 🌟 Hero Section */}
        <section className="min-h-screen flex items-center justify-center px-6 py-20">
          <div className="max-w-7xl mx-auto text-center">
            
            {/* Animated Logo */}
            <motion.div
              className="relative mb-12"
              initial={{ scale: 0, rotate: -180 }}
              animate={{ scale: 1, rotate: 0 }}
              transition={{ duration: 1, type: "spring" }}
            >
              <motion.div
                className="w-40 h-40 mx-auto bg-gradient-to-br from-cyan-400 via-blue-500 to-purple-600 rounded-3xl flex items-center justify-center shadow-2xl shadow-cyan-500/30"
                animate={{ 
                  rotate: [0, 5, -5, 0],
                  scale: [1, 1.05, 1]
                }}
                transition={{ duration: 6, repeat: Infinity }}
              >
                <motion.div
                  className="w-32 h-32 bg-gradient-to-br from-white to-cyan-100 rounded-2xl flex items-center justify-center"
                  animate={{ rotate: [0, -10, 10, 0] }}
                  transition={{ duration: 8, repeat: Infinity }}
                >
                  <Brain className="w-16 h-16 text-cyan-600" />
                </motion.div>
              </motion.div>
              
              {/* Orbiting Elements */}
              {[0, 1, 2].map((i) => (
                <motion.div
                className="absolute w-6 h-6 bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg"
                initial={{ scale: 0 }}
                animate={{
                  scale: 1,
                  rotate: 360,
                  x: Math.cos((i * 2 * Math.PI) / 3) * 120,
                  y: Math.sin((i * 2 * Math.PI) / 3) * 120,
                }}
                transition={{
                  scale: { delay: 0.5 + i * 0.2, duration: 0.6 },
                  rotate: { duration: 8, repeat: Infinity, ease: "linear" },
                  x: { duration: 4, repeat: Infinity, ease: "easeInOut" },
                  y: { duration: 4, repeat: Infinity, ease: "easeInOut" },
                }}
              >
                <Sparkles className="w-3 h-3 text-white" />
              </motion.div>
              ))}
            </motion.div>

            {/* Main Heading */}
            <motion.h1
              className="text-6xl md:text-8xl font-black mb-8"
              initial={{ opacity: 0, y: 50 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.3 }}
            >
              <span className="bg-gradient-to-r from-cyan-300 via-blue-400 to-purple-500 bg-clip-text text-transparent">
                SkillSwap
              </span>
              <br />
              <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                AI Matrix
              </span>
            </motion.h1>

            <motion.div
              className="inline-flex items-center gap-3 bg-white/10 backdrop-blur-lg px-6 py-3 rounded-full border border-white/20 mb-8"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.6 }}
            >
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
              <span className="text-cyan-300 font-semibold">PATENT-READY TECHNOLOGY</span>
              <Award className="w-5 h-5 text-yellow-400" />
            </motion.div>

            <motion.p
              className="text-xl md:text-2xl text-gray-300 max-w-4xl mx-auto leading-relaxed mb-12"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8 }}
            >
              Revolutionizing skill exchange through <span className="text-cyan-300 font-bold">neuro-biometric authentication</span> 
              and <span className="text-purple-300 font-bold">quantum AI processing</span>. 
              Experience the future of talent sharing today.
            </motion.p>

            {/* CTA Buttons */}
            <motion.div
              className="flex flex-col sm:flex-row gap-6 justify-center items-center mb-16"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1 }}
            >
              <Link
                to="/demo"
                className="group relative px-12 py-4 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl font-bold text-white shadow-2xl shadow-cyan-500/30 hover:shadow-cyan-500/50 transition-all duration-300 hover:scale-105"
              >
                <div className="flex items-center gap-3">
                  <Rocket className="w-6 h-6 group-hover:scale-110 transition-transform" />
                  <span>LIVE DEMO</span>
                </div>
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500 to-blue-600 blur-sm opacity-50 group-hover:opacity-70 transition-opacity -z-10" />
              </Link>

              <Link
                to="/register"
                className="px-12 py-4 bg-white/10 backdrop-blur-lg border border-white/20 rounded-2xl font-bold text-white hover:bg-white/20 transition-all duration-300 hover:scale-105"
              >
                GET STARTED FREE
              </Link>
            </motion.div>

            {/* Stats Grid */}
            <motion.div
              className="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto"
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.2 }}
            >
              {stats.map((stat, index) => (
                <motion.div
                  key={index}
                  className="text-center p-6 bg-white/5 backdrop-blur-lg rounded-2xl border border-white/10 hover:border-cyan-400/30 transition-all duration-300"
                  whileHover={{ scale: 1.05, y: -5 }}
                >
                  <div className={`text-3xl font-black bg-gradient-to-r ${stat.color} bg-clip-text text-transparent`}>
                    {stat.value}
                  </div>
                  <div className="text-gray-400 text-sm mt-2">{stat.label}</div>
                </motion.div>
              ))}
            </motion.div>
          </div>
        </section>

        {/* 💫 Features Section */}
        <section className="py-20 px-6">
          <div className="max-w-7xl mx-auto">
            <motion.div
              className="text-center mb-16"
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8 }}
            >
              <h2 className="text-4xl md:text-6xl font-black mb-6">
                <span className="bg-gradient-to-r from-cyan-300 to-purple-400 bg-clip-text text-transparent">
                  Revolutionary
                </span>
                <br />
                <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                  Technology Stack
                </span>
              </h2>
              <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                Powered by cutting-edge AI and blockchain technology for unparalleled security and performance
              </p>
            </motion.div>

            {/* Animated Feature Cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              {features.map((feature, index) => (
                <motion.div
                  key={index}
                  className="relative group"
                  initial={{ opacity: 0, y: 50 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                  whileHover={{ scale: 1.05, y: -10 }}
                >
                  <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/20 to-purple-600/20 rounded-3xl blur-lg group-hover:blur-xl transition-all duration-300" />
                  <div className="relative p-8 bg-slate-900/60 backdrop-blur-lg rounded-3xl border border-white/10 group-hover:border-cyan-400/30 transition-all duration-300 h-full">
                    <motion.div
                      className="w-16 h-16 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center mb-6"
                      animate={{ rotate: [0, 5, -5, 0] }}
                      transition={{ duration: 4, repeat: Infinity }}
                    >
                      <feature.icon className="w-8 h-8 text-white" />
                    </motion.div>
                    <h3 className="text-xl font-bold text-white mb-4">{feature.title}</h3>
                    <p className="text-gray-400 leading-relaxed">{feature.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* 🎯 Interactive Demo Section */}
        <section className="py-20 px-6">
          <div className="max-w-7xl mx-auto">
            <motion.div
              className="bg-gradient-to-br from-slate-800/50 to-purple-900/50 rounded-4xl p-12 backdrop-blur-xl border border-white/10"
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8 }}
            >
              <div className="grid lg:grid-cols-2 gap-12 items-center">
                <div>
                  <h2 className="text-4xl md:text-5xl font-black mb-6">
                    <span className="bg-gradient-to-r from-cyan-300 to-blue-400 bg-clip-text text-transparent">
                      Experience the
                    </span>
                    <br />
                    <span className="bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                      Future Now
                    </span>
                  </h2>
                  <p className="text-xl text-gray-300 mb-8 leading-relaxed">
                    Watch our neuro-biometric AI in action. Real-time skill matching with 
                    unprecedented accuracy and speed that will revolutionize how we exchange knowledge.
                  </p>
                  <div className="flex flex-wrap gap-4">
                    {["Neural Patterns", "Face Recognition", "Voice Biometrics", "Blockchain Security"].map((tech, index) => (
                      <motion.span
                        key={index}
                        className="px-4 py-2 bg-cyan-500/10 border border-cyan-400/30 rounded-full text-cyan-300 text-sm"
                        whileHover={{ scale: 1.1 }}
                      >
                        {tech}
                      </motion.span>
                    ))}
                  </div>
                </div>

                {/* Animated Demo Visual */}
                <motion.div
                  className="relative"
                  animate={{ y: [0, -20, 0] }}
                  transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
                >
                  <div className="relative w-full h-96 bg-gradient-to-br from-cyan-500/10 to-purple-600/10 rounded-3xl border border-white/20 backdrop-blur-lg overflow-hidden">
                    {/* Animated neural network lines */}
                    <svg className="absolute inset-0 w-full h-full">
                      {[...Array(20)].map((_, i) => (
                        <motion.path
                          key={i}
                          d={`M ${Math.random() * 400} ${Math.random() * 300} L ${Math.random() * 400} ${Math.random() * 300}`}
                          stroke="url(#gradient)"
                          strokeWidth="1"
                          fill="none"
                          initial={{ pathLength: 0 }}
                          animate={{ pathLength: 1 }}
                          transition={{ duration: 2, repeat: Infinity, delay: i * 0.1 }}
                        />
                      ))}
                      <defs>
                        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
                          <stop offset="0%" stopColor="#22d3ee" />
                          <stop offset="100%" stopColor="#6366f1" />
                        </linearGradient>
                      </defs>
                    </svg>

                    {/* Floating nodes */}
                    {[...Array(8)].map((_, i) => (
                      <motion.div
                        key={i}
                        className="absolute w-4 h-4 bg-gradient-to-r from-cyan-400 to-blue-500 rounded-full"
                        style={{
                          left: `${20 + (i % 4) * 25}%`,
                          top: `${30 + Math.floor(i / 4) * 30}%`,
                        }}
                        animate={{
                          scale: [1, 1.5, 1],
                          opacity: [0.5, 1, 0.5],
                        }}
                        transition={{
                          duration: 2,
                          repeat: Infinity,
                          delay: i * 0.3,
                        }}
                      />
                    ))}

                    {/* Central brain icon */}
                    <motion.div
                      className="absolute inset-0 flex items-center justify-center"
                      animate={{ rotate: [0, 5, -5, 0] }}
                      transition={{ duration: 8, repeat: Infinity }}
                    >
                      <Brain className="w-20 h-20 text-cyan-400/30" />
                    </motion.div>
                  </div>
                </motion.div>
              </div>
            </motion.div>
          </div>
        </section>

        {/* 🏆 Final CTA Section */}
        <section className="py-20 px-6">
          <motion.div
            className="max-w-4xl mx-auto text-center"
            initial={{ opacity: 0, y: 50 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <motion.div
              className="w-24 h-24 mx-auto mb-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-3xl flex items-center justify-center shadow-2xl shadow-yellow-500/30"
              animate={{ rotate: [0, 360] }}
              transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            >
              <Award className="w-12 h-12 text-white" />
            </motion.div>

            <h2 className="text-4xl md:text-6xl font-black mb-6">
              <span className="bg-gradient-to-r from-yellow-300 to-orange-400 bg-clip-text text-transparent">
                Ready to Revolutionize
              </span>
              <br />
              <span className="bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
                Skill Sharing?
              </span>
            </h2>

            <p className="text-xl text-gray-300 mb-12 max-w-2xl mx-auto">
              Join thousands of innovators already experiencing the future of 
              neuro-biometric skill exchange. Your journey starts here.
            </p>

            <motion.div
              className="flex flex-col sm:flex-row gap-6 justify-center items-center"
              whileInView={{ scale: 1 }}
              initial={{ scale: 0.8 }}
              transition={{ duration: 0.6 }}
            >
              <Link
                to="/register"
                className="group relative px-16 py-5 bg-gradient-to-r from-cyan-500 to-purple-600 rounded-2xl font-black text-white text-lg shadow-2xl shadow-purple-500/30 hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105"
              >
                <span className="relative z-10">START FREE TRIAL</span>
                <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-cyan-500 to-purple-600 blur-lg opacity-50 group-hover:opacity-70 transition-opacity -z-10" />
              </Link>

              <Link
                to="/contact"
                className="px-12 py-5 border-2 border-cyan-400/50 text-cyan-300 rounded-2xl font-bold hover:bg-cyan-400/10 transition-all duration-300 hover:scale-105"
              >
                CONTACT SALES
              </Link>
            </motion.div>
          </motion.div>
        </section>

        {/* 🌐 Footer */}
        <footer className="bg-slate-900/80 backdrop-blur-xl border-t border-white/10 py-12 px-6">
          <div className="max-w-7xl mx-auto">
            <div className="grid md:grid-cols-4 gap-8 mb-8">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-2xl flex items-center justify-center">
                    <Brain className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <div className="font-black text-white text-lg">SkillSwap AI</div>
                    <div className="text-cyan-400 text-xs">PATENT-PENDING</div>
                  </div>
                </div>
                <p className="text-gray-400 text-sm">
                  Revolutionizing skill exchange through advanced neuro-biometric AI technology.
                </p>
              </div>

              {["Product", "Company", "Resources", "Legal"].map((category, index) => (
                <div key={index}>
                  <h3 className="text-white font-bold mb-4">{category}</h3>
                  <ul className="space-y-2 text-sm text-gray-400">
                    {[1, 2, 3].map((item) => (
                      <li key={item}>
                        <Link to="#" className="hover:text-cyan-400 transition-colors">
                          Link {item}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>

            <div className="pt-8 border-t border-white/10 text-center">
              <p className="text-gray-400 text-sm">
                © 2026 SkillSwap AI Matrix. All rights reserved. | Patent-Pending Technology
              </p>
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}
