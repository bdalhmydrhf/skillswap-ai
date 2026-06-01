// src/components/BlockchainStatus.jsx
import React, { useState, useEffect } from "react";
import api from "../api/axiosConfig";

export default function BlockchainStatus({ contractId }) {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchBlockchainStatus();
  }, [contractId]);

  const fetchBlockchainStatus = async () => {
    try {
      const res = await api.get(`/contracts/${contractId}/blockchain-status/`);
      setStatus(res.data);
    } catch (error) {
      console.error("Error fetching blockchain status:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!status || !status.blockchain_tx_hash) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 mt-4">
        <p className="text-yellow-400">
          ⏳ العقد لم يسجل بعد على البلوكشين (يتم التسجيل تلقائياً بعد توقيع الطرفين)
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-r from-purple-900 to-blue-900 rounded-lg p-5 mt-4 border border-purple-500">
      <h3 className="text-xl font-bold text-white mb-3">
        🔗 بلوكشين إيثيريوم
      </h3>
      
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-gray-300">الحالة:</span>
          <span className={`px-2 py-1 rounded-full text-sm ${
            status.is_confirmed 
              ? "bg-green-500 text-white" 
              : "bg-yellow-500 text-black"
          }`}>
            {status.is_confirmed ? "✅ مؤكد" : "⏳ في انتظار التأكيد"}
          </span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-300">شبكة البلوكشين:</span>
          <span className="text-white font-mono">{status.network || "Sepolia"}</span>
        </div>

        <div className="flex justify-between items-center">
          <span className="text-gray-300">هاش المعاملة:</span>
          <span className="text-white font-mono text-sm break-all">
            {status.blockchain_tx_hash?.slice(0, 16)}...
          </span>
        </div>

        {status.block_number && (
          <div className="flex justify-between items-center">
            <span className="text-gray-300">رقم الكتلة:</span>
            <span className="text-white">{status.block_number}</span>
          </div>
        )}

        <div className="mt-3">
          <a
            href={`https://sepolia.etherscan.io/tx/${status.blockchain_tx_hash}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-300 hover:text-blue-100 underline flex items-center gap-2"
          >
            🔍 عرض على Etherscan
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
          </a>
        </div>
      </div>
    </div>
  );
}
