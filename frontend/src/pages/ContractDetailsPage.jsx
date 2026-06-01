// src/pages/ContractDetailsPage.jsx
import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  FileSignature, Shield, User, DollarSign, Calendar, 
  CheckCircle, XCircle, Clock, ExternalLink, ArrowLeft,
  Loader2, AlertTriangle, FileText, ListChecks
} from "lucide-react";
import api from "../api/axiosConfig";
import BlockchainStatus from "../Components/BlockchainStatus";

export default function ContractDetailsPage() {
  const { contractId } = useParams();
  const navigate = useNavigate();
  const [contract, setContract] = useState(null);
  const [loading, setLoading] = useState(true);
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");

  useEffect(() => {
    fetchContract();
  }, [contractId]);

  const fetchContract = async () => {
    try {
      const response = await api.get(`/contracts/${contractId}/`);
      setContract(response.data);
    } catch (error) {
      console.error("Error fetching contract:", error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusConfig = (status) => {
    const configs = {
      pending: { color: "text-yellow-400", bg: "bg-yellow-500/20", icon: Clock, text: "بانتظار التوقيع" },
      partially_signed: { color: "text-orange-400", bg: "bg-orange-500/20", icon: FileSignature, text: "تم التوقيع جزئياً" },
      active: { color: "text-green-400", bg: "bg-green-500/20", icon: CheckCircle, text: "نشط" },
      completed: { color: "text-emerald-400", bg: "bg-emerald-500/20", icon: CheckCircle, text: "مكتمل" },
      cancelled: { color: "text-red-400", bg: "bg-red-500/20", icon: XCircle, text: "ملغي" },
    };
    return configs[status] || configs.pending;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <Loader2 className="w-12 h-12 text-purple-400 animate-spin" />
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 flex items-center justify-center">
        <AlertTriangle className="w-16 h-16 text-yellow-400" />
        <p className="text-white text-xl mt-4">العقد غير موجود</p>
      </div>
    );
  }

  const statusConfig = getStatusConfig(contract.status);
  const StatusIcon = statusConfig.icon;
  const userRole = contract.client?.id === currentUser.id ? 'client' : 
                    contract.freelancer?.id === currentUser.id ? 'freelancer' : null;
  const hasSigned = userRole === 'client' ? contract.client_signature : contract.freelancer_signature;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-indigo-900 pt-24 pb-12 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <button onClick={() => navigate(-1)} className="mb-6 flex items-center gap-2 text-white/60 hover:text-white transition">
          <ArrowLeft size={20} /> رجوع
        </button>

        {/* Contract Card */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white/10 backdrop-blur-xl rounded-2xl border border-white/20 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-purple-600/30 to-pink-600/30 p-6 border-b border-white/10">
            <div className="flex justify-between items-start flex-wrap gap-4">
              <div>
                <h1 className="text-2xl font-bold text-white">{contract.title || `عقد #${contract.id}`}</h1>
                <p className="text-white/40 text-sm mt-1">تاريخ الإنشاء: {new Date(contract.created_at).toLocaleDateString('ar-EG')}</p>
              </div>
              <div className={`flex items-center gap-2 px-4 py-2 rounded-full ${statusConfig.bg}`}>
                <StatusIcon size={18} className={statusConfig.color} />
                <span className={`text-sm font-medium ${statusConfig.color}`}>{statusConfig.text}</span>
              </div>
            </div>
          </div>

          {/* Body */}
          <div className="p-6 space-y-6">
            {/* الأطراف */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><User size={14} /> العميل</div>
                <p className="text-white font-medium">{contract.client?.username || "غير معروف"}</p>
                {contract.client_signature && <div className="flex items-center gap-1 mt-2 text-green-400 text-xs"><CheckCircle size={12} /> تم التوقيع</div>}
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><User size={14} /> المستقل</div>
                <p className="text-white font-medium">{contract.freelancer?.username || "غير معروف"}</p>
                {contract.freelancer_signature && <div className="flex items-center gap-1 mt-2 text-green-400 text-xs"><CheckCircle size={12} /> تم التوقيع</div>}
              </div>
            </div>

            {/* المبلغ والموعد */}
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><DollarSign size={14} /> المبلغ</div>
                <p className="text-white text-xl font-bold">{contract.total_amount} {contract.currency || "USD"}</p>
              </div>
              <div className="bg-white/5 rounded-xl p-4">
                <div className="flex items-center gap-2 text-white/40 text-sm mb-2"><Calendar size={14} /> الموعد النهائي</div>
                <p className="text-white">
  {contract.deadline ? new Date(contract.deadline).toLocaleDateString('ar-EG') : "لم يتم تحديده"}
</p>
              </div>
            </div>

            {/* الوصف */}
            {contract.description && (
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-white/40 text-sm mb-2 flex items-center gap-2"><FileText size={14} /> الوصف</p>
                <p className="text-white/80">{contract.description}</p>
              </div>
            )}

            {/* المخرجات (Deliverables) */}
            {contract.deliverables && contract.deliverables.length > 0 && (
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-white/40 text-sm mb-2 flex items-center gap-2"><ListChecks size={14} /> المخرجات المطلوبة</p>
                <ul className="list-disc list-inside text-white/70 space-y-1">
                  {contract.deliverables.map((item, idx) => (
                    <li key={idx}>{item}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* الشروط */}
            {contract.terms && (
              <div className="bg-white/5 rounded-xl p-4">
                <p className="text-white/40 text-sm mb-2 flex items-center gap-2"><Shield size={14} /> الشروط والأحكام</p>
                <p className="text-white/70 text-sm whitespace-pre-wrap">{contract.terms}</p>
              </div>
            )}

            {/* معلومات البلوكشين */}
            {contract.blockchain_tx_hash && (
              <div className="bg-green-500/10 rounded-xl p-4 border border-green-500/20">
                <div className="flex items-center gap-2 mb-2"><Shield size={14} className="text-green-400" /><p className="text-green-400 text-sm font-medium">موثق على البلوكشين</p></div>
                <div className="flex items-center gap-2">
                  <code className="text-white/60 text-xs font-mono break-all flex-1">{contract.blockchain_tx_hash}</code>
                  <button onClick={() => window.open(`https://sepolia.etherscan.io/tx/${contract.blockchain_tx_hash}`, '_blank')} className="p-1 hover:bg-white/10 rounded">
                    <ExternalLink size={14} className="text-white/40" />
                  </button>
                </div>
              </div>
            )}
       {/* ✅✅✅ أضيفي مكون حالة البلوكشين هنا ✅✅✅ */}
       <BlockchainStatus contractId={contract.id} />
            {/* زر التوقيع */}
            {(contract.status === "pending" || contract.status === "partially_signed") && !hasSigned && userRole && (
              <button 
                onClick={() => navigate(`/contracts/${contractId}/sign`, { state: { contract } })}
                className="w-full py-4 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold text-lg hover:shadow-lg hover:shadow-purple-500/30 transition flex items-center justify-center gap-3"
              >
                <FileSignature size={20} />
                توقيع العقد
              </button>
            )}

            {(contract.status === "active" || contract.status === "completed") && (
              <div className="text-center py-4">
                <CheckCircle size={48} className="text-green-400 mx-auto mb-2" />
                <p className="text-white font-semibold">العقد موقع ونشط</p>
              </div>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
}
