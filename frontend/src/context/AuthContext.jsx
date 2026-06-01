// frontend/src/context/AuthContext.jsx
import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../api/axiosConfig';

const AuthContext = createContext();

export function useAuth() {
  return useContext(AuthContext);
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [token, setToken] = useState(localStorage.getItem('access_token'));

  useEffect(() => {
    if (token) {
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await api.get('/users/me/');
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await api.post('/token/', { email, password });
      localStorage.setItem('access_token', response.data.access);
      localStorage.setItem('refresh_token', response.data.refresh);
      localStorage.setItem('user_email', email);
      setToken(response.data.access);
      await fetchUser();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'فشل تسجيل الدخول' };
    }
  };

  const register = async (username, email, password) => {
    try {
      await api.post('/register/', { username, email, password });
      return await login(email, password);
    } catch (error) {
      return { success: false, error: error.response?.data?.error || 'فشل التسجيل' };
    }
  };

  // ✅ الدالة الصحيحة للبصمة (تدعم جميع الأنواع)
  const biometricLogin = async (biometricData, biometricType = 'voice') => {
    try {
      const formData = new FormData();
      formData.append('biometric_type', biometricType);
      
      // معالجة البيانات حسب النوع
      if (biometricData instanceof Blob) {
        formData.append('audio', biometricData, 'recording.wav');
      } else if (typeof biometricData === 'string') {
        formData.append('biometric_data', biometricData);
      }
      
      const userEmail = localStorage.getItem('user_email') || '';
      if (userEmail) {
        formData.append('email', userEmail);
      }

      const response = await api.post('/biometric/login/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // ✅ التصحيح: استخدم 'access' بدلاً من 'token'
      if (response.data.success && response.data.access) {
        localStorage.setItem('access_token', response.data.access);
        localStorage.setItem('refresh_token', response.data.refresh || response.data.access);
        localStorage.setItem('user_email', response.data.email || userEmail);
        localStorage.setItem('user_id', response.data.user_id);
        localStorage.setItem('biometric_type', biometricType);
        setToken(response.data.access);
        await fetchUser();
        return { success: true, data: response.data };
      }
      
      return { success: false, error: response.data.message || 'فشل التحقق من البصمة' };
    } catch (error) {
      console.error('Biometric login error:', error);
      return { 
        success: false, 
        error: error.response?.data?.detail || error.response?.data?.error || 'فشل تسجيل الدخول بالبصمة' 
      };
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_email');
    localStorage.removeItem('user_id');
    localStorage.removeItem('biometric_type');
    localStorage.removeItem('user');
    setToken(null);
    setUser(null);
  };

  const value = {
    user,
    loading,
    login,
    register,
    biometricLogin,
    logout,
    isAuthenticated: !!user,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
