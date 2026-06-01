// src/pages/SkillPostDetail.jsx
import React, { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { 
  ArrowLeft, User, DollarSign, MapPin, Calendar, 
  MessageCircle, Loader2, AlertCircle, Briefcase, Clock
} from "lucide-react";
import api from "../api/axiosConfig";

export default function SkillPostDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [contacting, setContacting] = useState(false);

  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const response = await api.get(`/skillposts/${id}/`);
        setPost(response.data);
      } catch (err) {
        console.error("Error fetching post:", err);
        setError("Post not found or an error occurred");
      } finally {
        setLoading(false);
      }
    };
    fetchPost();
  }, [id]);

  const handleContact = async () => {
    if (!currentUser || !currentUser.id) {
      navigate("/login");
      return;
    }

    if (currentUser.id === post?.creator?.id) {
      alert("You cannot contact yourself");
      return;
    }

    setContacting(true);
    try {
      const response = await api.post("/chatrooms/", {
        post_id: post.id,
        participant_id: post.creator.id,
        room_type: "post_discussion"
      });

      const chatroom = response.data;
      const roomId = chatroom.room_uuid || chatroom.id;
      navigate(`/chat/${roomId}`);
    } catch (err) {
      console.error("Error creating chat:", err);
      if (err.response?.status === 409) {
        // Room already exists
        try {
          const roomsRes = await api.get(`/chatrooms/?post_id=${post.id}`);
          if (roomsRes.data?.results?.length > 0) {
            const existingRoom = roomsRes.data.results[0];
            navigate(`/chat/${existingRoom.room_uuid || existingRoom.id}`);
          }
        } catch (e) {
          alert("Error creating chat room");
        }
      } else {
        alert("Error creating chat room");
      }
    } finally {
      setContacting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-12 h-12 text-indigo-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading post details...</p>
        </div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 flex items-center justify-center">
        <div className="text-center bg-white/80 backdrop-blur-sm p-8 rounded-2xl shadow-lg">
          <AlertCircle size={48} className="text-red-500 mx-auto mb-4" />
          <p className="text-gray-700 mb-4">{error || "Post not found"}</p>
          <button
            onClick={() => navigate("/skills")}
            className="px-4 py-2 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition"
          >
            Back to Posts
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-100 via-white to-blue-100 py-24 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Back Button */}
        <button
          onClick={() => navigate("/skills")}
          className="flex items-center gap-2 text-indigo-600 hover:text-indigo-800 mb-6 transition"
        >
          <ArrowLeft size={20} />
          <span>Back to Posts</span>
        </button>

        {/* Post Card */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/90 backdrop-blur-sm rounded-2xl shadow-xl overflow-hidden border border-indigo-100"
        >
          {/* Header */}
          <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-6 text-white">
            <h1 className="text-2xl md:text-3xl font-bold mb-2">{post.title}</h1>
            <div className="flex flex-wrap items-center gap-4 text-white/80 text-sm">
              <div className="flex items-center gap-1">
                <User size={14} />
                <span>{post.creator?.username || "User"}</span>
                {post.creator?.id === currentUser?.id && (
                  <span className="ml-2 text-xs bg-white/20 px-2 py-0.5 rounded-full">You</span>
                )}
              </div>
              <div className="flex items-center gap-1">
                <Calendar size={14} />
                <span>{new Date(post.created_at).toLocaleDateString('en-US')}</span>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6">
            {/* Price */}
            <div className="flex items-center gap-2 mb-4 text-2xl font-bold text-green-600">
              <DollarSign size={28} />
              <span>{post.price} {post.currency || 'USD'}</span>
            </div>

            {/* Location */}
            {post.location && (
              <div className="flex items-center gap-2 mb-4 text-gray-600">
                <MapPin size={18} />
                <span>{post.location}</span>
              </div>
            )}

            {/* Description */}
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-700 mb-2">Description</h3>
              <p className="text-gray-600 leading-relaxed">{post.description}</p>
            </div>

            {/* Requirements */}
            {post.requirements && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-700 mb-2">Requirements</h3>
                <p className="text-gray-600 leading-relaxed">{post.requirements}</p>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-4 mt-8 pt-6 border-t border-indigo-100">
              {currentUser?.id !== post.creator?.id && (
                <button
                  onClick={handleContact}
                  disabled={contacting}
                  className="flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 transition disabled:opacity-50"
                >
                  {contacting ? (
                    <Loader2 size={20} className="animate-spin" />
                  ) : (
                    <MessageCircle size={20} />
                  )}
                  {contacting ? "Creating..." : "Contact Publisher"}
                </button>
              )}
              <button
                onClick={() => navigate("/skills")}
                className="px-6 py-3 border border-indigo-300 text-indigo-600 rounded-xl hover:bg-indigo-50 transition"
              >
                Browse More Posts
              </button>
            </div>

            {/* Additional Stats */}
            <div className="mt-6 pt-4 flex flex-wrap gap-4 text-xs text-gray-400">
              <div className="flex items-center gap-1">
                <Briefcase size={12} />
                <span>Post ID: {post.id}</span>
              </div>
              {post.views_count !== undefined && (
                <div className="flex items-center gap-1">
                  <Clock size={12} />
                  <span>{post.views_count} views</span>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
