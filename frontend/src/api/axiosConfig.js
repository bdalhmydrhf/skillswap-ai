// frontend/src/api/axiosConfig.js
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8001/api/",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: false,
});

// ✅ إضافة التوكن تلقائيًا من localStorage إذا موجود
api.interceptors.request.use((config) => {
  const access = localStorage.getItem("access_token");
  if (access) {
    config.headers.Authorization = `Bearer ${access}`;
  }
  
  // ✅ مهم: إذا كان FormData، نترك axios يحدد الـ Content-Type بنفسه
  if (config.data instanceof FormData) {
    delete config.headers["Content-Type"];
  }
  
  return config;
}, (error) => {
  return Promise.reject(error);
});

export default api;
