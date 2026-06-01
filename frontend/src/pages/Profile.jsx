// src/pages/Profile.jsx - النسخة النهائية مع التحقق بالوثائق
import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { CheckCircle, Shield, Loader2 } from "lucide-react";
import api from "../api/axiosConfig";

// ✅ أضيفي هذا السطر خارج الكود (ثابت)
const BACKEND_URL = "http://127.0.0.1:8001";

export default function Profile() {
  const navigate = useNavigate();
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({});
  const [uploading, setUploading] = useState(false);
  const [verificationStatus, setVerificationStatus] = useState(null);
  
  const profileInputRef = useRef(null);
  const coverInputRef = useRef(null);

  // ✅ دالة جلب حالة التحقق
  const fetchVerificationStatus = async () => {
    try {
      const response = await api.get("/verification/status/");
      setVerificationStatus(response.data);
    } catch (error) {
      console.error("Error fetching verification status:", error);
    }
  };

  // ✅ دالة جلب بيانات المستخدم مع تصحيح URL الصورة
  const fetchUser = async () => {
    try {
      const response = await api.get("/users/me/");
      let userData = response.data;
      
      // ✅ تصحيح URL الصورة إذا كان نسبياً
      if (userData.profile_image && !userData.profile_image.startsWith('http')) {
        userData.profile_image = `${BACKEND_URL}${userData.profile_image}`;
      }
      if (userData.cover_image && !userData.cover_image.startsWith('http')) {
        userData.cover_image = `${BACKEND_URL}${userData.cover_image}`;
      }
      
      setUser(userData);
      setFormData(userData);
    } catch (error) {
      console.error("Error fetching user:", error);
    }
  };

  // جلب بيانات المستخدم عند تحميل الصفحة
  useEffect(() => {
    const loadUser = async () => {
      setLoading(true);
      await fetchUser();
      await fetchVerificationStatus();
      setLoading(false);
    };
    loadUser();
  }, []);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSave = async () => {
    try {
      await api.put("/users/me/profile/", {
        bio: formData.bio,
        city: formData.city,
        country: formData.country,
        phone: formData.phone,
        headline: formData.headline,
      });
      
      await fetchUser(); // ✅ إعادة جلب البيانات
      setIsEditing(false);
      alert("✅ Profile updated successfully");
    } catch (error) {
      console.error("Error updating profile:", error);
      alert("❌ Failed to update profile");
    }
  };

  // ✅ رفع الصورة الشخصية
  const uploadProfileImage = async (file) => {
    if (!file) return;
    
    setUploading(true);
    const formDataUpload = new FormData();
    formDataUpload.append('profile_image', file);
    
    try {
      const response = await api.post('/profile/upload-image/', formDataUpload, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (response.data.success) {
        await fetchUser(); // ✅ إعادة جلب البيانات بعد الرفع
        alert("✅ Profile image updated successfully");
      }
    } catch (error) {
      console.error("Upload failed:", error);
      alert("❌ Failed to upload image");
    } finally {
      setUploading(false);
    }
  };

  // ✅ رفع صورة الغلاف
  const uploadCoverImage = async (file) => {
    if (!file) return;
    
    setUploading(true);
    const formDataUpload = new FormData();
    formDataUpload.append('cover_image', file);
    
    try {
      const response = await api.post('/profile/upload-cover/', formDataUpload, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      if (response.data.success) {
        await fetchUser(); // ✅ إعادة جلب البيانات بعد الرفع
        alert("✅ Cover image updated successfully");
      }
    } catch (error) {
      console.error("Upload failed:", error);
      alert("❌ Failed to upload cover");
    } finally {
      setUploading(false);
    }
  };

  // ✅ الحصول على حالة التحقق
  const getVerificationBadge = () => {
    if (!verificationStatus?.has_verification) {
      return null;
    }
    
    if (verificationStatus.status === 'approved') {
      return (
        <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-green-500/20 text-green-400 text-xs">
          <CheckCircle size={12} />
          <span>Verified Identity</span>
        </div>
      );
    }
    
    if (verificationStatus.status === 'pending' || verificationStatus.status === 'under_review') {
      return (
        <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-yellow-500/20 text-yellow-400 text-xs">
          <Loader2 size={12} className="animate-spin" />
          <span>Verification Pending</span>
        </div>
      );
    }
    
    if (verificationStatus.status === 'rejected') {
      return (
        <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-red-500/20 text-red-400 text-xs">
          <Shield size={12} />
          <span>Verification Failed</span>
        </div>
      );
    }
    
    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-yellow-400 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900">
        <p className="text-white">User not found</p>
      </div>
    );
  }

  // ✅ إضافة timestamp لمنع caching
  const profileImageUrl = user.profile_image 
    ? `${user.profile_image}?t=${Date.now()}` 
    : "https://i.pravatar.cc/200";
    
  const coverImageUrl = user.cover_image 
    ? `${user.cover_image}?t=${Date.now()}` 
    : "https://images.unsplash.com/photo-1503264116251-35a269479413";

  return (
    <>
      <div className="min-h-screen px-6 pt-24 pb-16 text-white bg-gradient-to-br from-blue-900 via-indigo-900 to-purple-900">
        {/* صورة الغلاف */}
        <div
          className="relative w-full bg-center bg-cover shadow-lg h-60 rounded-b-3xl group cursor-pointer"
          style={{ backgroundImage: `url(${coverImageUrl})` }}
          onClick={() => coverInputRef.current?.click()}
        >
          <div className="absolute inset-0 bg-black/40 rounded-b-3xl group-hover:bg-black/30 transition"></div>
          <div className="absolute bottom-4 right-4 bg-black/50 backdrop-blur-sm rounded-full p-2 hover:bg-black/70 transition">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </div>
          <input
            type="file"
            ref={coverInputRef}
            accept="image/*"
            className="hidden"
            onChange={(e) => uploadCoverImage(e.target.files[0])}
            disabled={uploading}
          />
        </div>

        {/* معلومات المستخدم */}
        <div className="max-w-5xl mx-auto mt-[-5rem] relative z-10 bg-white/10 backdrop-blur-md rounded-3xl p-8 shadow-2xl border border-white/20">
          <div className="flex flex-col items-center gap-6 md:flex-row md:gap-10">
            
            {/* الصورة الشخصية */}
            <div className="relative group cursor-pointer" onClick={() => profileInputRef.current?.click()}>
              <img
                src={profileImageUrl}
                alt="Profile"
                className="object-cover w-40 h-40 border-4 border-yellow-400 rounded-full shadow-xl"
                onError={(e) => {
                  console.error("❌ Image failed to load:", profileImageUrl);
                  e.target.src = "https://i.pravatar.cc/200";
                }}
              />
              <div className="absolute inset-0 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              {uploading && (
                <div className="absolute inset-0 bg-black/70 rounded-full flex items-center justify-center">
                  <div className="w-8 h-8 border-2 border-yellow-400 border-t-transparent rounded-full animate-spin"></div>
                </div>
              )}
            </div>
            
            <input
              type="file"
              ref={profileInputRef}
              accept="image/*"
              className="hidden"
              onChange={(e) => uploadProfileImage(e.target.files[0])}
              disabled={uploading}
            />
            
            <div className="text-center md:text-left">
              <div className="flex items-center gap-2 flex-wrap justify-center md:justify-start">
                <h2 className="text-3xl font-bold">{user.username}</h2>
                {getVerificationBadge()}
              </div>
              <p className="mt-1 text-yellow-300">
                {user.city || "Not specified"} • {user.country || "Not specified"}
              </p>
              <p className="mt-2 text-sm text-gray-300">
                {user.bio ? user.bio.substring(0, 100) : "Hello! This is my profile"}
              </p>
            </div>
          </div>

          {/* المهارات */}
          <div className="mt-8">
            <h3 className="mb-3 text-xl font-semibold">Skills</h3>
            <div className="flex flex-wrap gap-3">
              {user.skills?.length > 0 ? (
                user.skills.map((skill, index) => (
                  <span
                    key={index}
                    className="px-4 py-1 font-semibold text-black transition duration-200 transform rounded-full shadow-lg bg-gradient-to-r from-yellow-400 to-yellow-500 hover:scale-105"
                  >
                    {typeof skill === 'object' ? skill.name : skill}
                  </span>
                ))
              ) : (
                <p className="text-gray-400">No skills added</p>
              )}
            </div>
          </div>

          {/* الإحصائيات */}
          <div className="grid grid-cols-2 gap-6 mt-10 text-center md:grid-cols-3">
            <div className="p-4 transition shadow-lg bg-white/10 rounded-2xl hover:bg-white/20">
              <h4 className="text-2xl font-bold text-yellow-400">{user.contracts_count || 0}</h4>
              <p className="text-sm text-gray-300">Contracts</p>
            </div>
            <div className="p-4 transition shadow-lg bg-white/10 rounded-2xl hover:bg-white/20">
            <h4 className="text-2xl font-bold text-yellow-400">{Math.round(user.completion_rate || 0)}%</h4>
              <p className="text-sm text-gray-300">Completion Rate</p>
            </div>
            <div className="p-4 transition shadow-lg bg-white/10 rounded-2xl hover:bg-white/20">
              <h4 className="text-2xl font-bold text-yellow-400">{user.avg_rating || 0}⭐</h4>
              <p className="text-sm text-gray-300">Average Rating</p>
            </div>
            <div className="p-4 transition shadow-lg bg-white/10 rounded-2xl hover:bg-white/20">
              <h4 className="text-2xl font-bold text-yellow-400">{user.trust_score || 0}</h4>
              <p className="text-sm text-gray-300">Trust Score</p>
            </div>
            <div className="p-4 transition shadow-lg bg-white/10 rounded-2xl hover:bg-white/20">
              <h4 className="text-2xl font-bold text-yellow-400">{user.avg_response_time || 0}h</h4>
              <p className="text-sm text-gray-300">Avg Response Time</p>
            </div>
          </div>

          {/* ✅ زر التحقق بالوثائق - يظهر فقط إذا لم يكن موثقاً */}
          {(!verificationStatus?.has_verification || verificationStatus?.status === 'rejected') && (
            <div className="mt-6 text-center">
              <button
                onClick={() => navigate('/verify-identity')}
                className="px-6 py-3 font-bold text-white transition rounded-full shadow-lg bg-gradient-to-r from-blue-500 to-purple-600 hover:scale-105 flex items-center justify-center gap-2 mx-auto"
              >
                <Shield size={18} />
                Verify Identity with Documents
              </button>
              <p className="text-white/40 text-xs mt-2">
                Upload ID and selfie to increase trust score
              </p>
            </div>
          )}

          {/* زر تعديل */}
          <div className="mt-10 text-center">
            <button
              onClick={() => setIsEditing(true)}
              className="px-6 py-2 font-bold text-black transition rounded-full shadow-lg bg-gradient-to-r from-yellow-400 to-yellow-500 hover:scale-110"
            >
              ✏ Edit Profile
            </button>
          </div>
        </div>
      </div>

      {/* مودال التعديل */}
      {isEditing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
          <div className="bg-white/10 border border-white/30 rounded-3xl p-8 w-[90%] max-w-lg text-white shadow-2xl">
            <h2 className="mb-4 text-2xl font-bold text-center text-yellow-300">
              Edit Profile
            </h2>

            <div className="space-y-4">
              <div className="text-gray-400 p-2 border border-white/20 rounded-lg bg-white/10">
                <span className="text-sm text-yellow-300">Username</span>
                <p className="font-semibold">{user.username}</p>
              </div>
              
              <input
                type="text"
                name="headline"
                placeholder="Headline (e.g. Senior Developer)"
                value={formData.headline || ""}
                onChange={handleChange}
                className="w-full p-2 text-white placeholder-gray-300 border rounded-lg bg-white/20 border-white/30"
              />
              <input
                type="text"
                name="city"
                placeholder="City"
                value={formData.city || ""}
                onChange={handleChange}
                className="w-full p-2 text-white placeholder-gray-300 border rounded-lg bg-white/20 border-white/30"
              />
              <input
                type="text"
                name="country"
                placeholder="Country"
                value={formData.country || ""}
                onChange={handleChange}
                className="w-full p-2 text-white placeholder-gray-300 border rounded-lg bg-white/20 border-white/30"
              />
              <textarea
                name="bio"
                placeholder="Bio"
                value={formData.bio || ""}
                onChange={handleChange}
                rows="3"
                className="w-full p-2 text-white placeholder-gray-300 border rounded-lg bg-white/20 border-white/30"
              />
            </div>

            <div className="flex justify-center gap-4 mt-6">
              <button
                onClick={handleSave}
                className="px-5 py-2 font-bold text-black transition rounded-full shadow-lg bg-gradient-to-r from-yellow-400 to-yellow-500 hover:scale-105"
              >
                Save
              </button>
              <button
                onClick={() => setIsEditing(false)}
                className="px-5 py-2 transition border rounded-full bg-white/20 border-white/40 hover:bg-white/30"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
