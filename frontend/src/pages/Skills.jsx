import React, { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Search, Code, Briefcase, Layers, MessageCircle, User, 
  DollarSign, MapPin, AlertCircle, Loader2, ChevronLeft, 
  ChevronRight, Shield, CheckCircle, Phone, Video, FileSignature 
} from "lucide-react";
import api from "../api/axiosConfig";
import { useNavigate } from "react-router-dom";

// ✅ Skeleton Loading Component
const SkillsSkeleton = () => (
  <div className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8">
    {[...Array(8)].map((_, i) => (
      <div key={i} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 animate-pulse">
        <div className="w-10 h-10 bg-gray-200 rounded-full mx-auto mb-4"></div>
        <div className="h-6 bg-gray-200 rounded w-3/4 mx-auto mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto mb-3"></div>
        <div className="h-16 bg-gray-200 rounded mb-4"></div>
        <div className="h-10 bg-gray-200 rounded w-full"></div>
      </div>
    ))}
  </div>
);

// ✅ Post Skeleton
const PostSkeleton = () => (
  <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-8">
    {[...Array(6)].map((_, i) => (
      <div key={i} className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 animate-pulse">
        <div className="h-6 bg-gray-200 rounded w-3/4 mb-2"></div>
        <div className="h-16 bg-gray-200 rounded mb-3"></div>
        <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
        <div className="h-4 bg-gray-200 rounded w-1/3 mb-4"></div>
        <div className="flex gap-3">
          <div className="h-10 bg-gray-200 rounded flex-1"></div>
          <div className="h-10 bg-gray-200 rounded flex-1"></div>
        </div>
      </div>
    ))}
  </div>
);

// ✅ Pagination Component
const Pagination = ({ currentPage, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;
  
  return (
    <div className="flex justify-center items-center gap-2 mt-12">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="p-2 rounded-lg bg-white/80 border border-indigo-200 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-50 transition"
      >
        <ChevronLeft size={20} />
      </button>
      
      <span className="px-4 py-2 text-sm text-gray-600">
        Page {currentPage} of {totalPages}
      </span>
      
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="p-2 rounded-lg bg-white/80 border border-indigo-200 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-indigo-50 transition"
      >
        <ChevronRight size={20} />
      </button>
    </div>
  );
};

// ✅ Toast Notification Component
const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -50 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -50 }}
      className={`fixed top-20 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg ${
        type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
      }`}
    >
      {type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
      <span>{message}</span>
    </motion.div>
  );
};

