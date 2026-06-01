// src/pages/ContractSignPage.jsx
import React, { useState, useEffect, useRef } from "react";
import { useParams, useNavigate, useLocation } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  FileSignature, Shield, User, DollarSign, Calendar, 
  CheckCircle, XCircle, Clock, ExternalLink, ArrowLeft,
  Loader2, AlertTriangle, Fingerprint, Mic, Camera, Key
} from "lucide-react";
import api from "../api/axiosConfig";
import BiometricModal from "../components/BiometricModal";
import PinModal from "../components/PinModal";

export default function ContractSignPage() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const [signing, setSigning] = useState(false);
  const [showBiometric, setShowBiometric] = useState(false);
  const [showPinModal, setShowPinModal] = useState(false);
  const [userRole, setUserRole] = useState(null);
  const [biometricVerified, setBiometricVerified] = useState(false);
  const [biometricData, setBiometricData] = useState(null);
  const [pinVerified, setPinVerified] = useState(false);
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");
  
  const confirmSignCalledRef = useRef(false); // ✅ منع التكرار

  // التحقق من المصادقة البيومترية القادمة من المحادثة
  useEffect(() => {
    if (location.state?.biometricVerified) {
      setBiometricVerified(true);
      setBiometricData(location.state.biometricData);
    }
  }, [location]);

  useEffect(() => {
    fetchContract();
  }, [contractId]);

  // ✅ مراقبة pinVerified - عندما تصبح true يتم التوقيع
  useEffect(() => {
    if (pinVerified && !signing && !confirmSignCalledRef.current) {
      confirmSignCalledRef.current = true;
      confirmSign(null, { method: 'pin', verified: true });
    }
  }, [pinVerified]);

  const fetchContract = async () => {
    try {
      const response = await api.get(`/contracts/${contractId}/`);
      setContract(response.data);
      
      if (response.data.client?.id === currentUser.id) {
        setUserRole('client');
      } else if (response.data.freelancer?.id === currentUser.id) {
        setUserRole('freelancer');
      }
    } catch (error) {
      console.error("Error fetching contract:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleSignClick = () => {
    setShowVerificationOptions(true);
  };

  const [showVerificationOptions, setShowVerificationOptions] = useState(false);

  const selectVerificationMethod = (method) => {
    setShowVerificationOptions(false);
    if (method === 'pin') {
      setShowPinModal(true);
    } else if (method === 'biometric') {
      setShowBiometric(true);
    }
  };

  // ✅ معالج نجاح التحقق بـ PIN - المعدل
  const handlePinSuccess = () => {
    setShowPinModal(false);
    setPinVerified(true);  // ✅ هذا سيؤدي إلى تشغيل useEffect أعلاه
  };

  const handleBiometricSuccess = (data) => {
    setBiometricData(data);
    setBiometricVerified(true);
    setShowBiometric(false);
    confirmSign(data, { method: 'biometric', verified: true });
  };

  const confirmSign = async (biometric = null, verification = null) => {
    // ✅ منع التكرار
    if (signing) return;
    
    setSigning(true);
    try {
      const payload = {
        biometric_verified: biometric !== null || biometricVerified,
        pin_verified: pinVerified,
        verification_method: verification?.method || (biometric ? 'biometric' : 'unknown'),
        biometric_type: biometric?.type || biometricData?.type || 'face',
        biometric_confidence: biometric?.confidence || biometricData?.confidence || 0.95
      };
      
      console.log("📤 Signing payload:", payload); // ✅ للتصحيح
      
      const response = await api.post(`/contracts/${contractId}/sign/`, payload);
      
      if (response.data.success) {
        alert(response.data.fully_signed 
          ? "🎉 Contract fully signed! It is now legally binding on the blockchain." 
          : "✅ You have signed the contract. Waiting for the other party to sign.");
        
        navigate('/contracts');
      }
    } catch (error) {
      console.error("Error signing contract:", error);
      alert(error.response?.data?.error || "❌ Failed to sign contract");
    } finally {
      setSigning(false);
      confirmSignCalledRef.current = false; // ✅ إعادة تعيين للتوقيعات المستقبلية
    }
  };

  const getStatusConfig = (status) => {
    const configs = {
      pending: { color: "text-yellow-400", bg: "bg-yellow-500/20", icon: Clock, text: "Awaiting Signatures" },
      partially_signed: { color: "text-orange-400", bg: "bg-orange-500/20", icon: FileSignature, text: "Partially Signed" },
      active: { color: "text-green-400", bg: "bg-green-500/20", icon: CheckCircle, text: "Active" },
      completed: { color: "text-emerald-400", bg: "bg-emerald-500/20", icon: CheckCircle, text: "Completed" },
      cancelled: { color: "text-red-400", bg: "bg-red-500/20", icon: XCircle, text: "Cancelled" },
    };
    return configs[status] || configs.pending;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-purple-400 animate-spin mx-auto mb-4" />
          <p className="text-white">Loading contract details...</p>
        </div>
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-yellow-400 mx-auto mb-4" />
          <p className="text-white text-xl">Contract not found</p>
          <button onClick={() => navigate('/contracts')} className="mt-4 px-6 py-2 bg-purple-500 rounded-lg">Back to Contracts</button>
        </div>
      </div>
    );
  }

  const statusConfig = getStatusConfig(contract.status);
  const StatusIcon = statusConfig.icon;
  const hasSigned = userRole === 'client' ? contract.client_signature : contract.freelancer_signature;
  const otherPartySigned = userRole === 'client' ? contract.freelancer_signature : contract.client_signature;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 pt-24 pb-12 px-6">
      <div className="max-w-4xl mx-auto">
        <button onClick={() => navigate(-1)} className="mb-6 flex items-center gap-2 text-white/60 hover:text-white transition">
          <ArrowLeft size={20} /> Back
        </button>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 overflow-hidden">
          <div className="bg-gradient-to-r from-purple-600/30 to-pink-600/30 p-6 border-b border-white/10">
            <div className="flex justify-between items-start flex-wrap gap-4">
              <div>
                <h1 className="text-2xl font-bold text-white">{contract.title || `Contract #${contract.id}`}</h1>
                <p className="text-white/40 text-sm mt-1">Created on {new Date(contract.created_at).toLocaleDateString()}</p>
              </div>
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${statusConfig.bg}`}>
                <StatusIcon size={18} className={statusConfig.color} />
                <span className={`text-sm font-medium ${statusConfig.color}`}>{statusConfig.text}</span>
              </div>
            </div>
          </div>

          <div className="p-6 space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><User size={14} /> Client</div>
                <p className="text-white font-medium">{contract.client?.username || "Unknown"}</p>
                {contract.client_signature && <div className="flex items-center gap-1 mt-2 text-green-400 text-xs"><CheckCircle size={12} /> Signed</div>}
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><User size={14} /> Freelancer</div>
                <p className="text-white font-medium">{contract.freelancer?.username || "Unknown"}</p>
                {contract.freelancer_signature && <div className="flex items-center gap-1 mt-2 text-green-400 text-xs"><CheckCircle size={12} /> Signed</div>}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><DollarSign size={14} /> Amount</div>
                <p className="text-white text-xl font-bold">{contract.total_amount} {contract.currency || "USD"}</p>
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><Calendar size={14} /> Deadline</div>
                <p className="text-white">{new Date(contract.deadline).toLocaleDateString()}</p>
              </div>
            </div>

            {contract.description && (
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-white/40 text-sm mb-2">Description</p>
                <p className="text-white/80">{contract.description}</p>
              </div>
            )}
            {contract.terms && (
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-white/40 text-sm mb-2">Terms & Conditions</p>
                <p className="text-white/70 text-sm whitespace-pre-wrap">{contract.terms}</p>
              </div>
            )}

            <div className="bg-white/5 rounded-xl p-4">
              <p className="text-white/40 text-sm mb-3 flex items-center gap-2"><Shield size={14} /> Signature Status</p>
              <div className="space-y-2">
                <div className="flex items-center justify-between"><span className="text-white/60">Your Signature</span><span className={hasSigned ? "text-green-400" : "text-yellow-400"}>{hasSigned ? "✓ Signed" : "Pending"}</span></div>
                <div className="flex items-center justify-between"><span className="text-white/60">Other Party</span><span className={otherPartySigned ? "text-green-400" : "text-yellow-400"}>{otherPartySigned ? "✓ Signed" : "Pending"}</span></div>
              </div>
            </div>

            {contract.blockchain_tx_hash && (
              <div className="bg-green-500/10 rounded-xl p-4 border border-green-500/20">
                <div className="flex items-center gap-2 mb-2"><Shield size={14} className="text-green-400" /><p className="text-green-400 text-sm font-medium">Blockchain Verified</p></div>
                <div className="flex items-center gap-2"><code className="text-white/60 text-xs font-mono break-all flex-1">{contract.blockchain_tx_hash}</code><button onClick={() => window.open(`https://sepolia.etherscan.io/tx/${contract.blockchain_tx_hash}`, '_blank')} className="p-1 hover:bg-white/10 rounded"><ExternalLink size={14} className="text-white/40" /></button></div>
              </div>
            )}

            {(contract.status === "pending" || contract.status === "partially_signed") && !hasSigned && (
              <button onClick={handleSignClick} disabled={signing} className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold text-lg hover:shadow-lg hover:shadow-purple-500/30 transition flex items-center justify-center gap-3">
                {signing ? <Loader2 size={20} className="animate-spin" /> : <FileSignature size={20} />}
                {signing ? "Signing..." : "Sign Contract"}
              </button>
            )}

            {(contract.status === "active" || contract.status === "completed") && (
              <div className="text-center py-4"><CheckCircle size={48} className="text-green-400 mx-auto mb-2" /><p className="text-white font-semibold">Contract Signed and Active</p><p className="text-white/40 text-sm">Both parties have signed this contract</p></div>
            )}

            {hasSigned && !otherPartySigned && contract.status !== "active" && (
              <div className="text-center py-2"><Clock size={24} className="text-yellow-400 mx-auto mb-2" /><p className="text-white/60 text-sm">Waiting for the other party to sign...</p></div>
            )}
          </div>
        </motion.div>
      </div>

      {/* نافذة اختيار طريقة التحقق */}
      {showVerificationOptions && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm" onClick={() => setShowVerificationOptions(false)}>
          <div className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-2xl p-6 max-w-md w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-xl font-bold text-white text-center mb-4">🔐 Verify Your Identity</h3>
            <p className="text-white/60 text-center mb-6">Choose verification method to sign contract</p>
            
            <div className="space-y-3">
              <button onClick={() => selectVerificationMethod('pin')} className="w-full flex items-center gap-4 p-4 rounded-xl border border-white/20 hover:bg-white/10 transition group">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                  <Key size={22} className="text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-semibold text-white">Security PIN</p>
                  <p className="text-sm text-white/50">Enter your 8-digit PIN</p>
                </div>
              </button>
              
              <button onClick={() => selectVerificationMethod('biometric')} className="w-full flex items-center gap-4 p-4 rounded-xl border border-white/20 hover:bg-white/10 transition group">
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
                  <Fingerprint size={22} className="text-white" />
                </div>
                <div className="flex-1 text-left">
                  <p className="font-semibold text-white">Biometric</p>
                  <p className="text-sm text-white/50">Use Face / Voice / Fingerprint</p>
                </div>
              </button>
            </div>
            
            <button onClick={() => setShowVerificationOptions(false)} className="w-full mt-6 py-2 border border-white/30 rounded-xl hover:bg-white/10 transition text-white/70">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Modal PIN */}
      {showPinModal && (
        <PinModal onSuccess={handlePinSuccess} onClose={() => setShowPinModal(false)} />
      )}

      {/* Biometric Modal */}
      {showBiometric && <BiometricModal onSuccess={handleBiometricSuccess} onClose={() => setShowBiometric(false)} purpose="sign_contract" contractId={contractId} />}
    </div>
  );
}
