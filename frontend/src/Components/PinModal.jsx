// src/components/PinModal.jsx
import React, { useState, useRef } from 'react';
import { motion } from 'framer-motion';
import { Key, Shield, AlertCircle, Loader2 } from 'lucide-react';
import api from '../api/axiosConfig';

const PinModal = ({ onSuccess, onClose }) => {
  const [pin, setPin] = useState(['', '', '', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRefs = useRef([]);

  const handleChange = (index, value) => {
    if (value.length > 1) return;
    if (value && !/^\d*$/.test(value)) return;
    
    const newPin = [...pin];
    newPin[index] = value;
    setPin(newPin);
    
    // الانتقال التلقائي للحقل التالي
    if (value && index < 7) {
      inputRefs.current[index + 1].focus();
    }
  };

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !pin[index] && index > 0) {
      inputRefs.current[index - 1].focus();
    }
  };

  const handleSubmit = async () => {
    const pinCode = pin.join('');
    if (pinCode.length !== 8) {
      setError('Please enter all 8 digits');
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await api.post('/biometric/verify-pin/', { pin: pinCode });
      if (response.data.success) {
        onSuccess();
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || 'Invalid PIN. Please try again.';
      setError(errorMsg);
      // مسح الحقول عند الخطأ
      setPin(['', '', '', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <motion.div
        initial={{ scale: 0.9, opacity: 0, y: 20 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.9, opacity: 0, y: 20 }}
        className="bg-gradient-to-br from-gray-900 to-purple-900 rounded-2xl p-6 max-w-md w-full mx-4 border border-purple-500/30"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-center mb-6">
          <div className="w-16 h-16 mx-auto mb-3 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center">
            <Shield size={32} className="text-white" />
          </div>
          <h3 className="text-xl font-bold text-white">Enter Security PIN</h3>
          <p className="text-white/50 text-sm mt-1">Enter your 8-digit PIN to sign this contract</p>
        </div>

        <div className="flex justify-center gap-3 mb-6">
          {[...Array(8)].map((_, i) => (
            <input
              key={i}
              ref={el => inputRefs.current[i] = el}
              type="password"
              maxLength="1"
              className="w-12 h-14 text-center text-2xl font-bold rounded-xl bg-white/10 border border-purple-500/50 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              value={pin[i]}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              autoFocus={i === 0}
            />
          ))}
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-red-500/20 border border-red-500/50 flex items-center gap-2">
            <AlertCircle size={18} className="text-red-400" />
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 text-white font-semibold hover:shadow-lg transition disabled:opacity-50"
        >
          {loading ? <Loader2 size={20} className="animate-spin mx-auto" /> : 'Verify PIN'}
        </button>

        <button onClick={onClose} className="w-full mt-3 py-2 rounded-xl border border-white/30 text-white/70 hover:bg-white/10 transition">
          Cancel
        </button>
      </motion.div>
    </motion.div>
  );
};

export default PinModal;
