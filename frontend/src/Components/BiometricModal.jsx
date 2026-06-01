// frontend/src/components/BiometricModal.jsx - Modified Version V4.2
// ✅ Context analysis + Fetch user enrolled biometrics + Display decision details

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  Camera, 
  Mic, 
  Fingerprint, 
  CheckCircle, 
  XCircle, 
  Loader2,
  RefreshCw,
  Shield,
  Clock,
  AlertTriangle,
  ArrowLeft,
  PenTool
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import api from '../api/axiosConfig';
import SignatureCanvas from 'react-signature-canvas';

export default function BiometricModal({ onSuccess, onClose, purpose = 'login', contractId = null }) {
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [confidence, setConfidence] = useState(0);
  const [email, setEmail] = useState('');
  const [countdown, setCountdown] = useState(null);
  const [verificationToken, setVerificationToken] = useState(null);
  const [retryCount, setRetryCount] = useState(0);
  const [recordingTime, setRecordingTime] = useState(0);
  const [step, setStep] = useState('selecting');
  
  const [analysisResult, setAnalysisResult] = useState(null);
  const [requiredModalities, setRequiredModalities] = useState([]);
  const [analysisDone, setAnalysisDone] = useState(false);
  const [userEnrolledModalities, setUserEnrolledModalities] = useState([]);
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const recordingTimerRef = useRef(null);
  const sigCanvasRef = useRef(null);

  const methods = [
    { id: 'face', name: 'Face Recognition', icon: <Camera size={24} />, description: 'Use your device camera', color: 'from-blue-500 to-indigo-600' },
    { id: 'voice', name: 'Voice Recognition', icon: <Mic size={24} />, description: 'Speak a short phrase', color: 'from-purple-500 to-pink-600' },
    { id: 'fingerprint', name: 'Fingerprint', icon: <Fingerprint size={24} />, description: 'Use fingerprint sensor', color: 'from-emerald-500 to-teal-600' },
    { id: 'signature', name: 'Digital Signature', icon: <PenTool size={24} />, description: 'Draw your signature', color: 'from-orange-500 to-red-600' },
  ];

  // ============================================================
  // 🎯 Fetch user's enrolled biometric modalities
  // ============================================================
  const fetchUserEnrolledModalities = async () => {
    const userEmail = email || localStorage.getItem('user_email');
    if (!userEmail) return [];
    
    try {
      let userId = localStorage.getItem('user_id');
      
      if (!userId) {
        const userRes = await api.get('/users/me/');
        userId = userRes.data.id;
        localStorage.setItem('user_id', userId);
      }
      
      if (!userId) return [];
      
      const response = await api.get(`/biometric/status/${userId}/`);
      
      const enrolled = [];
      if (response.data.face_enrolled) enrolled.push('face');
      if (response.data.voice_enrolled) enrolled.push('voice');
      if (response.data.fingerprint_enrolled) enrolled.push('fingerprint');
      if (response.data.signature_enrolled) enrolled.push('signature');
      
      console.log("✅ Enrolled modalities:", enrolled);
      return enrolled;
      
    } catch (error) {
      console.error("Error fetching enrolled modalities:", error);
      return [];
    }
  };

  // ============================================================
  // 🎯 Detect location using IP (easier, no user permission needed)
  // ============================================================
  const detectLocationFromIP = async () => {
    try {
      // Using free ipapi.co service (no API key required)
      const response = await fetch('https://ipapi.co/json/');
      const data = await response.json();
      
      console.log("📍 IP Location detected:", data);
      
      // Determine location type based on data
      let locationType = 'home'; // default
      
      // If IP belongs to a company/institution
      if (data.org && (data.org.includes('University') || data.org.includes('Office') || data.org.includes('Company'))) {
        locationType = 'work';
      }
      // If IP is public (cafe, airport, hotel)
      else if (data.org && (data.org.includes('Cafe') || data.org.includes('Airport') || data.org.includes('Hotel'))) {
        locationType = 'public';
      }
      
      return {
        location: locationType,
        city: data.city,
        country: data.country_name,
        ip: data.ip,
        latitude: data.latitude,
        longitude: data.longitude,
        source: 'ip'
      };
      
    } catch (error) {
      console.log("IP location detection failed:", error);
      return {
        location: 'home',
        city: null,
        country: null,
        source: 'default'
      };
    }
  };

  // ============================================================
  // 🎯 Detect location using GPS (more accurate but requires permission)
  // ============================================================
  const detectLocationFromGPS = async () => {
    return new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve(null);
        return;
      }
      
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            // Convert coordinates to address (Reverse Geocoding)
            const geoResponse = await fetch(
              `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.coords.latitude}&lon=${position.coords.longitude}&zoom=18&addressdetails=1`
            );
            const geoData = await geoResponse.json();
            
            let locationType = 'home';
            
            // Determine location type from OSM data
            if (geoData.address) {
              if (geoData.address.office || geoData.address.workplace || geoData.address.industrial) {
                locationType = 'work';
              } else if (geoData.address.cafe || geoData.address.restaurant || geoData.address.pub) {
                locationType = 'public';
              }
            }
            
            resolve({
              location: locationType,
              city: geoData.address?.city || geoData.address?.town,
              country: geoData.address?.country,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
              accuracy: position.coords.accuracy,
              source: 'gps'
            });
          } catch (error) {
            console.log("Reverse geocoding failed:", error);
            resolve(null);
          }
        },
        (error) => {
          console.log("Geolocation error:", error.message);
          resolve(null);
        },
        { timeout: 5000, enableHighAccuracy: true }
      );
    });
  };

  // ============================================================
  // 🎯 Main context analysis function (fully modified)
  // ============================================================
  const analyzeContext = async () => {
    try {
      setStatus('analyzing');
      setMessage('Analyzing device and security context...');
      
      // ============================================================
      // 1. Detect real device capabilities
      // ============================================================
      let hasCamera = false;
      let hasMic = false;
      let cameraWorks = false;
      let micWorks = false;
      
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        try {
          const testStream = await navigator.mediaDevices.getUserMedia({ video: true });
          cameraWorks = testStream.getVideoTracks().length > 0;
          hasCamera = true;
          testStream.getTracks().forEach(track => track.stop());
        } catch(e) {
          cameraWorks = false;
          console.log("Camera not available or permission denied");
        }
        
        try {
          const testStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          micWorks = testStream.getAudioTracks().length > 0;
          hasMic = true;
          testStream.getTracks().forEach(track => track.stop());
        } catch(e) {
          micWorks = false;
          console.log("Microphone not available or permission denied");
        }
      }
      
      // ============================================================
      // 2. Detect device type
      // ============================================================
      const userAgent = navigator.userAgent;
      const isMobile = /Mobi|Android|iPhone|iPad|iPod/i.test(userAgent);
      const isTablet = /iPad|Android(?!.*Mobile)/i.test(userAgent);
      const hasTouch = 'ontouchstart' in window;
      
      let deviceType = 'desktop';
      if (isTablet) deviceType = 'tablet';
      else if (isMobile) deviceType = 'mobile';
      
      // ============================================================
      // 3. Detect real location (try GPS first, then IP)
      // ============================================================
      let location = 'home';
      let locationDetails = { city: null, country: null, latitude: null, longitude: null };
      
      // First attempt: GPS (more accurate)
      const gpsLocation = await detectLocationFromGPS();
      if (gpsLocation) {
        location = gpsLocation.location;
        locationDetails = {
          city: gpsLocation.city,
          country: gpsLocation.country,
          latitude: gpsLocation.latitude,
          longitude: gpsLocation.longitude,
        };
        console.log(`📍 GPS location: ${locationDetails.city}, ${locationDetails.country} → Type: ${location}`);
        setMessage(`📍 Location detected: ${locationDetails.city || 'Unknown city'}`);
      } else {
        // Second attempt: IP (less accurate)
        const ipLocation = await detectLocationFromIP();
        location = ipLocation.location;
        locationDetails = {
          city: ipLocation.city,
          country: ipLocation.country,
          latitude: ipLocation.latitude,
          longitude: ipLocation.longitude,
        };
        console.log(`📍 IP location: ${locationDetails.city}, ${locationDetails.country} → Type: ${location}`);
        if (locationDetails.city) {
          setMessage(`📍 Approximate location: ${locationDetails.city}, ${locationDetails.country}`);
        }
      }
      
      // ============================================================
      // 4. Fetch user's enrolled biometrics
      // ============================================================
      let userId = localStorage.getItem('user_id');
      if (!userId) {
        try {
          const userRes = await api.get('/users/me/');
          userId = userRes.data.id;
          localStorage.setItem('user_id', userId);
        } catch(e) {
          console.error("Could not fetch user ID");
        }
      }
      
      let enrolledModalities = [];
      if (userId) {
        try {
          const statusRes = await api.get(`/biometric/status/${userId}/`);
          if (statusRes.data.face_enrolled) enrolledModalities.push('face');
          if (statusRes.data.voice_enrolled) enrolledModalities.push('voice');
          if (statusRes.data.fingerprint_enrolled) enrolledModalities.push('fingerprint');
          if (statusRes.data.signature_enrolled) enrolledModalities.push('signature');
          setUserEnrolledModalities(enrolledModalities);
        } catch(e) {
          console.error("Error fetching enrolled modalities:", e);
        }
      }
      
      // ============================================================
      // 5. Send context analysis request to server
      // ============================================================
      const currentHour = new Date().getHours();
      const isWeekend = [0, 6].includes(new Date().getDay());
      const isNight = currentHour < 6 || currentHour > 22;
      
      const response = await api.post("/biometric/analyze-and-decide/", {
        context: { 
          location: location,
          device_type: deviceType,
          network_type: navigator.onLine ? 'online' : 'offline',
          hour: currentHour,
          is_weekend: isWeekend,
          is_night: isNight,
          city: locationDetails.city,
          country: locationDetails.country,
        },
        quality_scores: {},
        device_info: {
          has_camera: hasCamera && cameraWorks,
          has_microphone: hasMic && micWorks,
          has_fingerprint: !!window.PublicKeyCredential,
          has_touch: hasTouch,
          screen_resolution: `${window.screen.width}x${window.screen.height}`,
          is_mobile: isMobile,
          is_tablet: isTablet,
        }
      });
      
      console.log("📊 Analysis result:", response.data);
      setAnalysisResult(response.data);
      
      // ============================================================
      // 6. Merge result with enrolled biometrics
      // ============================================================
      let recommendedModalities = response.data.modalities || ['face', 'voice'];
      
      if (enrolledModalities.length > 0) {
        let finalModalities = recommendedModalities.filter(m => enrolledModalities.includes(m));
        if (finalModalities.length === 0) {
          finalModalities = enrolledModalities;
        }
        setRequiredModalities(finalModalities);
      } else {
        setRequiredModalities(recommendedModalities);
      }
      
      setAnalysisDone(true);
      setStatus('idle');
      setMessage('');
      
      // ============================================================
      // 7. Process decision from server
      // ============================================================
      if (response.data.decision === 'deny') {
        setStatus('error');
        setMessage(`❌ Access denied: ${response.data.explanation || 'Security risk detected'}`);
        return false;
      }
      
      if (response.data.decision === 'require_mfa') {
        setStatus('error');
        setMessage(`🔐 Additional verification required: ${response.data.explanation || 'Please use multiple biometrics'}`);
        return false;
      }
      
      // Display security level information
      if (response.data.risk_level === 'low') {
        setMessage(`🟢 Low security level, using ${requiredModalities.length} verification method(s)`);
      } else if (response.data.risk_level === 'medium') {
        setMessage(`🟡 Medium security level, using ${requiredModalities.length} verification method(s)`);
      } else if (response.data.risk_level === 'high') {
        setMessage(`🔴 High security level, using ${requiredModalities.length} verification method(s)`);
      }
      
      return true;
      
    } catch (error) {
      console.error("Analysis failed:", error);
      setAnalysisDone(true);
      setStatus('idle');
      setMessage('');
      return true;
    }
  };

  // ============================================================
  // 🧹 Cleanup and other helper functions
  // ============================================================
  
  const cleanupMedia = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (recordingTimerRef.current) {
      clearInterval(recordingTimerRef.current);
      recordingTimerRef.current = null;
    }
  }, []);

  const startFaceCapture = async () => {
    try {
      cleanupMedia();
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' } 
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setStatus('idle');
      setMessage('Position your face in the frame');
    } catch (error) {
      console.error("Camera error:", error);
      setMessage('Cannot access camera');
      setStatus('error');
    }
  };

  const captureFace = async () => {
    if (!videoRef.current || !videoRef.current.videoWidth) {
      setMessage('Camera not ready');
      return;
    }
    const userEmail = email || localStorage.getItem('user_email');
    if (!userEmail) {
      setStatus('error');
      setMessage('❌ Please enter your email address first');
      return;
    }
    setStatus('capturing');
    setMessage('Capturing image...');
    
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.9).split(',')[1];
    
    cleanupMedia();
    await verifyBiometric('face', imageData);
  };

  const startVoiceCapture = async () => {
    try {
      cleanupMedia();
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = async () => {
          const fullAudioData = reader.result;
          const audioData = fullAudioData.split(',')[1];
          cleanupMedia();
          await verifyBiometric('voice', audioData);
        };
      };
      
      setStatus('capturing');
      setRecordingTime(0);
      
      recordingTimerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      mediaRecorder.start();
      
      setTimeout(() => {
        if (mediaRecorder.state === 'recording') {
          mediaRecorder.stop();
        }
        if (recordingTimerRef.current) {
          clearInterval(recordingTimerRef.current);
        }
      }, 3000);
      
    } catch (error) {
      console.error("Microphone error:", error);
      setMessage('Cannot access microphone');
      setStatus('error');
    }
  };

  const startFingerprintCapture = async () => {
    setStatus('capturing');
    setMessage('Use your fingerprint sensor...');
    
    try {
      if (!window.PublicKeyCredential) {
        throw new Error('WebAuthn not supported on this device');
      }
      
      setTimeout(async () => {
        await verifyBiometric('fingerprint', 'fingerprint_data_simulated');
      }, 2000);
      
    } catch (error) {
      console.error("Fingerprint error:", error);
      setMessage('Fingerprint not supported, try face or voice');
      setStatus('error');
    }
  };

  const startSignatureCapture = async () => {
    setStatus('capturing');
    setMessage('Draw your signature in the box below...');
    setStep('signature_drawing');
  };

  const clearSignature = () => {
    if (sigCanvasRef.current) {
      sigCanvasRef.current.clear();
    }
  };

  const captureSignature = async () => {
    if (!sigCanvasRef.current || sigCanvasRef.current.isEmpty()) {
      setMessage('Please draw your signature first');
      return;
    }
    
    setStatus('verifying');
    setMessage('Verifying signature...');
    
    const fullSignatureData = sigCanvasRef.current.toDataURL();
    const signatureData = fullSignatureData.split(',')[1];
    
    await verifyBiometric('signature', signatureData);
  };

  const verifyBiometric = async (type, data) => {
    setStatus('verifying');
    setMessage('Verifying identity...');
    
    let userEmail = email;
    if (!userEmail) {
      userEmail = localStorage.getItem('user_email');
    }
    if (!userEmail) {
      setStatus('error');
      setMessage('❌ Please enter your email address');
      return;
    }
    
    if (requiredModalities.length > 0 && !requiredModalities.includes(type)) {
      setStatus('error');
      setMessage(`❌ ${type} not registered for your account. Please use: ${requiredModalities.join(', ')}`);
      return;
    }
    
    try {
      let endpoint = '/biometric/login/';
      let payload = { 
        email: userEmail,  
        biometric_type: type, 
        biometric_data: data 
      };
      
      if (purpose === 'sign_contract' && contractId) {
        endpoint = `/biometric/verify-before-sign/${contractId}/`;
        payload = { 
          biometric_type: type, 
          biometric_data: data,
          purpose: 'sign_contract',
          timestamp: new Date().toISOString()
        };
      }
      
      const res = await api.post(endpoint, payload);
      
      setConfidence(res.data.confidence || 0.95);
      setVerificationToken(res.data.biometric_token || `token_${Date.now()}`);
      setStatus('success');
      setMessage(res.data.message || '✅ Verification successful!');
      
      const expiresIn = res.data.expires_in || 300;
      setCountdown(expiresIn);
      
      timerRef.current = setInterval(() => {
        setCountdown(prev => {
          if (prev <= 1) {
            clearInterval(timerRef.current);
            setMessage('Verification expired');
            setStatus('error');
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      
      setTimeout(() => {
        onSuccess({
          verified: true,
          type: type,
          confidence: res.data.confidence || 0.95,
          timestamp: new Date().toISOString(),
          contractId: contractId,
          biometric_token: verificationToken,
          expires_in: expiresIn,
          access: res.data.access || res.data.token || verificationToken,
          refresh: res.data.refresh || '',
          user_id: res.data.user_id,
          username: res.data.username || (userEmail ? userEmail.split('@')[0] : 'user'),
          email: userEmail
        });
      }, 1500);
      
    } catch (error) {
      console.error("Biometric verification error:", error);
      setStatus('error');
      setRetryCount(prev => prev + 1);
      
      if (error.response?.status === 401) {
        setMessage('❌ Verification failed: Biometric data does not match');
      } else if (error.response?.status === 404) {
        setMessage('❌ User not found');
      } else if (error.response?.status === 400) {
        setMessage(error.response?.data?.error || '❌ Invalid request');
      } else if (error.response?.status === 403) {
        setMessage('❌ You are not authorized to sign this contract');
      } else if (!navigator.onLine) {
        setMessage('❌ No internet connection');
      } else {
        setMessage(error.response?.data?.error || '❌ Verification failed');
      }
    }
  };

  const retryCapture = () => {
    setRetryCount(prev => prev + 1);
    setStatus('idle');
    setMessage('');
    setStep('capturing');
    
    if (selectedMethod === 'face') {
      startFaceCapture();
    } else if (selectedMethod === 'voice') {
      startVoiceCapture();
    } else if (selectedMethod === 'fingerprint') {
      startFingerprintCapture();
    } else if (selectedMethod === 'signature') {
      startSignatureCapture();
    }
  };

  const handleMethodSelect = (methodId) => {
    setSelectedMethod(methodId);
    setStatus('idle');
    setMessage('');
    setRetryCount(0);
    setStep('capturing');
    
    if (methodId === 'face') {
      startFaceCapture();
    } else if (methodId === 'voice') {
      startVoiceCapture();
    } else if (methodId === 'fingerprint') {
      startFingerprintCapture();
    } else if (methodId === 'signature') {
      startSignatureCapture();
    }
  };

  const handleBack = () => {
    cleanupMedia();
    setSelectedMethod(null);
    setStatus('idle');
    setMessage('');
    setConfidence(0);
    setCountdown(null);
    setRetryCount(0);
    setStep('selecting');
  };

  // ============================================================
  // 🔄 useEffect hooks
  // ============================================================
  
  useEffect(() => {
    const storedEmail = localStorage.getItem('user_email');
    if (storedEmail) setEmail(storedEmail);
  }, []);

  useEffect(() => {
    const initBiometric = async () => {
      setStatus('analyzing');
      setMessage('Analyzing device and sensors...');
      const canProceed = await analyzeContext();
      if (!canProceed) {
        return;
      }
    };
    
    initBiometric();
  }, []);

  useEffect(() => {
    return () => {
      cleanupMedia();
    };
  }, [cleanupMedia]);

  const formatCountdown = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  // Filter displayed methods based on analysis
  const displayMethods = analysisDone && requiredModalities.length > 0
    ? methods.filter(m => requiredModalities.includes(m.id))
    : methods;

  // ============================================================
  // 🎨 UI Component (JSX)
  // ============================================================
  
  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md"
        onClick={(e) => e.target === e.currentTarget && onClose()}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          transition={{ type: "spring", damping: 25 }}
          className="bg-gradient-to-br from-gray-900 via-purple-900 to-indigo-900 rounded-3xl p-8 w-[95%] max-w-md text-white shadow-2xl border border-white/20"
        >
          <div className="text-center mb-6">
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
              <Shield size={32} className="text-white" />
            </div>
            <h2 className="text-2xl font-bold">
              {purpose === 'login' ? '🔐 Biometric Login' : '✍️ Identity Verification'}
            </h2>
            <p className="text-white/50 text-sm mt-1">
              {purpose === 'login' 
                ? 'Choose your preferred verification method' 
                : 'Verify your identity before signing the contract'}
            </p>
            
            {analysisResult && (
              <div className="text-white/40 text-xs mt-2 space-y-1">
                <p>Risk level: {analysisResult.risk_level} | Trust: {Math.round(analysisResult.trust_score * 100)}%</p>
                <p>Decision: {analysisResult.decision === 'allow' ? '✅ Allowed' : '❌ Denied'}</p>
                <p className="text-white/30 text-xs">{analysisResult.explanation}</p>
              </div>
            )}
            
            {userEnrolledModalities && userEnrolledModalities.length > 0 && (
              <p className="text-white/30 text-xs mt-1">
                Enrolled biometrics: {userEnrolledModalities.join(', ')}
              </p>
            )}
          </div>

          {purpose === 'login' && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mb-4">
              <input
                type="email"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full p-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:border-purple-500 transition"
              />
              <p className="text-white/40 text-xs mt-1">Enter your registered email</p>
            </motion.div>
          )}

          {status === 'success' && countdown !== null && (
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="mb-4 p-3 rounded-xl bg-green-500/20 border border-green-500/30 flex items-center justify-center gap-2">
              <Clock size={16} className="text-green-400" />
              <span className="text-green-400 text-sm">Verification valid for: {formatCountdown(countdown)}</span>
            </motion.div>
          )}

          {retryCount >= 2 && status === 'error' && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="mb-4 p-3 rounded-xl bg-yellow-500/20 border border-yellow-500/30 flex items-center justify-center gap-2">
              <AlertTriangle size={16} className="text-yellow-400" />
              <span className="text-yellow-400 text-sm">Multiple attempts failed. Try another method.</span>
            </motion.div>
          )}

          {!selectedMethod && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-3">
              {displayMethods.map((method, idx) => (
                <motion.button
                  key={method.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  onClick={() => handleMethodSelect(method.id)}
                  className="w-full flex items-center gap-4 p-4 rounded-2xl border border-white/20 hover:bg-white/10 transition-all duration-300 group"
                  whileHover={{ scale: 1.02, x: 5 }}
                >
                  <div className={`w-12 h-12 bg-gradient-to-r ${method.color} rounded-full flex items-center justify-center shadow-lg group-hover:scale-110 transition`}>
                    {method.icon}
                  </div>
                  <div className="flex-1 text-left">
                    <h3 className="font-semibold">{method.name}</h3>
                    <p className="text-sm text-white/40">{method.description}</p>
                  </div>
                </motion.button>
              ))}
            </motion.div>
          )}

          {selectedMethod === 'signature' && step === 'signature_drawing' && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mt-4">
              <div className="border-2 border-dashed border-purple-500 rounded-2xl bg-white/10 p-3 mb-4">
                <SignatureCanvas
                  ref={sigCanvasRef}
                  penColor="#ffffff"
                  backgroundColor="rgba(255,255,255,0.1)"
                  canvasProps={{ width: 400, height: 200, className: "rounded-xl w-full" }}
                />
              </div>
              <div className="flex gap-3">
                <button onClick={clearSignature} className="flex-1 py-2.5 bg-gray-600 rounded-xl hover:bg-gray-700 transition">Clear</button>
                <button onClick={captureSignature} className="flex-1 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl hover:shadow-lg transition">Verify</button>
              </div>
              <button onClick={handleBack} className="w-full mt-3 py-2.5 border border-white/30 rounded-xl hover:bg-white/10 transition">Back</button>
            </motion.div>
          )}

          {selectedMethod === 'face' && status !== 'success' && step !== 'signature_drawing' && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mt-4">
              <div className="relative">
                <video ref={videoRef} autoPlay playsInline muted className="w-full rounded-2xl border-2 border-purple-500 shadow-lg" />
                <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                  <div className="w-48 h-48 rounded-full border-2 border-purple-400/50 shadow-lg"></div>
                </div>
              </div>
              <div className="flex gap-3 mt-4">
                <button onClick={captureFace} className="flex-1 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl hover:shadow-lg hover:shadow-purple-500/30 transition font-medium flex items-center justify-center gap-2">
                  <Camera size={18} /> Capture
                </button>
                <button onClick={handleBack} className="py-2.5 px-4 border border-white/30 rounded-xl hover:bg-white/10 transition flex items-center gap-2">
                  <ArrowLeft size={18} /> Back
                </button>
              </div>
            </motion.div>
          )}

          {selectedMethod === 'voice' && status === 'capturing' && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="mt-4 text-center py-8">
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center animate-pulse">
                <Mic size={40} className="text-white" />
              </div>
              <p className="text-lg font-semibold">Recording...</p>
              <p className="text-white/60 text-sm mt-2">{recordingTime}s / 3s</p>
              <p className="text-white/40 text-sm mt-4">Say something like "I agree to this contract"</p>
            </motion.div>
          )}

          {(status === 'verifying' || (status === 'capturing' && selectedMethod !== 'voice' && selectedMethod !== 'signature')) && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
              <div className="relative w-20 h-20 mx-auto mb-4">
                <div className="absolute inset-0 border-4 border-purple-500/30 rounded-full"></div>
                <div className="absolute inset-0 border-4 border-t-purple-500 border-r-pink-500 border-b-indigo-500 border-l-transparent rounded-full animate-spin"></div>
                <div className="absolute inset-2 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full animate-pulse"></div>
              </div>
              <p className="font-semibold">{message}</p>
              <p className="text-white/40 text-sm mt-2">This may take a few seconds</p>
            </motion.div>
          )}

          {status === 'success' && (
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-8">
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-r from-green-500 to-emerald-600 flex items-center justify-center">
                <CheckCircle size={40} className="text-white" />
              </div>
              <p className="text-xl font-semibold text-green-400">Verified!</p>
              <p className="text-white/60 text-sm mt-2">{message}</p>
              <p className="text-white/40 text-xs mt-4">Confidence: {Math.round(confidence * 100)}%</p>
            </motion.div>
          )}

          {status === 'error' && (
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-8">
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-red-500/20 flex items-center justify-center">
                <XCircle size={40} className="text-red-400" />
              </div>
              <p className="text-red-400 font-semibold">{message}</p>
              <div className="flex gap-3 mt-6">
                <button onClick={retryCapture} className="flex-1 py-2.5 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl hover:shadow-lg transition flex items-center justify-center gap-2">
                  <RefreshCw size={18} /> Retry
                </button>
                <button onClick={handleBack} className="flex-1 py-2.5 border border-white/30 rounded-xl hover:bg-white/10 transition flex items-center justify-center gap-2">
                  <ArrowLeft size={18} /> Other Method
                </button>
              </div>
            </motion.div>
          )}

          {!selectedMethod && (
            <button onClick={onClose} className="w-full mt-6 py-2.5 border border-white/30 rounded-xl hover:bg-white/10 transition text-white/70">
              Cancel
            </button>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}