export default function Skills() {
  const [skills, setSkills] = useState([]);
  const [posts, setPosts] = useState([]);
  const [query, setQuery] = useState("");
  const [activeTab, setActiveTab] = useState("skills");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [toast, setToast] = useState(null);
  const [contactingId, setContactingId] = useState(null);
  
  const navigate = useNavigate();
  
  // ✅ الحصول على المستخدم الحالي
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");
  const itemsPerPage = 9;

  // ✅ عرض إشعار
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
  };

  // ✅ جلب البيانات
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      try {
        // جلب المهارات
        const skillsRes = await api.get("/skills/");
        let skillsData = [];
        if (Array.isArray(skillsRes.data)) {
          skillsData = skillsRes.data;
        } else if (skillsRes.data && Array.isArray(skillsRes.data.results)) {
          skillsData = skillsRes.data.results;
        }
        setSkills(skillsData);
        
        // جلب المنشورات مع Pagination
        const postsRes = await api.get(`/skillposts/?page=${currentPage}&page_size=${itemsPerPage}`);
        let postsData = [];
        if (Array.isArray(postsRes.data)) {
          postsData = postsRes.data;
        } else if (postsRes.data && Array.isArray(postsRes.data.results)) {
          postsData = postsRes.data.results;
          setTotalPages(Math.ceil(postsRes.data.count / itemsPerPage) || 1);
        }
        setPosts(postsData);
      } catch (error) {
        console.error("Error fetching data:", error);
        setError("Failed to load data. Please refresh the page.");
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [currentPage]);

  // ✅✅✅ الدالة المصححة: فقط إنشاء غرفة محادثة (بدون عقد) ✅✅✅
  const handleContact = async (post) => {
    // ✅ التحقق من تسجيل الدخول
    if (!currentUser || !currentUser.id) {
      showToast("Please login first", "error");
      navigate("/login");
      return;
    }
    
    // ✅ منع التواصل مع النفس
    if (currentUser.id === post.creator?.id) {
      showToast("You cannot chat with yourself", "error");
      return;
    }
    
    // ✅ التحقق من وجود creator
    if (!post.creator || !post.creator.id) {
      setError("Cannot start chat: Post creator not found");
      showToast("Post creator not found", "error");
      return;
    }

    setContactingId(post.id);
    showToast("Creating chat room...", "success");

    try {
      console.log("Creating chat room for post:", post.id, "with user:", post.creator.id);
      
      // ✅ 1. إنشاء غرفة محادثة فقط (بدون عقد)
      const chatResponse = await api.post("/chatrooms/", {
        post_id: post.id,
        participant_id: post.creator.id,
        room_type: "post_discussion"
      });
      
      const chatroom = chatResponse.data;
      console.log("Chat room created:", chatroom);
      
      // ✅ تم حذف جزء إنشاء العقد التلقائي بالكامل
      // ✅ العقد سيتم إنشاؤه لاحقاً من داخل صفحة المحادثة بعد التفاوض
      
      showToast("Chat room created! Discuss and create contract later.", "success");
      
      // ✅ الانتقال إلى صفحة المحادثة
      const roomId = chatroom.room_uuid || chatroom.id;
      navigate(`/chat/${roomId}`);
      
    } catch (error) {
      console.error("Error creating chat:", error);
      setContactingId(null);
      
      // عرض رسالة خطأ مفصلة
      if (error.response) {
        if (error.response.status === 400) {
          const errorDetail = error.response.data?.detail || error.response.data?.error || 'Invalid data';
          showToast(`Bad request: ${errorDetail}`, "error");
        } else if (error.response.status === 401) {
          showToast("Please login again", "error");
          navigate("/login");
        } else if (error.response.status === 409) {
          showToast("Chat room already exists", "error");
          try {
            const existingRooms = await api.get(`/chatrooms/?post_id=${post.id}`);
            if (existingRooms.data?.results?.length > 0) {
              const existingRoom = existingRooms.data.results[0];
              navigate(`/chat/${existingRoom.room_uuid || existingRoom.id}`);
            }
          } catch (e) {
            console.error(e);
          }
        } else {
          showToast(`Server error: ${error.response.status}`, "error");
        }
      } else if (error.request) {
        showToast("No response from server. Please check if the server is running.", "error");
      } else {
        showToast(`Error: ${error.message}`, "error");
      }
    } finally {
      setContactingId(null);
    }
  };

  // ✅ تصفية البيانات
  const filteredSkills = skills.filter((skill) =>
    skill.name?.toLowerCase().includes(query.toLowerCase())
  );
  
  const filteredPosts = posts.filter((post) =>
    post.title?.toLowerCase().includes(query.toLowerCase())
  );

  // ✅ Skeleton Loading
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 py-20 px-8">
        <div className="text-center mb-10">
          <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center animate-pulse">
            <Loader2 className="w-10 h-10 text-white animate-spin" />
          </div>
          <p className="text-indigo-600">Loading skills marketplace...</p>
        </div>
        {activeTab === "skills" ? <SkillsSkeleton /> : <PostSkeleton />}
      </div>
    );
  }

  // ✅ Error State
  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 flex items-center justify-center">
        <div className="text-center text-red-600 bg-white/80 backdrop-blur-sm p-8 rounded-2xl shadow-lg">
          <AlertCircle size={48} className="mx-auto mb-4" />
          <p className="mb-4">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 py-20 px-8">
      {/* Toast Notifications */}
      <AnimatePresence>
        {toast && (
          <Toast
            message={toast.message}
            type={toast.type}
            onClose={() => setToast(null)}
          />
        )}
      </AnimatePresence>

      {/* 🔹 العنوان الرئيسي */}
      <motion.h1
        className="text-5xl font-extrabold text-center mb-4 text-indigo-700 drop-shadow-md"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
      >
        💡 Explore Skills Marketplace
      </motion.h1>
      
      <p className="text-center text-gray-600 mb-8">
        Connect with talented people and start exchanging skills
      </p>

      {/* 🔹 مربع البحث */}
      <div className="flex justify-center mb-12">
        <div className="relative w-full max-w-lg">
          <Search className="absolute left-3 top-3 text-gray-500" size={20} />
          <input
            type="text"
            placeholder="Search for a skill or post..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 rounded-2xl border border-indigo-300 shadow-sm focus:ring-2 focus:ring-indigo-400 outline-none bg-white/80 backdrop-blur-sm"
          />
        </div>
      </div>

      {/* 🔹 أزرار التبويب */}
      <div className="flex justify-center gap-4 mb-8">
        <button
          onClick={() => setActiveTab("skills")}
          className={`px-6 py-2 rounded-full font-semibold transition ${
            activeTab === "skills"
              ? "bg-indigo-600 text-white shadow-lg"
              : "bg-white text-indigo-600 border border-indigo-300 hover:bg-indigo-50"
          }`}
        >
          📚 Skills ({filteredSkills.length})
        </button>
        <button
          onClick={() => setActiveTab("posts")}
          className={`px-6 py-2 rounded-full font-semibold transition ${
            activeTab === "posts"
              ? "bg-indigo-600 text-white shadow-lg"
              : "bg-white text-indigo-600 border border-indigo-300 hover:bg-indigo-50"
          }`}
        >
          📝 Skill Posts ({filteredPosts.length})
        </button>
      </div>

      {/* 🔹 عرض المهارات */}
      {activeTab === "skills" && (
        <motion.div
          className="grid sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-8"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: {},
            visible: { transition: { staggerChildren: 0.1 } },
          }}
        >
          {filteredSkills.length === 0 ? (
            <p className="text-center text-gray-500 col-span-full py-20">
              No skills found. Try another search 🔍
            </p>
          ) : (
            filteredSkills.map((skill, index) => (
              <motion.div
                key={skill.id || index}
                className="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl p-6 hover:shadow-xl transition duration-300 border border-indigo-100 relative overflow-hidden group cursor-pointer"
                whileHover={{ scale: 1.04, rotate: 0.5 }}
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 },
                }}
                onClick={() => setActiveTab("posts")}
              >
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-blue-500"></div>

                <div className="flex justify-center mb-4">
                  {index % 3 === 0 ? (
                    <Code className="text-indigo-500 w-10 h-10 group-hover:scale-110 transition" />
                  ) : index % 3 === 1 ? (
                    <Briefcase className="text-indigo-500 w-10 h-10 group-hover:scale-110 transition" />
                  ) : (
                    <Layers className="text-indigo-500 w-10 h-10 group-hover:scale-110 transition" />
                  )}
                </div>

                <h3 className="text-xl font-bold text-indigo-700 text-center mb-2">
                  {skill.name}
                </h3>
                <p className="text-sm text-gray-600 text-center mb-3">
                  {skill.category || "General"}
                </p>
                <p className="text-gray-700 text-center text-sm line-clamp-3">
                  {skill.description || "No description available."}
                </p>

                <div className="flex justify-center mt-4">
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      setActiveTab("posts");
                    }}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm px-4 py-2 rounded-xl transition"
                  >
                    View Posts
                  </button>
                </div>
              </motion.div>
            ))
          )}
        </motion.div>
      )}

      {/* 🔹 عرض المنشورات */}
      {activeTab === "posts" && (
        <>
          <motion.div
            className="grid sm:grid-cols-2 md:grid-cols-3 gap-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
          >
            {filteredPosts.length === 0 ? (
              <p className="text-center text-gray-500 col-span-full py-20">
                No posts available. Create your first skill post! 🚀
              </p>
            ) : (
              filteredPosts.map((post) => (
                <motion.div
                  key={post.id}
                  className="bg-white/80 backdrop-blur-sm shadow-lg rounded-2xl p-6 hover:shadow-xl transition duration-300 border border-indigo-100 relative overflow-hidden"
                  whileHover={{ scale: 1.02 }}
                >
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500"></div>
                  
                  <h3 className="text-xl font-bold text-indigo-700 mb-2 line-clamp-1">{post.title}</h3>
                  <p className="text-gray-600 text-sm mb-3 line-clamp-2">{post.description}</p>
                  
                  <div className="space-y-2 mb-4">
                    <div className="flex items-center gap-2 text-gray-600 text-sm">
                      <User size={16} className="text-indigo-500" />
                      <span>{post.creator?.username || 'Unknown'}</span>
                      {post.creator?.id === currentUser?.id && (
                        <span className="text-xs bg-green-100 text-green-600 px-2 py-0.5 rounded-full">You</span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-green-600 text-sm">
                      <DollarSign size={16} className="text-green-500" />
                      <span>{post.price} {post.currency || 'USD'}</span>
                    </div>
                    {post.location && (
                      <div className="flex items-center gap-2 text-gray-500 text-sm">
                        <MapPin size={14} />
                        <span>{post.location}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex gap-3 mt-4">
                    <button 
                      onClick={() => handleContact(post)}
                      disabled={contactingId === post.id}
                      className="flex-1 flex items-center justify-center gap-2 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {contactingId === post.id ? (
                        <Loader2 size={16} className="animate-spin" />
                      ) : (
                        <MessageCircle size={16} />
                      )}
                      {contactingId === post.id ? "Creating..." : "Contact"}
                    </button>
                    <button 
                      onClick={() => navigate(`/skillpost/${post.id}`)}
                      className="flex-1 py-2 border border-indigo-300 text-indigo-600 rounded-xl hover:bg-indigo-50 transition text-sm"
                    >
                      Details
                    </button>
                  </div>
                </motion.div>
              ))
            )}
          </motion.div>
          
          {/* Pagination */}
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={(page) => {
              setCurrentPage(page);
              window.scrollTo({ top: 0, behavior: 'smooth' });
            }}
          />
        </>
      )}
    </div>
  );
}
