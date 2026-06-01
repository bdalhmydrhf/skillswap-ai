// src/Components/DeviceCapabilitiesTest.jsx
import React, { useState, useEffect, useRef } from 'react';
import DeviceCapabilityDetector from '../utils/deviceCapabilities';
import axios from 'axios';
import SignatureCanvas from 'react-signature-canvas';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Camera, Mic, FileSignature, Shield, Zap, Brain, Cpu, UserCheck,
  Star, Award, Target
} from 'lucide-react';

export default function DeviceCapabilitiesTest() {
  // States متقدمة
  const [methods, setMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeMethod, setActiveMethod] = useState(null); // 'face' | 'voice' | 'signature' | null
  const [result, setResult] = useState(null);
  const [capturedPhoto, setCapturedPhoto] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [systemStats, setSystemStats] = useState({
    totalScans: 0,
    successRate: 0,
    avgResponseTime: 0,
    securityLevel: 'HIGH'
  });
  const [scanHistory, setScanHistory] = useState([]);

  // Refs
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const sigCanvas = useRef(null);

  // User ID ذكي
  const [userId] = useState(() => {
    const storedId = localStorage.getItem('biometric_user_id');
    if (!storedId) {
      const newId = 'user_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('biometric_user_id', newId);
      return newId;
    }
    return storedId;
  });

  // تهيئة النظام
  useEffect(() => {
    initializeSystem();
    loadUserProfile();
    // cleanup on unmount
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(t => t.stop());
      }
    };
  }, []);

  const initializeSystem = async () => {
    try {
      const availableMethods = await DeviceCapabilityDetector.detectAvailableMethods();
      setMethods(availableMethods);
      
      const stats = JSON.parse(localStorage.getItem('system_stats') || '{"totalScans":0,"successRate":0,"avgResponseTime":0,"securityLevel":"HIGH"}');
      setSystemStats(stats);
      
      const history = JSON.parse(localStorage.getItem('scan_history') || '[]');
      setScanHistory(history);
      
    } catch (error) {
      console.error('Error initializing system:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadUserProfile = () => {
    const profile = JSON.parse(localStorage.getItem('user_profile_' + userId) || 'null');
    setUserProfile(profile);
  };

  const saveUserProfile = (profile) => {
    localStorage.setItem('user_profile_' + userId, JSON.stringify(profile));
    setUserProfile(profile);
  };

  const updateSystemStats = (success, responseTime, quality = 0) => {
    const newTotalScans = systemStats.totalScans + 1;
    const prevSumSuccesses = (systemStats.successRate / 100) * systemStats.totalScans;
    const newSuccessRate = ((prevSumSuccesses + (success ? 1 : 0)) / newTotalScans) * 100;

    const newAvgResponse = systemStats.avgResponseTime === 0
      ? responseTime
      : Math.round(((systemStats.avgResponseTime * systemStats.totalScans) + responseTime) / newTotalScans);

    const newStats = {
      totalScans: newTotalScans,
      successRate: Number(newSuccessRate.toFixed(1)),
      avgResponseTime: isNaN(newAvgResponse) ? 0 : newAvgResponse,
      securityLevel: systemStats.securityLevel
    };
    
    setSystemStats(newStats);
    localStorage.setItem('system_stats', JSON.stringify(newStats));

    // إضافة للمحفوظات
    const newScan = {
      id: Date.now(),
      method: activeMethod,
      success: success,
      timestamp: new Date().toISOString(),
      responseTime: responseTime,
      quality: quality
    };
    
    const updatedHistory = [newScan, ...scanHistory.slice(0, 9)];
    setScanHistory(updatedHistory);
    localStorage.setItem('scan_history', JSON.stringify(updatedHistory));
  };

  // ---------------------------
  // FACE: start camera & capture
  // ---------------------------
  const startFaceAuth = async () => {
    try {
      setResult(null);
      setCapturedPhoto(null);

      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'user',
          width: { ideal: 1280 },
          height: { ideal: 720 }
        } 
      });
      
      streamRef.current = mediaStream;
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
      setActiveMethod('face');
      
    } catch (error) {
      alert('لا يمكن الوصول للكاميرا: ' + error.message);
      console.error(error);
    }
  };

  // helper: safely get video dimensions (fallback if 0)
  const getVideoDimensions = (videoEl) => {
    const w = videoEl && videoEl.videoWidth ? videoEl.videoWidth : 640;
    const h = videoEl && videoEl.videoHeight ? videoEl.videoHeight : 480;
    return { w, h };
  };

  const captureAndAnalyze = async () => {
    if (!videoRef.current) {
      alert('الكاميرا غير جاهزة');
      return;
    }

    const startTime = performance.now();

    try {
      setLoading(true);
      
      // ensure we have sensible width/height (some browsers return 0 initially)
      const { w, h } = getVideoDimensions(videoRef.current);

      const canvas = document.createElement('canvas');
      canvas.width = w;
      canvas.height = h;
      
      const ctx = canvas.getContext('2d');
      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';
      // draw current frame
      ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
      
      const photoDataUrl = canvas.toDataURL('image/jpeg', 0.9);
      setCapturedPhoto(photoDataUrl);

      // إرسال البيانات للتحليل (backend يجب أن يدعم endpoint هذا)
      const response = await axios.post('http://127.0.0.1:8000/api/biometric/process/', {
        user_id: userId,
        modalities: {
          face: photoDataUrl
        },
        context: {
          device_type: "advanced_browser_camera",
          location: "secure_system",
          resolution: canvas.width + 'x' + canvas.height
        }
      }, { timeout: 15000 });

      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);

      // backend قد يعيد quality_scores, adaptive_profile, security_level
      const faceQuality = response.data.quality_scores ? (response.data.quality_scores.face || 0) : 0;

      const resultData = {
        ...response.data,
        performance: {
          responseTime,
          imageSize: Math.round(photoDataUrl.length / 1024) + ' KB',
          resolution: canvas.width + 'x' + canvas.height
        }
      };

      setResult(resultData);

      // save profile if returned
      if (response.data.adaptive_profile) {
        saveUserProfile(response.data.adaptive_profile);
      }

      updateSystemStats(true, responseTime, faceQuality);
      
      // show quality message (use response's score if present, else estimate)
      const scoreToShow = faceQuality || estimateImageQuality(photoDataUrl);
      showQualityFeedback(scoreToShow);

    } catch (error) {
      console.error('Analysis error:', error);
      updateSystemStats(false, 0, 0);
      alert('فشل في التحليل — تأكدي من اتصال السيرفر أو شغّل الـ backend.');
    } finally {
      setLoading(false);
    }
  };

  const estimateImageQuality = (dataUrl) => {
    // بسيط: طول الصورة يقدّر جودة (فقط كـ fallback)
    if (!dataUrl) return 0;
    const sizeKB = dataUrl.length / 1024;
    if (sizeKB > 150) return 0.85;
    if (sizeKB > 60) return 0.55;
    return 0.25;
  };

  const showQualityFeedback = (qualityScore) => {
    let message = '';
    let emoji = '';
    
    if (qualityScore > 0.7) {
      message = 'ممتاز! جودة عالية جداً - النظام يتذكرك بشكل مثالي';
      emoji = '🎯';
    } else if (qualityScore > 0.4) {
      message = 'جيدة - النظام يتعلم منك ويتحسن';
      emoji = '📈';
    } else {
      message = 'منخفضة - حاولي تحسين الإضاءة والوضوح';
      emoji = '💡';
    }
    
    setTimeout(() => {
      alert(emoji + ' ' + message);
    }, 300);
  };

  // ---------------------------
  // VOICE: record or simulate
  // ---------------------------
  const startVoiceAuth = async () => {
    try {
      setResult(null);
      setActiveMethod('voice');

      const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
      // We intentionally stop after short record — backend will analyze a sample
      setTimeout(async () => {
        mediaStream.getTracks().forEach(track => track.stop());
        await simulateVoiceAnalysis();
      }, 2000);
      
    } catch (error) {
      alert('لا يمكن الوصول للميكروفون: ' + (error.message || error));
      console.error(error);
    }
  };

  const simulateVoiceAnalysis = async () => {
    try {
      setLoading(true);
      const startTime = performance.now();

      // For demo: send a lightweight mock sample string (backend should accept)
      const response = await axios.post('http://127.0.0.1:8000/api/biometric/process/', {
        user_id: userId,
        modalities: {
          voice: "voice_sample_simulated_" + Date.now()
        },
        context: {
          device_type: "browser_microphone"
        }
      }, { timeout: 15000 });

      const endTime = performance.now();
      const responseTime = Math.round(endTime - startTime);

      const voiceQuality = response.data.quality_scores ? (response.data.quality_scores.voice || 0.5) : 0.5;

      setResult({
        ...response.data,
        performance: { responseTime }
      });

      updateSystemStats(true, responseTime, voiceQuality);

    } catch (error) {
      console.error('Voice analysis error:', error);
      updateSystemStats(false, 0, 0);
      alert('خطأ في تحليل الصوت — تفقد السيرفر.');
    } finally {
      setLoading(false);
      setActiveMethod(null);
    }
  };

  // ---------------------------
  // SIGNATURE: draw + send
  // ---------------------------
  const startSignatureAuth = async () => {
    setResult(null);
    setCapturedPhoto(null);
    setActiveMethod('signature');
    // signature UI will appear — user can draw then press "تحليل التوقيع"
  };

  const clearSignature = () => {
    if (sigCanvas.current) sigCanvas.current.clear();
  };

  const analyzeSignature = async () => {
    if (!userId) {
      alert('⚠ يرجى إدخال معرف المستخدم أولاً (على اليمين أعلى)');
      return;
    }
    if (!sigCanvas.current || sigCanvas.current.isEmpty()) {
      alert('⚠ الرجاء رسم توقيعك داخل المربع أولاً');
      return;
    }

    const points = sigCanvas.current.toData();
    const signatureData = {
      points,
      timestamps: points.map((_, i) => i * 0.1)
    };

    setLoading(true);
    try {
      const startTime = performance.now();
      const res = await axios.post('http://127.0.0.1:8000/api/biometric/process/', {
        user_id: userId,
        modalities: { signature: signatureData },
        context: { device_type: "browser_signature", location: "frontend_test" }
      }, { timeout: 15000 });
      const endTime = performance.now();

      const signatureQuality = res.data.quality_scores ? (res.data.quality_scores.signature || 0.5) : 0.5;
      setResult({
        ...res.data,
        performance: { responseTime: Math.round(endTime - startTime) }
      });

      updateSystemStats(true, Math.round(endTime - startTime), signatureQuality);

    } catch (err) {
      console.error(err);
      updateSystemStats(false, 0, 0);
      alert('حدث خطأ أثناء الاتصال بالـ API — راجعي الكونسول للمزيد من التفاصيل');
    } finally {
      setLoading(false);
    }
  };

  // أدوات مساعدة
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setActiveMethod(null);
    setCapturedPhoto(null);
  };

  const resetSystem = () => {
    stopCamera();
    setResult(null);
    setCapturedPhoto(null);
    if (sigCanvas.current) sigCanvas.current.clear();
  };

  const getQualityColor = (score) => {
    if (score > 0.7) return 'text-green-400';
    if (score > 0.4) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getSecurityBadge = (level) => {
    const badges = {
      'عالي جداً': { color: 'bg-red-500', text: '🛡 عالي جداً' },
      'عالي': { color: 'bg-green-500', text: '✅ عالي' },
      'متوسط': { color: 'bg-yellow-500', text: '⚠ متوسط' },
      'منخفض': { color: 'bg-orange-500', text: '🔶 منخفض' }
    };
    return badges[level] || badges['متوسط'];
  };

  if (loading && !activeMethod) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 to-purple-900">
        <div className="text-center text-white">
          <motion.div
            animate={{ rotate: 360, scale: [1, 1.2, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="w-20 h-20 border-4 border-blue-400 border-t-transparent rounded-full mx-auto mb-4"
          />
          <h2 className="text-2xl font-bold mb-2">جاري تحميل النظام المتقدم</h2>
          <p className="text-blue-200">نظام المصادقة البيومترية الذكي</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 to-blue-900 text-white">
      {/* الهيدر */}
      <header className="bg-black/40 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <motion.div
                whileHover={{ rotate: 360 }}
                className="w-12 h-12 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center"
              >
                <Brain className="w-6 h-6" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                  NeuroBio AI System
                </h1>
                <p className="text-sm text-gray-400">نظام المصادقة البيومترية الذكي</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              <div className="text-right mr-4">
                <p className="text-sm text-gray-400">ID: {userId.slice(0, 8)}...</p>
                <p className="text-xs text-green-400">🟢 متصل</p>
              </div>
              <div className="bg-white/6 rounded-xl px-3 py-2 text-black/80">
                <input
                  type="text"
                  placeholder="User ID (optional)"
                  className="bg-transparent outline-none text-sm text-white placeholder-gray-300"
                  value={userId}
                  readOnly
                />
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* إحصائيات سريعة */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
        >
          <div className="bg-white/10 rounded-2xl p-4 text-center backdrop-blur-lg">
            <Cpu className="w-8 h-8 text-blue-400 mx-auto mb-2" />
            <p className="text-2xl font-bold">{systemStats.totalScans}</p>
            <p className="text-sm text-gray-400">المسحات</p>
          </div>
          
          <div className="bg-white/10 rounded-2xl p-4 text-center backdrop-blur-lg">
            <Zap className="w-8 h-8 text-green-400 mx-auto mb-2" />
            <p className="text-2xl font-bold">{systemStats.successRate.toFixed(1)}%</p>
            <p className="text-sm text-gray-400">الناجحة</p>
          </div>
          
          <div className="bg-white/10 rounded-2xl p-4 text-center backdrop-blur-lg">
            <Shield className="w-8 h-8 text-purple-400 mx-auto mb-2" />
            <p className="text-2xl font-bold">{systemStats.securityLevel}</p>
            <p className="text-sm text-gray-400">الأمان</p>
          </div>
          
          <div className="bg-white/10 rounded-2xl p-4 text-center backdrop-blur-lg">
            <UserCheck className="w-8 h-8 text-orange-400 mx-auto mb-2" />
            <p className="text-2xl font-bold">{userProfile ? '✅' : '🆕'}</p>
            <p className="text-sm text-gray-400">الملف</p>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* المنطقة الرئيسية */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-lg rounded-3xl p-6 border border-white/10"
            >
              <h2 className="text-3xl font-bold mb-6 text-center bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                نظام المصادقة المتقدم
              </h2>

              {/* واجهة الكاميرا */}
              <AnimatePresence>
                {activeMethod === 'face' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mb-6"
                  >
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <p className="text-sm text-gray-400 mb-2 text-center">📹 الكاميرا المباشرة</p>
                        <div className="relative rounded-xl overflow-hidden border-2 border-blue-500">
                          <video 
                            ref={videoRef}
                            autoPlay 
                            playsInline
                            className="w-full h-64 object-cover"
                          />
                          <div className="absolute top-2 left-2 bg-red-500 px-2 py-1 rounded text-xs">
                            🔴 مباشر
                          </div>
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-sm text-gray-400 mb-2 text-center">
                          {capturedPhoto ? '📸 صورتك الملتقطة' : '🖼 ستظهر صورتك هنا'}
                        </p>
                        <div className="w-full h-64 rounded-xl border-2 border-dashed border-green-500 bg-black/20 flex items-center justify-center">
                          {capturedPhoto ? (
                            <motion.img 
                              initial={{ scale: 0.8 }}
                              animate={{ scale: 1 }}
                              src={capturedPhoto} 
                              alt="صورتك" 
                              className="w-full h-full object-cover rounded-xl"
                            />
                          ) : (
                            <div className="text-center text-gray-500">
                              <Camera className="w-12 h-12 mx-auto mb-2" />
                              <p>إضغطي لإلتقاط</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-3 justify-center mb-3">
                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={captureAndAnalyze}
                        disabled={loading}
                        className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-bold disabled:opacity-50"
                      >
                        {loading ? (
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            جاري التحليل...
                          </div>
                        ) : (
                          '📸 إلتقاط وتحليل'
                        )}
                      </motion.button>
                      
                      <button 
                        onClick={stopCamera}
                        className="px-6 py-3 bg-gradient-to-r from-red-500 to-pink-600 text-white rounded-xl font-bold"
                      >
                        🛑 إيقاف
                      </button>
                    </div>

                    {capturedPhoto && (
                      <div className="text-center">
                        <p className="text-sm text-green-400">
                          👆 صورتك جاهزة! تأكدي من وضوحها ثم إضغطي "إلتقاط وتحليل"
                        </p>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>

              {/* واجهة الصوت */}
              <AnimatePresence>
                {activeMethod === 'voice' && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center py-8"
                  >
                    <motion.div
                      animate={{ scale: [1, 1.1, 1] }}
                      transition={{ duration: 2, repeat: Infinity }}
                      className="text-4xl mb-4"
                    >
                      🎙
                    </motion.div>
                    <h3 className="text-xl font-bold mb-2">التعرف الصوتي</h3>
                    <p className="text-gray-400 mb-4">جاري التحضير للتسجيل...</p>
                    <div className="flex justify-center space-x-1">
                      {[1, 2, 3].map((i) => (
                        <motion.div
                          key={i}
                          animate={{ height: [20, 40, 20] }}
                          transition={{ duration: 1, repeat: Infinity, delay: i * 0.2 }}
                          className="w-3 bg-blue-500 rounded-full"
                        />
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* واجهة التوقيع الرقمي */}
              <AnimatePresence>
                {activeMethod === 'signature' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="mb-6"
                  >
                    <div className="text-center mb-4">
                      <h3 className="text-xl font-bold">✍ التوقيع الرقمي</h3>
                      <p className="text-gray-400">ارسم توقيعك داخل المربع ثم اضغط "تحليل التوقيع" لإرساله للخادم</p>
                    </div>

                    <div className="border-2 border-dashed rounded-2xl bg-black/20 p-3 mb-3">
                      <SignatureCanvas
                        ref={sigCanvas}
                        penColor="white"
                        backgroundColor="transparent"
                        canvasProps={{ width: 700, height: 220, className: "rounded-xl" }}
                      />
                    </div>

                    <div className="flex gap-3 justify-center mb-3">
                      <button onClick={clearSignature} className="px-6 py-2 bg-gray-300 text-black rounded-lg">🧹 مسح</button>
                      <button onClick={analyzeSignature} disabled={loading} className="px-6 py-2 bg-gradient-to-r from-indigo-600 to-indigo-500 text-white rounded-lg">
                        {loading ? '⏳ جاري التحليل...' : '🔍 تحليل التوقيع'}
                      </button>
                      <button onClick={() => { setActiveMethod(null); }} className="px-6 py-2 bg-red-500 text-white rounded-lg">🔙 خروج</button>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* طرق المصادقة */}
              <div className="grid grid-cols-1 gap-4">
                {methods.map((method, index) => {
                  const details = DeviceCapabilityDetector.getMethodDetails(method);
                  return (
                    <motion.div
                      key={method}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      whileHover={{ scale: 1.02 }}
                      className="bg-white/10 rounded-2xl p-4 border border-white/10 hover:border-blue-500/30 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="text-3xl">
                            {details.icon}
                          </div>
                          <div>
                            <h3 className="font-bold text-lg">{details.name}</h3>
                            <p className="text-gray-400 text-sm">{details.description}</p>
                            <p className="text-xs text-gray-500 mt-1">مستوى أمان: {details.security}</p>
                          </div>
                        </div>
                        
                        <motion.button
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                          onClick={() => {
                            if (method === 'face') startFaceAuth();
                            else if (method === 'voice') startVoiceAuth();
                            else if (method === 'hand_drawing') startSignatureAuth();
                          }}
                          disabled={activeMethod !== null}
                          className="px-6 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg font-semibold disabled:opacity-30"
                        >
                          {activeMethod ? '⚡ نشط...' : '🚀 تفعيل'}
                        </motion.button>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </motion.div>
          </div>

          {/* لوحة النتائج */}
          <div>
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="bg-white/5 backdrop-blur-lg rounded-3xl p-6 border border-white/10 h-full"
            >
              <h3 className="text-xl font-bold mb-6 text-center">📈 نتائج التحليل</h3>
              
              <AnimatePresence>
                {result && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="space-y-4"
                  >
                    {/* النتائج الرئيسية */}
                    <div className="bg-gradient-to-r from-green-500/20 to-blue-500/20 rounded-2xl p-4 border border-green-500/30">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-green-400 font-bold">✅ تحليل ناجح</span>
                        <Award className="w-5 h-5 text-yellow-400" />
                      </div>
                      
                      {result.quality_scores && (
                        <div className="mb-2">
                          <div className="flex justify-between text-sm">
                            <span>الجودة:</span>
                            <span className={getQualityColor(Object.values(result.quality_scores)[0] || 0)}>
                              {((Object.values(result.quality_scores)[0] || 0) * 100).toFixed(1)}%
                            </span>
                          </div>
                          <div className="w-full bg-gray-700 rounded-full h-2 mt-1">
                            <div 
                              className="bg-green-500 h-2 rounded-full transition-all"
                              style={{ width: ((Object.values(result.quality_scores)[0] || 0) * 100) + '%' }}
                            />
                          </div>
                        </div>
                      )}

                      {!result.quality_scores && (
                        <div className="text-sm text-gray-300">لا توجد بيانات جودة — السيرفر لم يعِد quality_scores.</div>
                      )}
                    </div>

                    {/* معلومات الأداء */}
                    {result.performance && (
                      <div className="bg-black/30 rounded-2xl p-4">
                        <h4 className="font-bold mb-3 flex items-center gap-2">
                          <Zap className="w-4 h-4" />
                          الأداء
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>الوقت:</span>
                            <span>{result.performance.responseTime}ms</span>
                          </div>
                          {result.performance.imageSize && (
                            <div className="flex justify-between">
                              <span>حجم الصورة:</span>
                              <span>{result.performance.imageSize}</span>
                            </div>
                          )}
                          {result.performance.resolution && (
                            <div className="flex justify-between">
                              <span>الدقة:</span>
                              <span>{result.performance.resolution}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* التعلم التكيفي */}
                    {result.adaptive_profile && (
                      <div className="bg-purple-500/10 rounded-2xl p-4 border border-purple-500/20">
                        <h4 className="font-bold mb-3 flex items-center gap-2">
                          <Brain className="w-4 h-4" />
                          التعلم التكيفي
                        </h4>
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span>مرات التكيف:</span>
                            <span className="text-blue-400">{result.adaptive_profile.adaptation_count}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>مستوى الثقة:</span>
                            <span className="text-green-400">{(result.user_confidence ? result.user_confidence : 0) * 100}%</span>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* الأمان */}
                    {result.security_level && (
                      <div className="bg-yellow-500/10 rounded-2xl p-4 border border-yellow-500/20">
                        <h4 className="font-bold mb-2">🛡 مستوى الأمان</h4>
                        <div className={'px-3 py-1 rounded-full text-sm text-center ' + (getSecurityBadge(result.security_level).color)}>
                          {getSecurityBadge(result.security_level).text}
                        </div>
                      </div>
                    )}

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={resetSystem}
                      className="w-full py-3 bg-gradient-to-r from-gray-600 to-gray-700 rounded-2xl font-bold"
                    >
                      🔄 مسح والبدء من جديد
                    </motion.button>
                  </motion.div>
                )}
              </AnimatePresence>

              {!result && (
                <div className="text-center py-12 text-gray-500">
                  <Target className="w-16 h-16 mx-auto mb-4 opacity-50" />
                  <p>النتائج ستظهر هنا</p>
                  <p className="text-sm mt-2">بعد إجراء المسح البيومتري</p>
                </div>
              )}
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
}
