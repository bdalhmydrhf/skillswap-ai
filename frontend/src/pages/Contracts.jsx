// src/pages/Contracts.jsx - النسخة الأسطورية V5.0
// ✅ متكاملة مع: Biometric Authentication, Chat Integration, Real-time Updates
// ✅ مع نظام التقييم (Rating) المتكامل + زر إكمال العقد (Complete)

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Hourglass, 
  CheckCircle, 
  XCircle, 
  Edit, 
  MessageCircle, 
  FileSignature,
  Shield,
  Clock,
  DollarSign,
  User,
  Briefcase,
  Calendar,
  Hash,
  ExternalLink,
  RefreshCw,
  Eye,
  EyeOff,
  Copy,
  Check,
  Star,
  CheckSquare
} from "lucide-react";
import api from "../api/axiosConfig";
import BiometricModal from "../components/BiometricModal";

export default function Contracts() {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedContract, setSelectedContract] = useState(null);
  const [showBiometric, setShowBiometric] = useState(false);
  const [selectedContractId, setSelectedContractId] = useState(null);
  const [biometricVerified, setBiometricVerified] = useState(false);
  const [biometricData, setBiometricData] = useState(null);
  const [signingInProgress, setSigningInProgress] = useState(false);
  const [copied, setCopied] = useState(false);
  const [filter, setFilter] = useState("all"); // all, pending, active, completed
  const [refreshKey, setRefreshKey] = useState(0);
  
  // ✅ Rating Modal State
  const [ratingModal, setRatingModal] = useState({ open: false, contractId: null, rating: 0, feedback: "" });
  const [ratingLoading, setRatingLoading] = useState(false);
  
  // ✅ Complete Contract State
  const [completingId, setCompletingId] = useState(null);

  // جلب العقود من الباكند
  const fetchContracts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await api.get("/contracts/");
      let contractsData = [];
      if (Array.isArray(response.data)) {
        contractsData = response.data;
      } else if (response.data && Array.isArray(response.data.results)) {
        contractsData = response.data.results;
      }
      setContracts(contractsData);
    } catch (error) {
      console.error("Error fetching contracts:", error);
      setContracts([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchContracts();
  }, [fetchContracts, refreshKey]);

  // تصفية العقود
  const filteredContracts = contracts.filter(contract => {
    if (filter === "all") return true;
    return contract.status === filter;
  });

  // إحصائيات العقود
  const stats = {
    total: contracts.length,
    pending: contracts.filter(c => c.status === "pending" || c.status === "partially_signed").length,
    active: contracts.filter(c => c.status === "active").length,
    completed: contracts.filter(c => c.status === "completed").length,
  };

  const getStatusColor = (status) => {
    switch (status) {
      case "pending":
        return "bg-yellow-500/20 text-yellow-700 border-yellow-500/30";
      case "partially_signed":
        return "bg-orange-500/20 text-orange-700 border-orange-500/30";
      case "signed":
        return "bg-blue-500/20 text-blue-700 border-blue-500/30";
      case "active":
        return "bg-green-500/20 text-green-700 border-green-500/30";
      case "completed":
        return "bg-emerald-500/20 text-emerald-700 border-emerald-500/30";
      case "cancelled":
        return "bg-red-500/20 text-red-700 border-red-500/30";
      case "disputed":
        return "bg-purple-500/20 text-purple-700 border-purple-500/30";
      default:
        return "bg-gray-500/20 text-gray-700 border-gray-500/30";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "pending":
        return <Hourglass size={18} className="text-yellow-600" />;
      case "partially_signed":
        return <FileSignature size={18} className="text-orange-600" />;
      case "signed":
        return <Edit size={18} className="text-blue-600" />;
      case "active":
        return <CheckCircle size={18} className="text-green-600" />;
      case "completed":
        return <CheckCircle size={18} className="text-emerald-600" />;
      case "cancelled":
        return <XCircle size={18} className="text-red-600" />;
      case "disputed":
        return <Shield size={18} className="text-purple-600" />;
      default:
        return null;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case "pending": return "Awaiting Signatures";
      case "partially_signed": return "Partially Signed";
      case "signed": return "Signed";
      case "active": return "Active";
      case "completed": return "Completed";
      case "cancelled": return "Cancelled";
      case "disputed": return "Disputed";
      default: return status?.toUpperCase() || "UNKNOWN";
    }
  };

  const handleSignClick = (contractId) => {
    setSelectedContractId(contractId);
    setShowBiometric(true);
  };

  const handleBiometricSuccess = async (data) => {
    setBiometricData(data);
    setBiometricVerified(true);
    setShowBiometric(false);
  };

  const confirmSign = async () => {
    setSigningInProgress(true);
    try {
      const response = await api.post(`/contracts/${selectedContractId}/sign/`, {
        biometric_verified: true,
        biometric_type: biometricData?.type || 'face',
        biometric_confidence: biometricData?.confidence || 0.95,
        biometric_data: biometricData
      });
      
      if (response.data.success) {
        localStorage.setItem('dashboard-refresh', Date.now().toString());
        if (response.data.fully_signed) {
          alert("🎉 Contract fully signed! It is now legally binding on the blockchain.");
        } else {
          alert("✅ You have signed the contract. Waiting for the other party to sign.");
        }
        
        // تحديث القائمة
        setRefreshKey(prev => prev + 1);
        setSelectedContract(null);
        setBiometricVerified(false);
        setBiometricData(null);
      }

    } catch (error) {
      console.error("Error signing contract:", error);
      alert(error.response?.data?.error || "❌ Failed to sign contract");
    } finally {
      setSigningInProgress(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const goToChat = (roomId) => {
    window.location.href = `/chat/${roomId}`;
  };

  // ✅ فتح نافذة التقييم
  const openRatingModal = (contractId) => {
    setRatingModal({ open: true, contractId, rating: 0, feedback: "" });
  };

  // ✅ إرسال التقييم
  const submitRating = async () => {
    setRatingLoading(true);
    try {
      await api.post(`/v3/rate-contract/${ratingModal.contractId}/`, {
        rating: ratingModal.rating,
        feedback: ratingModal.feedback
      });
      alert("✅ Rating submitted successfully! Trust score will be updated.");
      setRatingModal({ open: false, contractId: null, rating: 0, feedback: "" });
      setRefreshKey(prev => prev + 1); // تحديث القائمة
    } catch (error) {
      console.error("Rating failed:", error);
      alert(error.response?.data?.error || "❌ Failed to submit rating");
    } finally {
      setRatingLoading(false);
    }
  };

  // ✅ إكمال العقد (Complete Contract)
  const completeContract = async (contractId) => {
    if (!window.confirm("Are you sure you want to mark this contract as completed?")) {
      return;
    }
    
    setCompletingId(contractId);
    try {
      const response = await api.post(`/contracts/${contractId}/complete/`);
      if (response.data.success) {
        alert("✅ Contract completed successfully! Trust score will be updated.");
        localStorage.setItem('dashboard-refresh', Date.now().toString());
        setRefreshKey(prev => prev + 1);
      }
    } catch (error) {
      console.error("Error completing contract:", error);
      alert(error.response?.data?.error || "❌ Failed to complete contract");
    } finally {
      setCompletingId(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-24 h-24 mx-auto mb-6">
            <div className="absolute inset-0 border-4 border-purple-400/30 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-t-purple-500 border-r-pink-500 border-b-indigo-500 border-l-transparent rounded-full animate-spin"></div>
          </div>
          <p className="text-white text-xl font-semibold">Loading Contracts</p>
          <p className="text-white/60 text-sm mt-2">Fetching blockchain data...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 pt-20 pb-12 px-6">
        {/* Decorative Background */}
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-0 left-0 w-96 h-96 bg-purple-500 rounded-full blur-[100px] animate-pulse"></div>
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-pink-500 rounded-full blur-[100px] animate-pulse delay-1000"></div>
        </div>

        <div className="relative z-10 max-w-7xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-5xl font-bold bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400 bg-clip-text text-transparent mb-4">
              Smart Contracts
            </h1>
            <p className="text-white/60 text-lg">Blockchain-powered agreements with biometric security</p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-4 text-center border border-white/20">
              <p className="text-3xl font-bold text-purple-400">{stats.total}</p>
              <p className="text-white/60 text-sm">Total Contracts</p>
            </div>
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-4 text-center border border-white/20">
              <p className="text-3xl font-bold text-yellow-400">{stats.pending}</p>
              <p className="text-white/60 text-sm">Pending</p>
            </div>
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-4 text-center border border-white/20">
              <p className="text-3xl font-bold text-green-400">{stats.active}</p>
              <p className="text-white/60 text-sm">Active</p>
            </div>
            <div className="bg-white/10 backdrop-blur-xl rounded-2xl p-4 text-center border border-white/20">
              <p className="text-3xl font-bold text-emerald-400">{stats.completed}</p>
              <p className="text-white/60 text-sm">Completed</p>
            </div>
          </div>

          {/* Filter Tabs */}
          <div className="flex flex-wrap justify-center gap-3 mb-8">
            {["all", "pending", "active", "completed"].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-5 py-2 rounded-full font-medium transition-all duration-300 ${
                  filter === tab
                    ? "bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/30"
                    : "bg-white/10 text-white/60 hover:bg-white/20"
                }`}
              >
                {tab === "all" ? "All" : tab === "pending" ? "Pending" : tab === "active" ? "Active" : "Completed"}
              </button>
            ))}
            <button
              onClick={() => setRefreshKey(prev => prev + 1)}
              className="px-5 py-2 rounded-full font-medium bg-white/10 text-white/60 hover:bg-white/20 transition-all duration-300 flex items-center gap-2"
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>
          </div>

          {/* Contracts Grid */}
          {filteredContracts.length === 0 ? (
            <div className="text-center py-20">
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-white/5 flex items-center justify-center">
                <FileSignature size={40} className="text-white/30" />
              </div>
              <p className="text-white/40 text-lg">No contracts found</p>
              <p className="text-white/20 text-sm mt-2">Create a contract from a skill post to get started</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <AnimatePresence>
                {filteredContracts.map((contract, index) => (
                  <motion.div
                    key={contract.id}
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.05 }}
                    whileHover={{ y: -5 }}
                    className="group bg-white/10 backdrop-blur-xl rounded-2xl overflow-hidden border border-white/20 hover:border-purple-400/50 transition-all duration-300"
                  >
                    {/* Contract Header */}
                    <div className="p-5 border-b border-white/10">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center">
                            <Briefcase size={18} className="text-white" />
                          </div>
                          <div>
                            <h3 className="text-white font-semibold line-clamp-1">
                              {contract.title || `Contract #${contract.id}`}
                            </h3>
                            <p className="text-white/40 text-xs">
                              {new Date(contract.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                        <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${getStatusColor(contract.status)} border`}>
                          {getStatusIcon(contract.status)}
                          <span>{getStatusText(contract.status)}</span>
                        </div>
                      </div>

                      {/* Parties */}
                      <div className="flex items-center justify-between text-sm mt-3">
                        <div className="flex items-center gap-2">
                          <User size={14} className="text-purple-400" />
                          <span className="text-white/70">{contract.client?.username || "Client"}</span>
                        </div>
                        <span className="text-white/30">→</span>
                        <div className="flex items-center gap-2">
                          <User size={14} className="text-pink-400" />
                          <span className="text-white/70">{contract.freelancer?.username || "Freelancer"}</span>
                        </div>
                      </div>
                    </div>

                    {/* Contract Body */}
                    <div className="p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <DollarSign size={16} className="text-emerald-400" />
                          <span className="text-white font-semibold">
                            {contract.total_amount} {contract.currency || "USD"}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Clock size={14} className="text-white/40" />
                          <span className="text-white/40 text-xs">
                            {contract.days_until_deadline > 0 
                              ? `${contract.days_until_deadline} days left` 
                              : "Deadline passed"}
                          </span>
                        </div>
                      </div>

                      {contract.skill && (
                        <div className="flex items-center gap-2">
                          <Hash size={14} className="text-white/40" />
                          <span className="text-white/60 text-sm">{contract.skill.name}</span>
                        </div>
                      )}

                      {contract.blockchain_tx_hash && (
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                          <span className="text-white/40 text-xs">Verified on Blockchain</span>
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="p-4 border-t border-white/10 flex gap-3">
                      <button
                        onClick={() => setSelectedContract(contract)}
                        className="flex-1 py-2 rounded-xl bg-white/10 text-white/80 hover:bg-white/20 transition text-sm font-medium"
                      >
                        View Details
                      </button>
                      
                      {/* ✅ زر إكمال العقد - يظهر فقط للعقود النشطة (active) */}
                      {contract.status === "active" && (
                        <button
                          onClick={() => completeContract(contract.id)}
                          disabled={completingId === contract.id}
                          className="flex-1 py-2 rounded-xl bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50"
                        >
                          {completingId === contract.id ? (
                            <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            <CheckSquare size={16} />
                          )}
                          {completingId === contract.id ? "Completing..." : "Complete"}
                        </button>
                      )}
                      
                      {/* ✅ زر التقييم - يظهر فقط للعقود المكتملة */}
                      {contract.status === "completed" && (
                        <button
                          onClick={() => openRatingModal(contract.id)}
                          className="flex-1 py-2 rounded-xl bg-yellow-500/20 text-yellow-400 hover:bg-yellow-500/30 transition text-sm font-medium flex items-center justify-center gap-2"
                        >
                          <Star size={16} />
                          Rate
                        </button>
                      )}
                      
                      {(contract.status === "pending" || contract.status === "partially_signed") && (
                        <button
                          onClick={() => handleSignClick(contract.id)}
                          className="flex-1 py-2 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:shadow-lg hover:shadow-purple-500/30 transition text-sm font-medium flex items-center justify-center gap-2"
                        >
                          <FileSignature size={16} />
                          Sign
                        </button>
                      )}
                    {contract.chatroom?.id && (
  <button
    onClick={() => goToChat(contract.chatroom.id)}
    className="flex-1 py-2 rounded-xl bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30 transition text-sm font-medium flex items-center justify-center gap-2"
  >
    <MessageCircle size={16} />
    Chat
  </button>
)}
                    
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* Contract Details Modal */}
      <AnimatePresence>
        {selectedContract && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setSelectedContract(null)}
          >
            <motion.div
              className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl shadow-2xl w-[95%] max-w-2xl max-h-[90vh] overflow-y-auto border border-white/20"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="sticky top-0 bg-gradient-to-r from-purple-600 to-pink-600 p-5 rounded-t-2xl">
                <div className="flex justify-between items-center">
                  <h2 className="text-xl font-bold text-white">Contract Details</h2>
                  <button
                    onClick={() => setSelectedContract(null)}
                    className="p-1 hover:bg-white/20 rounded-lg transition"
                  >
                    <XCircle size={20} className="text-white" />
                  </button>
                </div>
                <p className="text-white/70 text-sm mt-1">Contract #{selectedContract.id}</p>
              </div>

              {/* Modal Body */}
              <div className="p-6 space-y-5">
                {/* Status Badge */}
                <div className={`flex items-center gap-2 px-3 py-2 rounded-xl ${getStatusColor(selectedContract.status)} border w-fit`}>
                  {getStatusIcon(selectedContract.status)}
                  <span className="font-medium">{getStatusText(selectedContract.status)}</span>
                </div>

                {/* Basic Info */}
                <div className="space-y-3">
                  <h3 className="text-white font-semibold text-lg">{selectedContract.title || "Contract Agreement"}</h3>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Client</p>
                      <p className="text-white font-medium">{selectedContract.client?.username || "N/A"}</p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Freelancer</p>
                      <p className="text-white font-medium">{selectedContract.freelancer?.username || "N/A"}</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Amount</p>
                      <p className="text-emerald-400 font-bold text-lg">
                        {selectedContract.total_amount} {selectedContract.currency || "USD"}
                      </p>
                    </div>
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Deadline</p>
                      <p className="text-white">{new Date(selectedContract.deadline).toLocaleDateString()}</p>
                    </div>
                  </div>

                  {selectedContract.skill && (
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Skill</p>
                      <p className="text-white">{selectedContract.skill.name}</p>
                    </div>
                  )}

                  {selectedContract.description && (
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Description</p>
                      <p className="text-white/80 text-sm">{selectedContract.description}</p>
                    </div>
                  )}

                  {selectedContract.terms && (
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Terms & Conditions</p>
                      <p className="text-white/70 text-sm whitespace-pre-wrap">{selectedContract.terms}</p>
                    </div>
                  )}

                  {selectedContract.contract_hash && (
                    <div className="bg-white/5 rounded-xl p-3">
                      <p className="text-white/40 text-xs mb-1">Contract Hash</p>
                      <div className="flex items-center gap-2">
                        <code className="text-white/60 text-xs font-mono break-all flex-1">
                          {selectedContract.contract_hash}
                        </code>
                        <button
                          onClick={() => copyToClipboard(selectedContract.contract_hash)}
                          className="p-1 hover:bg-white/10 rounded transition"
                        >
                          {copied ? <Check size={14} className="text-green-400" /> : <Copy size={14} className="text-white/40" />}
                        </button>
                      </div>
                    </div>
                  )}

                  {selectedContract.blockchain_tx_hash && (
                    <div className="bg-green-500/10 rounded-xl p-3 border border-green-500/20">
                      <div className="flex items-center gap-2 mb-1">
                        <Shield size={14} className="text-green-400" />
                        <p className="text-green-400 text-xs font-medium">Blockchain Verified</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <code className="text-white/60 text-xs font-mono break-all flex-1">
                          Tx: {selectedContract.blockchain_tx_hash}
                        </code>
                        <button
                          onClick={() => window.open(`https://sepolia.etherscan.io/tx/${selectedContract.blockchain_tx_hash}`, '_blank')}
                          className="p-1 hover:bg-white/10 rounded transition"
                        >
                          <ExternalLink size={14} className="text-white/40" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>

                {/* Signatures Status */}
                <div className="space-y-2">
                  <h4 className="text-white font-medium flex items-center gap-2">
                    <FileSignature size={16} className="text-purple-400" />
                    Signatures
                  </h4>
                  <div className="flex items-center gap-3">
                    <div className="flex-1 bg-white/5 rounded-xl p-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${selectedContract.client_signature ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'}`}></div>
                        <span className="text-white/60 text-sm">Client: {selectedContract.client?.username}</span>
                      </div>
                      <p className="text-xs text-white/40 mt-1">
                        {selectedContract.client_signature ? "✓ Signed" : "Awaiting signature"}
                      </p>
                    </div>
                    <div className="flex-1 bg-white/5 rounded-xl p-3">
                      <div className="flex items-center gap-2">
                        <div className={`w-2 h-2 rounded-full ${selectedContract.freelancer_signature ? 'bg-green-400' : 'bg-yellow-400 animate-pulse'}`}></div>
                        <span className="text-white/60 text-sm">Freelancer: {selectedContract.freelancer?.username}</span>
                      </div>
                      <p className="text-xs text-white/40 mt-1">
                        {selectedContract.freelancer_signature ? "✓ Signed" : "Awaiting signature"}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Timestamps */}
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between items-center">
                    <span className="text-white/40">Created</span>
                    <span className="text-white/60">{new Date(selectedContract.created_at).toLocaleString()}</span>
                  </div>
                  {selectedContract.signed_at && (
                    <div className="flex justify-between items-center">
                      <span className="text-white/40">Signed</span>
                      <span className="text-white/60">{new Date(selectedContract.signed_at).toLocaleString()}</span>
                    </div>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex gap-3 pt-4 border-t border-white/10">
                  {(selectedContract.status === "pending" || selectedContract.status === "partially_signed") && (
                    <button
                      onClick={() => handleSignClick(selectedContract.id)}
                      className="flex-1 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:shadow-lg hover:shadow-purple-500/30 transition flex items-center justify-center gap-2"
                    >
                      <FileSignature size={18} />
                      Sign Contract
                    </button>
                  )}
                  
                  {/* ✅ زر إكمال العقد في المودال */}
                  {selectedContract.status === "active" && (
                    <button
                      onClick={() => completeContract(selectedContract.id)}
                      disabled={completingId === selectedContract.id}
                      className="flex-1 py-3 rounded-xl bg-emerald-500/20 text-emerald-400 font-semibold hover:bg-emerald-500/30 transition flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {completingId === selectedContract.id ? (
                        <div className="w-4 h-4 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
                      ) : (
                        <CheckSquare size={18} />
                      )}
                      {completingId === selectedContract.id ? "Completing..." : "Complete Contract"}
                    </button>
                  )}
                  
                  {selectedContract.status === "completed" && (
                    <button
                      onClick={() => openRatingModal(selectedContract.id)}
                      className="flex-1 py-3 rounded-xl bg-yellow-500/20 text-yellow-400 font-semibold hover:bg-yellow-500/30 transition flex items-center justify-center gap-2"
                    >
                      <Star size={18} />
                      Rate Contract
                    </button>
                  )}
                  {selectedContract.room_id && (
                    <button
                      onClick={() => goToChat(selectedContract.room_id)}
                      className="flex-1 py-3 rounded-xl bg-emerald-500/20 text-emerald-400 font-semibold hover:bg-emerald-500/30 transition flex items-center justify-center gap-2"
                    >
                      <MessageCircle size={18} />
                      Open Chat
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Biometric Verification Modal */}
      <AnimatePresence>
        {showBiometric && (
          <BiometricModal
            onSuccess={handleBiometricSuccess}
            onClose={() => setShowBiometric(false)}
            purpose="sign_contract"
            contractId={selectedContractId}
          />
        )}
      </AnimatePresence>

      {/* Sign Confirmation Modal */}
      <AnimatePresence>
        {biometricVerified && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 w-[90%] max-w-md text-center border border-white/20"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
            >
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
                <Shield size={40} className="text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Identity Verified</h2>
              <p className="text-white/60 mb-6">
                Your biometric identity has been verified. You can now digitally sign this contract.
              </p>
              <div className="flex gap-4">
                <button
                  onClick={confirmSign}
                  disabled={signingInProgress}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:shadow-lg transition flex items-center justify-center gap-2"
                >
                  {signingInProgress ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      Signing...
                    </>
                  ) : (
                    <>
                      <FileSignature size={18} />
                      Sign Contract
                    </>
                  )}
                </button>
                <button
                  onClick={() => {
                    setBiometricVerified(false);
                    setBiometricData(null);
                  }}
                  className="flex-1 py-3 rounded-xl bg-white/10 text-white/80 font-semibold hover:bg-white/20 transition"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ✅ Rating Modal */}
      <AnimatePresence>
        {ratingModal.open && (
          <motion.div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setRatingModal({ open: false, contractId: null, rating: 0, feedback: "" })}
          >
            <motion.div
              className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 w-[90%] max-w-md text-center border border-white/20"
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-br from-yellow-500 to-orange-600 flex items-center justify-center">
                <span className="text-4xl">⭐</span>
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">Rate this Contract</h2>
              <p className="text-white/60 mb-6">Your feedback helps build trust in the community</p>
              
              {/* Stars Rating */}
              <div className="flex justify-center gap-3 mb-6">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setRatingModal({ ...ratingModal, rating: star })}
                    className="text-5xl transition-transform hover:scale-110"
                  >
                    <span className={star <= ratingModal.rating ? "text-yellow-400" : "text-gray-500"}>
                      ★
                    </span>
                  </button>
                ))}
              </div>
              
              {/* Feedback Textarea */}
              <textarea
                placeholder="Write your feedback (optional)..."
                value={ratingModal.feedback}
                onChange={(e) => setRatingModal({ ...ratingModal, feedback: e.target.value })}
                rows="3"
                className="w-full p-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-white/40 resize-none mb-6"
              />
              
              <div className="flex gap-4">
                <button
                  onClick={submitRating}
                  disabled={ratingLoading || ratingModal.rating === 0}
                  className="flex-1 py-3 rounded-xl bg-gradient-to-r from-yellow-500 to-orange-600 text-white font-semibold hover:shadow-lg transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {ratingLoading ? (
                    <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  ) : (
                    "Submit Rating"
                  )}
                </button>
                <button
                  onClick={() => setRatingModal({ open: false, contractId: null, rating: 0, feedback: "" })}
                  className="flex-1 py-3 rounded-xl bg-white/10 text-white/80 font-semibold hover:bg-white/20 transition"
                >
                  Cancel
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}