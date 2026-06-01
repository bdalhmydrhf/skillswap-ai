// frontend/src/components/BiometricEnrollModal.jsx
import React, { useState, useRef, useEffect } from 'react';
import { Camera, Mic, Fingerprint, CheckCircle, XCircle, Loader2, Cpu, PenTool } from 'lucide-react';
import api from '../api/axiosConfig';
import DeviceCapabilityDetector from '../utils/deviceCapabilities';
import SignatureCanvas from 'react-signature-canvas';

export default function BiometricEnrollModal({ onSuccess, onClose, userId }) {
  const [step, setStep] = useState('detecting');
  const [availableMethods, setAvailableMethods] = useState([]);
  const [suggestedMethod, setSuggestedMethod] = useState(null);
  const [selectedMethod, setSelectedMethod] = useState(null);
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [confidence, setConfidence] = useState(0);
  
  // ✅ إضافات للعداد والتسجيل المتكرر
  const [samplesCount, setSamplesCount] = useState(0);
  const [neededSamples, setNeededSamples] = useState(5);
  const [enrollmentComplete, setEnrollmentComplete] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  const videoRef = useRef(null);
  const streamRef = useRef(null);
  const sigCanvasRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const methodsConfig = {
    fingerprint: { 
      name: ' Finger', 
      icon: <Fingerprint size={24} />, 
      description: 'Use your device\'s fingerprint sensor (Windows Hello)', 
      priority: 1
    },
    face: { 
      name: 'Face Recognition', 
      icon: <Camera size={24} />, 
      description: 'Use your device\'s camera to capture your face', 
      priority: 2 
    },
    voice: { 
      name: 'Voice Recognition', 
      icon: <Mic size={24} />, 
      description: 'Speak a short phrase to record your voice', 
      priority: 3 
    },
    signature: { 
      name: 'Digital Signature', 
      icon: <PenTool size={24} />, 
      description: 'Draw your signature (works on all devices)', 
      priority: 4
    },
  };

  // كشف إمكانيات الجهاز
  useEffect(() => {
    const detectCapabilities = async () => {
      setMessage('Checking your device capabilities...');
      try {
        const methods = await DeviceCapabilityDetector.detectAvailableMethods();
        const supportedMethods = methods.filter(m => ['face', 'voice', 'fingerprint', 'signature'].includes(m));
        
        if (!supportedMethods.includes('signature')) {
          supportedMethods.push('signature');
        }
        
        setAvailableMethods(supportedMethods);
        
        const priorityOrder = ['fingerprint', 'face', 'voice', 'signature'];
        const bestMethod = priorityOrder.find(m => supportedMethods.includes(m));
        setSuggestedMethod(bestMethod || 'signature');
        
        setStep('selecting');
      } catch (error) {
        console.error('Error detecting capabilities:', error);
        setMessage('Failed to detect device capabilities');
        setStep('error');
      }
    };
    detectCapabilities();
  }, []);

  // ✅ دالة تسجيل الصوت المحسنة (تدعم 5 مرات)
  const startVoiceCapture = async () => {
    if (isRecording) return;
    
    setStatus('capturing');
    setIsRecording(true);
    setMessage(`🎤 Recording  ${samplesCount + 1} of  ${neededSamples}... Speak for 3 seconds`);
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      let mimeType = '';
      if (MediaRecorder.isTypeSupported('audio/wav')) {
        mimeType = 'audio/wav';
      } else if (MediaRecorder.isTypeSupported('audio/ogg')) {
        mimeType = 'audio/ogg';
      } else {
        mimeType = 'audio/webm';
      }
      
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        const reader = new FileReader();
        reader.readAsDataURL(blob);
        reader.onloadend = async () => {
          const fullAudioData = reader.result;
          const audioData = fullAudioData.split(',')[1];
          
          if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
          }
          
          await saveBiometric('voice', audioData);
        };
      };
      
      mediaRecorder.start();
      setTimeout(() => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
          mediaRecorderRef.current.stop();
          setIsRecording(false);
        }
      }, 3000);
      
    } catch (error) {
      console.error("Microphone error:", error);
      setMessage('❌ Cannot access microphone');
      setStatus('error');
      setIsRecording(false);
    }
  };

  // دالة التقاط الوجه
  const startFaceCapture = async () => {
    try {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
    } catch (error) {
      console.error("Camera error:", error);
      setMessage('❌ Cannot access camera');
      setStatus('error');
    }
  };

  const captureFace = async () => {
    if (!videoRef.current) return;
    
    setStatus('capturing');
    setMessage('Capturing image...');
    
    const canvas = document.createElement('canvas');
    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);
    const imageData = canvas.toDataURL('image/jpeg', 0.9).split(',')[1];
    
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
    
    await saveBiometric('face', imageData);
  };

  // دالة تسجيل بصمة الإصبع
  const startFingerprintCapture = async () => {
    setStatus('capturing');
    setMessage('Opening Windows Hello...');
    
    try {
      if (!window.PublicKeyCredential) {
        throw new Error('WebAuthn not supported');
      }
      
      const publicKeyCredentialCreationOptions = {
        challenge: new Uint8Array(32),
        rp: { name: "SkillSwap AI", id: window.location.hostname },
        user: {
          id: new Uint8Array(16),
          name: userId?.toString() || "user",
          displayName: "User"
        },
        pubKeyCredParams: [
          { alg: -7, type: "public-key" },
          { alg: -257, type: "public-key" }
        ],
        authenticatorSelection: {
          authenticatorAttachment: "platform",
          userVerification: "required"
        },
        timeout: 60000
      };
      
      const credential = await navigator.credentials.create({
        publicKey: publicKeyCredentialCreationOptions
      });
      
      const credentialData = JSON.stringify({
        id: credential.id,
        rawId: Array.from(new Uint8Array(credential.rawId)),
        type: credential.type,
        response: {
          authenticatorData: Array.from(new Uint8Array(credential.response.authenticatorData)),
          clientDataJSON: Array.from(new Uint8Array(credential.response.clientDataJSON))
        }
      });
      
      await saveBiometric('fingerprint', credentialData);
    } catch (error) {
      console.error("Fingerprint error:", error);
      setMessage('Failed to register fingerprint. Try another method.');
      setStatus('error');
    }
  };

  // دالة التوقيع الرقمي
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
    
    setStatus('saving');
    setMessage('');
    
    const fullSignatureData = sigCanvasRef.current.toDataURL();
    const signatureData = fullSignatureData.split(',')[1];
    await saveBiometric('signature', signatureData);
  };

  // ✅ دالة الحفظ المحسنة - تدعم التسجيل المتكرر
  const saveBiometric = async (type, data) => {
    if (!userId) {
      console.error("❌ userId is undefined!");
      setMessage("Error: User ID not found");
      setStatus('error');
      return;
    }
    
    setStatus('saving');
    setMessage(`Saving sample ${samplesCount + 1}of ${neededSamples}...`);
    
    try {
      const response = await api.post('/biometric/enroll/', {
        biometric_type: type,
        data: data
      });
      
      const newCount = response.data.samples_collected;
      const isComplete = response.data.enrollment_complete;
      const totalNeeded = response.data.needed_samples || 5;
      
      setSamplesCount(newCount);
      setNeededSamples(totalNeeded);
      setConfidence(0.95);
      
      if (isComplete) {
        setEnrollmentComplete(true);
        setStatus('success');
        setMessage(`✅ Enrollment completed successfully! (${newCount}/${totalNeeded})`);
        
        setTimeout(() => {
          onSuccess(response.data);
        }, 2000);
      } else {
        // ✅ لم يكتمل - نعود لشاشة التسجيل لالتقاط العينة التالية
        setStatus('idle');
        setMessage(`✅ Collected ${newCount} of ${totalNeeded}. Click 'Record Again' to continue`);
        
        // إعادة تعيين الحالة لشاشة التسجيل
        setStep('capturing');
        setStatus('idle');
      }
      
    } catch (error) {
      console.error('Enroll error:', error);
      console.error('Response data:', error.response?.data);
      console.error('Response status:', error.response?.status);
      setStatus('error');
      setMessage(error.response?.data?.error || error.response?.data?.message || 'Failed to enroll biometric');
      setIsRecording(false);
    }
  };

  const handleMethodSelect = (methodId) => {
    setSelectedMethod(methodId);
    setStatus('idle');
    setMessage('');
    
    // إعادة تعيين العداد لكل طريقة
    setSamplesCount(0);
    setEnrollmentComplete(false);
    
    if (methodId === 'face') {
      startFaceCapture();
    } else if (methodId === 'voice') {
      setStep('capturing');
    } else if (methodId === 'fingerprint') {
      startFingerprintCapture();
    } else if (methodId === 'signature') {
      startSignatureCapture();
    }
  };

  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  // خطوة الكشف عن الجهاز
  if (step === 'detecting') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
        <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-3xl p-8 w-[90%] max-w-md text-white text-center">
          <Cpu className="w-16 h-16 text-indigo-500 animate-spin mx-auto mb-4" />
          <p className="text-lg">{message}</p>
        </div>
      </div>
    );
  }

  // خطوة اختيار الطريقة
  if (step === 'selecting') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
        <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-3xl p-8 w-[90%] max-w-md text-white">
          <h2 className="text-2xl font-bold text-center mb-4">🔐Biometric Authentication Setup</h2>
          
          <div className="mb-6 p-4 bg-indigo-500/20 rounded-2xl border border-indigo-500/30">
            <p className="text-center mb-2">🔍 Your device supports:</p>
            <div className="flex flex-wrap justify-center gap-3">
              {availableMethods.map(m => (
                <span key={m} className="px-3 py-1 bg-indigo-500/30 rounded-full text-sm">
                  {m === 'fingerprint' && '👆 Fingerprint'}
                  {m === 'face' && '📸 Face'}
                  {m === 'voice' && '🎤 Voice'}
                  {m === 'signature' && '✍ Signature'}
                </span>
              ))}
            </div>
          </div>

          {suggestedMethod && (
            <p className="text-center text-gray-300 mb-6">
              <span className="text-green-400">✨We recommend using: {methodsConfig[suggestedMethod]?.name}</span>
            </p>
          )}

          <div className="space-y-3">
            {availableMethods.map((method) => (
              <button
                key={method}
                onClick={() => {
                  setSelectedMethod(method);
                  handleMethodSelect(method);
                  if (method !== 'signature') {
                    setStep('capturing');
                  }
                }}
                className="w-full flex items-center gap-4 p-4 rounded-2xl border border-white/20 hover:bg-white/10 transition-all hover:border-indigo-500"
              >
                <div className="w-12 h-12 bg-indigo-500/20 rounded-full flex items-center justify-center">
                  {methodsConfig[method]?.icon}
                </div>
                <div className="flex-1 text-left">
                  <h3 className="font-semibold">{methodsConfig[method]?.name}</h3>
                  <p className="text-sm text-gray-400">{methodsConfig[method]?.description}</p>
                </div>
                {method === suggestedMethod && (
                  <span className="text-green-400 text-sm bg-green-500/20 px-2 py-1 rounded-full">⭐ Recommended</span>
                )}
              </button>
            ))}
          </div>

          <button
            onClick={onClose}
            className="w-full mt-6 py-2 border border-white/30 rounded-xl hover:bg-white/10 transition"
          >
          Skip for now (You can enroll later from settings)
          </button>
        </div>
      </div>
    );
  }

  // خطوة التقاط بصمة الوجه
  if (step === 'capturing' && selectedMethod === 'face') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
        <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-3xl p-8 w-[90%] max-w-md text-white">
          <h2 className="text-2xl font-bold text-center mb-4">📸 Face Recognition Enrollment</h2>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            className="w-full rounded-2xl border-2 border-indigo-500 mb-4"
          />
          <button
            onClick={captureFace}
            disabled={status === 'saving'}
            className="w-full py-2 bg-indigo-600 rounded-xl hover:bg-indigo-700 transition disabled:opacity-50"
          >
             Capture Photo
          </button>
          <button
            onClick={() => setStep('selecting')}
            className="w-full mt-2 py-2 border border-white/30 rounded-xl hover:bg-white/10 transition"
          >
             Back
          </button>
        </div>
      </div>
    );
  }

  // ✅ خطوة التقاط بصمة الصوت المحسنة مع العداد
  if (step === 'capturing' && selectedMethod === 'voice') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
        <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-3xl p-8 w-[90%] max-w-md text-white">
          <h2 className="text-2xl font-bold text-center mb-4">🎤 Voice Recognition Enrollment  </h2>
          
          {/* ✅ عداد التسجيل */}
          <div className="text-center mb-6">
            <div className="flex justify-center gap-2 mb-2">
              {[...Array(neededSamples)].map((_, i) => (
                <div
                  key={i}
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
                    i < samplesCount
                      ? 'bg-green-500 text-white'
                      : i === samplesCount && status === 'idle'
                      ? 'bg-indigo-500 text-white animate-pulse'
                      : 'bg-gray-600 text-gray-300'
                  }`}
                >
                  {i + 1}
                </div>
              ))}
            </div>
            <p className="text-gray-300">
              {samplesCount >= neededSamples 
                ? '✅ Enrollment complete!' 
                : `📊 Collected ${samplesCount} of ${neededSamples} samples`}
            </p>
          </div>
          
          {!enrollmentComplete && samplesCount < neededSamples && (
            <button
              onClick={startVoiceCapture}
              disabled={status === 'saving' || isRecording}
              className="w-full py-3 bg-indigo-600 rounded-xl hover:bg-indigo-700 transition disabled:opacity-50 text-lg font-semibold"
            >
              {isRecording ? '🎤 Recording...' : samplesCount === 0 ? '🎤 Start Recording ' : '🎤 Record Again'}
            </button>
          )}
          
          {samplesCount >= neededSamples && (
            <div className="text-center">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-2" />
              <p className="text-green-400 font-semibold">✅ Enrollment completed successfully! </p>
              <button
                onClick={() => onSuccess({ enrollment_complete: true })}
                className="mt-4 py-2 px-6 bg-green-600 rounded-xl hover:bg-green-700 transition"
              >
                Continue
              </button>
            </div>
          )}
          
          {status === 'error' && (
            <div className="mt-4 text-center">
              <p className="text-red-400 mb-2">{message}</p>
              <button
                onClick={() => {
                  setStatus('idle');
                  setMessage('');
                }}
                className="py-2 px-4 bg-indigo-600 rounded-xl hover:bg-indigo-700 transition"
              >
                Retry
              </button>
            </div>
          )}
          
          {status === 'saving' && (
            <div className="text-center mt-4">
              <Loader2 className="w-8 h-8 text-indigo-500 animate-spin mx-auto mb-2" />
              <p>{message}</p>
            </div>
          )}
          
          {status === 'idle' && samplesCount > 0 && samplesCount < neededSamples && (
            <p className="text-center text-gray-400 text-sm mt-4">
              🎤 Speak the same phrase for 3 seconds 
            </p>
          )}
          
          <button
            onClick={() => {
              if (window.confirm('Cancel enrollment? Current progress will be lost.')) {
                setStep('selecting');
                setSamplesCount(0);
                setEnrollmentComplete(false);
              }
            }}
            className="w-full mt-4 py-2 border border-white/30 rounded-xl hover:bg-white/10 transition"
          >
          Cancel
          </button>
        </div>
      </div>
    );
  }

  // خطوة رسم التوقيع الرقمي
  if (step === 'signature_drawing' && selectedMethod === 'signature') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
        <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-3xl p-8 w-[90%] max-w-md text-white">
          <h2 className="text-2xl font-bold text-center mb-4">✍ Digital Signature</h2>
          <div className="border-2 border-dashed rounded-2xl bg-white/10 p-3 mb-4">
            <SignatureCanvas
              ref={sigCanvasRef}
              penColor="white"
              backgroundColor="transparent"
              canvasProps={{ width: 500, height: 200, className: "rounded-xl" }}
            />
          </div>
          <div className="flex gap-3">
            <button
              onClick={clearSignature}
              className="flex-1 py-2 bg-gray-600 rounded-xl hover:bg-gray-700 transition"
            >
              🧹 Clear
            </button>
            <button
              onClick={captureSignature}
              disabled={status === 'saving'}
              className="flex-1 py-2 bg-indigo-600 rounded-xl hover:bg-indigo-700 transition disabled:opacity-50"
            >
              💾 Save Signature
            </button>
          </div>
          <button
            onClick={() => setStep('selecting')}
            className="w-full mt-2 py-2 border border-white/30 rounded-xl hover:bg-white/10 transition"
          >
        Back
          </button>
        </div>
      </div>
    );
  }

  // خطوة الحفظ أو النجاح أو الخطأ
  if (status === 'saving' || status === 'success' || status === 'error') {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
        <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-3xl p-8 w-[90%] max-w-md text-white text-center">
          {status === 'saving' && (
            <>
              <Loader2 className="w-16 h-16 text-indigo-500 animate-spin mx-auto mb-4" />
              <p>{message}</p>
            </>
          )}
          {status === 'success' && (
            <>
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <p className="text-green-400 font-semibold">{message}</p>
              <p className="text-sm text-gray-400 mt-2">Confidence:  {Math.round(confidence * 100)}%</p>
            </>
          )}
          {status === 'error' && (
            <>
              <XCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
              <p className="text-red-400">{message}</p>
              <button
                onClick={() => {
                  setStatus('idle');
                  setStep('selecting');
                  setSamplesCount(0);
                }}
                className="mt-4 py-2 px-6 bg-indigo-600 rounded-xl hover:bg-indigo-700 transition"
              >
                Retry
              </button>
            </>
          )}
        </div>
      </div>
    );
  }

  return null;
}