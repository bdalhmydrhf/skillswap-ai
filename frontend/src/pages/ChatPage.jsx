// src/pages/ChatPage.jsx - النسخة النهائية V14.0 (PRODUCTION READY)
// ✅ التدفق الصحيح: محادثة ← تفاوض ← إنشاء عقد ← عرض تفاصيل العقد ← توقيع وتحقق

import React, { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Paperclip, Send, Image as ImageIcon, CheckCheck, Smile, MoreVertical,
  Phone, Video, Search, Users, Sparkles, X, Download, FileText, Music,
  Film, File as FileIcon, Reply, Copy, FileSignature, Shield, PlusCircle
} from "lucide-react";
import api from "../api/axiosConfig";
import { useNavigate } from "react-router-dom";

export default function ChatPage() {
  const navigate = useNavigate();
  const [rooms, setRooms] = useState([]);
  const [messages, setMessages] = useState([]);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [newMessage, setNewMessage] = useState("");
  const [loading, setLoading] = useState(true);
  const [ws, setWs] = useState(null);
  const [typingUser, setTypingUser] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [showEmojiPicker, setShowEmojiPicker] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [replyingTo, setReplyingTo] = useState(null);
  const [selectedMessage, setSelectedMessage] = useState(null);
  const [showContextMenu, setShowContextMenu] = useState(false);
  const [contextMenuPos, setContextMenuPos] = useState({ x: 0, y: 0 });
  const [toast, setToast] = useState(null);
  const [creatingContract, setCreatingContract] = useState(false);
  
  const typingTimeoutRef = useRef(null);
  const chatEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const fileInputRef = useRef(null);
  const imageInputRef = useRef(null);
  const currentUser = JSON.parse(localStorage.getItem("user") || "{}");

  const emojis = ['😀', '😂', '😍', '🥰', '😎', '🤔', '👍', '❤️', '🔥', '🎉', '✨', '💯', '🙏', '😢', '🥺', '😡', '👋', '🤝', '💪', '🎨', '📚', '💻', '🚀', '⭐', '💡', '🎯', '📱', '💎', '🌟', '💫'];

  const filteredRooms = rooms.filter(room => room.name?.toLowerCase().includes(searchQuery.toLowerCase()) || room.room_type?.toLowerCase().includes(searchQuery.toLowerCase()));

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  // Fetch rooms
  useEffect(() => {
    const fetchRooms = async () => {
      try {
        const response = await api.get("/chatrooms/");
        let roomsData = [];
        if (Array.isArray(response.data)) roomsData = response.data;
        else if (response.data && Array.isArray(response.data.results)) roomsData = response.data.results;
        setRooms(roomsData);
        if (roomsData.length > 0 && !selectedRoom) setSelectedRoom(roomsData[0]);
      } catch (error) { console.error("Error fetching rooms:", error); setRooms([]); } 
      finally { setLoading(false); }
    };
    fetchRooms();
  }, []);

  // Fetch messages
  useEffect(() => {
    if (!selectedRoom?.id) return;
    const fetchMessages = async () => {
      try {
        const response = await api.get(`/chatrooms/${selectedRoom.id}/messages/`);
        let messagesData = [];
        if (response.data?.messages && Array.isArray(response.data.messages)) messagesData = response.data.messages;
        else if (Array.isArray(response.data)) messagesData = response.data;
        
        const formatted = messagesData.map(msg => {
          let fileUrl = null;
          if (msg.file_url) fileUrl = msg.file_url;
          else if (msg.media?.file) fileUrl = msg.media.file;
          else if (msg.media?.ipfs_cdn_url) fileUrl = msg.media.ipfs_cdn_url;
          else if (msg.media?.file_url) fileUrl = msg.media.file_url;
          
          if (fileUrl && fileUrl.startsWith('/media/')) {
            fileUrl = `http://127.0.0.1:8001${fileUrl}`;
          }
          
          return {
            id: msg.id,
            sender: msg.sender?.username || "Unknown",
            sender_id: msg.sender?.id,
            text: msg.text || msg.decrypted_text || "",
            time: new Date(msg.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            fullTime: msg.created_at,
            read: msg.status === "read",
            delivered: msg.status === "delivered",
            isMe: msg.sender?.id === currentUser.id,
            message_type: msg.message_type,
            file_url: fileUrl,
            file_name: msg.file_name || (msg.media?.file?.name?.split('/').pop()),
            file_size: msg.file_size || msg.media?.size_mb,
            reply_to: msg.reply_to,
            media_id: msg.media?.id
          };
        });
        setMessages(formatted);
      } catch (error) { 
        console.error("Error fetching messages:", error); 
        setMessages([]); 
      }
    };
    fetchMessages();
  }, [selectedRoom]);

  // WebSocket connection
  useEffect(() => {
    if (!selectedRoom) return;
    const token = localStorage.getItem("access_token");
    if (!token) { console.error("No access token found"); return; }
    const roomIdentifier = selectedRoom.room_uuid || selectedRoom.id;
    if (!roomIdentifier) { console.error("No room identifier found"); return; }
    const wsUrl = `ws://127.0.0.1:8001/ws/v1/chat/${roomIdentifier}/?token=${token}`;
    const websocket = new WebSocket(wsUrl);
    websocket.onopen = () => console.log("WebSocket connected");
    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "message" || data.action === "message") {
        let fileUrl = data.file_url;
        if (fileUrl && fileUrl.startsWith('/media/')) {
          fileUrl = `http://127.0.0.1:8001${fileUrl}`;
        }
        const newMsg = { 
          id: data.message_id || Date.now(), 
          sender: data.sender || data.sender_name || "Unknown", 
          sender_id: data.sender_id, 
          text: data.message, 
          time: new Date(data.created_at || Date.now()).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), 
          fullTime: data.created_at, 
          read: false, 
          delivered: false, 
          isMe: data.sender_id === currentUser.id, 
          message_type: data.message_type || "text", 
          file_url: fileUrl, 
          file_name: data.file_name, 
          file_size: data.file_size,
          media_id: data.media_id
        };
        setMessages((prev) => [...prev, newMsg]);
      } else if (data.type === "typing" || data.action === "typing") { 
        if (data.is_typing && data.user_id !== currentUser.id) setTypingUser(data.user); 
        else setTypingUser(null); 
      } else if (data.type === "read_receipt") { 
        setMessages(prev => prev.map(msg => msg.id === data.message_id ? { ...msg, read: true } : msg)); 
      }
    };
    websocket.onerror = (error) => console.error("WebSocket error:", error);
    websocket.onclose = () => console.log("WebSocket disconnected");
    setWs(websocket);
    return () => { if (websocket.readyState === WebSocket.OPEN) websocket.close(); };
  }, [selectedRoom, currentUser.id]);

  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  const handleTyping = (value) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    if (typingTimeoutRef.current) clearTimeout(typingTimeoutRef.current);
    if (!isTyping && value) { ws.send(JSON.stringify({ action: "typing", is_typing: true })); setIsTyping(true); }
    if (value) { typingTimeoutRef.current = setTimeout(() => { ws.send(JSON.stringify({ action: "typing", is_typing: false })); setIsTyping(false); }, 1000); }
  };

  const sendMessage = async () => {
    if (newMessage.trim() === "") return;
    if (!selectedRoom || !selectedRoom.id) { console.error("No room selected"); return; }
    const messageText = newMessage; setNewMessage("");
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ action: "message", message: messageText, message_type: "text", reply_to: replyingTo?.id }));
      const msg = { id: Date.now(), sender: currentUser.username || "You", sender_id: currentUser.id, text: messageText, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), fullTime: new Date().toISOString(), read: false, delivered: false, isMe: true, message_type: "text" };
      setMessages((prev) => [...prev, msg]); setReplyingTo(null);
    } else {
      try {
        const payload = { room: selectedRoom.id, text: messageText, message_type: "text" };
        if (replyingTo?.id) payload.reply_to = replyingTo.id;
        await api.post("/messages/", payload);
        const msg = { id: Date.now(), sender: currentUser.username || "You", sender_id: currentUser.id, text: messageText, time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), fullTime: new Date().toISOString(), read: false, delivered: true, isMe: true, message_type: "text" };
        setMessages((prev) => [...prev, msg]); setReplyingTo(null);
      } catch (error) { console.error("Error sending message:", error); }
    }
  };

  // ✅ رفع الملفات
  const handleFileUpload = async (event, type = "file") => {
    const file = event.target.files[0];
    if (!file) return;
    if (!selectedRoom || !selectedRoom.id) return;
    
    setUploading(true);
    setUploadProgress(0);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('description', `File sent in chat room ${selectedRoom.id}`);
        
        const mediaResponse = await api.post('/media/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
            onUploadProgress: (p) => {
                if (p.total) setUploadProgress(Math.round((p.loaded * 100) / p.total));
            }
        });
        
        const media = mediaResponse.data;
        const fileType = file.type.startsWith('image/') ? 'image' : 
                        file.type.startsWith('video/') ? 'video' : 
                        file.type.startsWith('audio/') ? 'audio' : 'file';
        const messageText = `📎 ${file.name}`;
        
        const messagePayload = {
            room: selectedRoom.id,
            text: messageText,
            message_type: fileType,
            media_id: media.id
        };
        
        const messageResponse = await api.post("/messages/", messagePayload);
        const savedMessage = messageResponse.data;
        
        let fileUrl = media.file_url || media.file;
        if (fileUrl && fileUrl.startsWith('/media/')) {
            fileUrl = `http://127.0.0.1:8001${fileUrl}`;
        }
        
        const msg = { 
            id: savedMessage.id,
            sender: currentUser.username || "You", 
            sender_id: currentUser.id, 
            text: messageText, 
            time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), 
            fullTime: new Date().toISOString(), 
            read: false, 
            delivered: true, 
            isMe: true, 
            message_type: fileType, 
            file_url: fileUrl, 
            file_name: file.name, 
            file_size: (file.size / 1024 / 1024).toFixed(2),
            media_id: media.id
        };
        setMessages((prev) => [...prev, msg]);
        
    } catch (error) { 
        console.error("Error uploading file:", error); 
        alert("Failed to upload file. Please try again."); 
    } finally { 
        setUploading(false); 
        setUploadProgress(0); 
        if (fileInputRef.current) fileInputRef.current.value = ''; 
        if (imageInputRef.current) imageInputRef.current.value = ''; 
    }
  };

  const addEmoji = (emoji) => { setNewMessage(prev => prev + emoji); setShowEmojiPicker(false); };
  const copyMessage = (text) => { navigator.clipboard.writeText(text); setShowContextMenu(false); };
  const replyToMessage = (message) => { setReplyingTo(message); setShowContextMenu(false); };
  
  const getFileIcon = (messageType, fileName) => {
    if (messageType === 'image') return <ImageIcon size={20} className="text-pink-400" />;
    if (messageType === 'video') return <Video size={20} className="text-purple-400" />;
    if (messageType === 'audio') return <Music size={20} className="text-green-400" />;
    if (fileName?.endsWith('.pdf')) return <FileText size={20} className="text-red-400" />;
    if (fileName?.endsWith('.doc') || fileName?.endsWith('.docx')) return <FileText size={20} className="text-blue-400" />;
    if (fileName?.endsWith('.xls') || fileName?.endsWith('.xlsx')) return <FileText size={20} className="text-green-400" />;
    if (fileName?.endsWith('.zip') || fileName?.endsWith('.rar')) return <FileIcon size={20} className="text-yellow-400" />;
    return <FileIcon size={20} className="text-gray-400" />;
  };
  
  const getFileColor = (fileName) => {
    if (fileName?.endsWith('.pdf')) return 'from-red-500 to-rose-600';
    if (fileName?.endsWith('.doc') || fileName?.endsWith('.docx')) return 'from-blue-500 to-indigo-600';
    if (fileName?.endsWith('.xls') || fileName?.endsWith('.xlsx')) return 'from-green-500 to-emerald-600';
    if (fileName?.endsWith('.zip') || fileName?.endsWith('.rar')) return 'from-yellow-500 to-amber-600';
    return 'from-gray-500 to-gray-600';
  };
  
  const getFullUrl = (url) => {
    if (!url) return null;
    if (url.startsWith('http')) return url;
    if (url.startsWith('/media/')) return `http://127.0.0.1:8001${url}`;
    return `http://127.0.0.1:8001/media/${url}`;
  };

  const openFile = (url) => {
    if (!url) return;
    const fullUrl = getFullUrl(url);
    window.open(fullUrl, '_blank');
  };

  // ============================================================
  // ✅ الدوال الخاصة بالعقود (المنطق الصحيح)
  // ============================================================

  // ✅ 1. إنشاء عقد جديد بعد التفاوض (النسخة المحدثة مع التحقق من skill_id)
  const createContractFromChat = async () => {
    if (!selectedRoom) {
      showToast("No chat selected", "error");
      return;
    }

    if (selectedRoom?.contract) {
      showToast("A contract already exists for this chat", "error");
      return;
    }

    // ✅ الحصول على skill_id (بعد تعديل الـ Serializer)
    let skillId = null;

    // 1. حاول من room.skill_id (الحقل الجديد)
    if (selectedRoom.skill_id) {
        skillId = selectedRoom.skill_id;
        console.log("✅ Found skill_id from room:", skillId);
    }
    // 2. حاول من room.post_skill_id
    else if (selectedRoom.post_skill_id) {
        skillId = selectedRoom.post_skill_id;
        console.log("✅ Found post_skill_id from room:", skillId);
    }
    // 3. حاول من الـ post.skill.id (الطريقة القديمة)
    else if (selectedRoom.post?.skill?.id) {
        skillId = selectedRoom.post.skill.id;
        console.log("✅ Found skill from post object:", skillId);
    }
    // 4. إذا لم يوجد، اطلب من المستخدم
    else {
        const userSkillId = prompt(
            "⚠️ No skill associated with this chat.\n\n" +
            "Please enter a valid Skill ID (e.g., 1, 2, 3):\n\n" +
            "💡 You can find Skill IDs from the Skills page.",
            ""
        );
        if (!userSkillId || isNaN(parseInt(userSkillId))) {
            showToast("Skill ID is required to create a contract.", "error");
            return;
        }
        skillId = parseInt(userSkillId);
        
        // التحقق من وجود skill_id في قاعدة البيانات
        try {
            const skillCheck = await api.get(`/api/skills/${skillId}/`);
            if (!skillCheck.data) {
                showToast(`Skill with ID ${skillId} not found.`, "error");
                return;
            }
        } catch (error) {
            showToast(`Skill with ID ${skillId} does not exist.`, "error");
            return;
        }
    }

    const amount = prompt("💰 Enter contract amount (USD):", "100");
    if (!amount) return;
    if (isNaN(parseFloat(amount)) || parseFloat(amount) <= 0) {
      showToast("Please enter a valid amount", "error");
      return;
    }

    const deadlineDays = prompt("📅 Enter deadline (days from today):", "30");
    if (!deadlineDays) return;
    if (isNaN(parseInt(deadlineDays)) || parseInt(deadlineDays) <= 0) {
      showToast("Please enter a valid number of days", "error");
      return;
    }

    const deadlineDate = new Date();
    deadlineDate.setDate(deadlineDate.getDate() + parseInt(deadlineDays));
    const deadlineStr = deadlineDate.toISOString();

    const otherParticipant = selectedRoom.participants?.find(p => p.id !== currentUser.id);
    if (!otherParticipant) {
      showToast("Could not find the other participant", "error");
      return;
    }

    setCreatingContract(true);

    try {
      // ✅ بناء بيانات العقد مع skill_id دائماً
      const contractData = {
        title: `Contract between ${currentUser.username} and ${otherParticipant.username}`,
        description: "Contract created from chat discussion",
        client_id: currentUser.id,
        freelancer_id: otherParticipant.id,
        skill_id: skillId,  // ✅ الآن skill_id موجود دائماً
        total_amount: parseFloat(amount),
        currency: 'USD',
        status: 'pending',
        deadline: deadlineStr,
        chatroom_id: selectedRoom.id,
        terms: "Both parties agree to complete the work as described."
      };

      // ✅ إذا كان هناك post، حدّث العنوان
      if (selectedRoom.post?.title) {
        contractData.title = `Contract: ${selectedRoom.post.title}`;
      }

      console.log("📤 Sending contract data:", contractData);

      const response = await api.post("/contracts/", contractData);
      
      if (response.data) {
        showToast("✅ Contract created successfully!", "success");
        
        const roomResponse = await api.get(`/chatrooms/${selectedRoom.id}/`);
        setSelectedRoom(roomResponse.data);
        
        if (ws && ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ 
            action: "message", 
            message: `📄 Contract created for $${amount}. Please review and sign.`, 
            message_type: "system"
          }));
        }
      }
    } catch (error) {
      console.error("Error creating contract:", error);
      const errorMsg = error.response?.data?.error || error.response?.data?.message || error.message;
      showToast(`Failed to create contract: ${errorMsg}`, "error");
    } finally {
      setCreatingContract(false);
    }
  };

  // ✅✅✅ 2. التوجه إلى تفاصيل العقد (منطق صحيح - المستخدم يشوف العقد قبل التوقيع) ✅✅✅
  const goToContractDetails = () => {
    if (!selectedRoom?.contract?.id) {
      showToast("No contract associated with this chat", "error");
      return;
    }
    navigate(`/contracts/${selectedRoom.contract.id}/details`);
  };

  // ✅ عرض حالة العقد (Badge)
  const getContractStatusBadge = () => {
    if (!selectedRoom?.contract) return null;
    const contract = selectedRoom.contract;
    const config = { 
      pending: { color: "bg-yellow-500/20 text-yellow-400", text: "📝 Pending Signature" },
      partially_signed: { color: "bg-orange-500/20 text-orange-400", text: "⚠️ Partially Signed" },
      active: { color: "bg-green-500/20 text-green-400", text: "✅ Active" },
      completed: { color: "bg-emerald-500/20 text-emerald-400", text: "🎉 Completed" },
      signed: { color: "bg-emerald-500/20 text-emerald-400", text: "✅ Signed" }
    };
    const c = config[contract.status] || config.pending;
    return (
      <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium border ${c.color}`}>
        <Shield size={10} />
        <span>{c.text}</span>
      </div>
    );
  };

  const getRoomIcon = (room) => {
    if (room.contract) {
      if (room.contract.status === 'active') return "✅";
      if (room.contract.status === 'pending') return "📝";
      if (room.contract.status === 'completed') return "🎉";
      return "📄";
    }
    return "💬";
  };

  const renderMessageContent = (text, messageType, fileUrl, fileName, fileSize, media_id) => {
    const fullUrl = getFullUrl(fileUrl);
    
    if ((messageType === 'image' || fullUrl?.match(/\.(jpg|jpeg|png|gif|webp)$/i)) && fullUrl) {
      return (
        <div className="relative group mt-1">
          <img 
            src={fullUrl} 
            alt={fileName || "Image"} 
            className="max-w-[250px] max-h-[250px] rounded-2xl object-cover cursor-pointer hover:opacity-90 transition" 
            onClick={() => openFile(fullUrl)} 
            onError={(e) => { e.target.src = 'https://via.placeholder.com/250x250?text=Image+Not+Found'; }}
          />
          <div className="absolute bottom-2 right-2 bg-black/50 rounded-full px-2 py-0.5 text-xs text-white">
            {fileSize ? `${fileSize} MB` : ''}
          </div>
        </div>
      );
    }
    
    if (messageType === 'video' && fileUrl) {
      return (
        <div className="mt-1">
          <video src={fileUrl} controls className="max-w-[280px] max-h-[200px] rounded-2xl" />
          <p className="text-xs opacity-60 mt-1">{fileName}</p>
        </div>
      );
    }
    
    if ((messageType === 'audio' || fullUrl?.match(/\.(mp3|wav|ogg|flac)$/i)) && fullUrl) {
      return (
        <div className="flex items-center gap-3 bg-white/10 rounded-2xl p-3 min-w-[250px]">
          <div className="w-10 h-10 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 flex items-center justify-center">
            <Music size={20} className="text-white" />
          </div>
          <div className="flex-1">
            <p className="text-sm font-medium truncate max-w-[180px]">{fileName || 'Audio File'}</p>
            <audio src={fullUrl} controls className="w-full h-8" />
          </div>
        </div>
      );
    }
    
    if (fullUrl) {
      return (
        <div 
          className="flex items-center gap-3 bg-white/10 rounded-2xl p-3 min-w-[260px] hover:bg-white/15 transition-all duration-200 group cursor-pointer"
          onClick={() => openFile(fullUrl)}
        >
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getFileColor(fileName)} flex items-center justify-center shadow-lg group-hover:scale-105 transition`}>
            {getFileIcon(messageType, fileName)}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate text-white">{fileName || 'File'}</p>
            <div className="flex items-center gap-2 text-xs text-white/50">
              <span>{fileSize ? `${fileSize} MB` : '0 MB'}</span>
              <span>•</span>
              <span>{fileName?.split('.').pop()?.toUpperCase() || 'FILE'}</span>
            </div>
          </div>
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center group-hover:bg-white/20 transition">
            <Download size={16} className="text-white/70" />
          </div>
        </div>
      );
    }
    
    if (text) {
      let displayText = text;
      if (displayText.startsWith('📎')) displayText = displayText.substring(2);
      return <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{displayText}</p>;
    }
    
    return <p className="text-sm italic opacity-60">[Empty message]</p>;
  };

  if (loading) {
    return (
      <div className="relative flex h-screen items-center justify-center overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-pink-300 via-gray-200 to-pink-200"></div>
        <div className="relative z-10 text-center">
          <div className="relative w-24 h-24 mx-auto mb-6">
            <div className="absolute inset-0 border-4 border-pink-400/30 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-t-pink-500 border-r-gray-400 border-b-pink-600 border-l-transparent rounded-full animate-spin"></div>
            <div className="absolute inset-2 bg-gradient-to-br from-pink-500 to-purple-600 rounded-full animate-pulse"></div>
          </div>
          <p className="text-gray-800 text-xl font-semibold">Loading...</p>
          <p className="text-gray-600 text-sm mt-2">Connecting to secure channel...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative flex h-screen pt-16 overflow-hidden">
      <AnimatePresence>
        {toast && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            className={`fixed top-20 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg ${
              toast.type === 'success' ? 'bg-green-500 text-white' : 'bg-red-500 text-white'
            }`}
          >
            <span>{toast.message}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="absolute inset-0 z-0 bg-gradient-to-br from-pink-200 via-gray-200 to-pink-100">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-10 left-10 w-32 h-32 rounded-full bg-pink-300/60 animate-ping-slow"></div>
          <div className="absolute bottom-20 right-10 w-48 h-48 rounded-full bg-purple-300/50 animate-pulse-slow"></div>
          <div className="absolute top-1/2 left-1/3 w-64 h-64 rounded-full bg-pink-400/40 animate-zoom"></div>
          <div className="absolute bottom-1/3 right-1/4 w-40 h-40 rounded-full bg-gray-400/40 animate-bounce-slow"></div>
          <div className="absolute top-1/4 right-1/5 w-56 h-56 rounded-full bg-purple-300/50 animate-float-slow"></div>
          <div className="absolute bottom-10 left-1/3 w-36 h-36 rounded-full bg-pink-400/50 animate-ping-slow delay-1000"></div>
        </div>
        <div className="absolute inset-0 backdrop-blur-[1px] bg-white/30"></div>
      </div>

      {/* Sidebar */}
      <motion.div initial={{ x: -300, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ type: "spring", stiffness: 100, damping: 20 }} className="relative z-10 w-96 bg-white/30 backdrop-blur-xl border-r border-white/40 flex flex-col">
        <div className="p-6 border-b border-white/30">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold bg-gradient-to-r from-pink-500 to-purple-500 bg-clip-text text-transparent">Messages</h1>
            <Sparkles className="text-pink-500" size={24} />
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={18} />
            <input type="text" placeholder="Search conversations..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="w-full bg-white/50 border border-gray-300 rounded-xl py-2.5 pl-10 pr-4 text-gray-800 placeholder-gray-500 focus:outline-none focus:border-pink-400" />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {filteredRooms.length === 0 ? (
            <div className="text-center text-gray-500 py-8">
              <Users className="mx-auto mb-2 opacity-50" size={40} />
              <p>No conversations yet</p>
            </div>
          ) : (
            filteredRooms.map((room, idx) => (
              <motion.div key={room.id} initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: idx * 0.05 }} onClick={() => setSelectedRoom(room)} className={`group cursor-pointer p-4 rounded-2xl transition-all duration-300 ${selectedRoom?.id === room.id ? "bg-gradient-to-r from-pink-200/80 to-purple-200/80 border border-pink-400 shadow-lg" : "hover:bg-white/50 border border-transparent"}`}>
                <div className="flex items-center gap-3">
                  <div className="relative">
                    <div className="w-12 h-12 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center text-white font-bold text-lg">
                      {getRoomIcon(room)}
                    </div>
                    <div className="absolute -bottom-0.5 -right-0.5 w-3.5 h-3.5 bg-green-500 rounded-full border-2 border-white"></div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-800 truncate">{room.name || `Chat ${room.id}`}</h3>
                    <p className="text-sm text-gray-500 truncate">
                      {room.contract ? (room.contract.status === 'pending' ? "📝 Contract pending" : "📄 Contract exists") : "💬 Discussion"}
                    </p>
                  </div>
                  {room.unread_count > 0 && (
                    <div className="w-5 h-5 rounded-full bg-pink-500 flex items-center justify-center">
                      <span className="text-white text-xs font-bold">{room.unread_count}</span>
                    </div>
                  )}
                </div>
              </motion.div>
            ))
          )}
        </div>
      </motion.div>

      {/* Main Chat Area */}
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.2 }} className="relative z-10 flex-1 flex flex-col bg-white/40 backdrop-blur-md">
        {!selectedRoom ? (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <div className="w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br from-pink-200/80 to-purple-200/80 flex items-center justify-center">
                <MessageCircleIcon className="text-gray-500" size={50} />
              </div>
              <h2 className="text-2xl font-semibold text-gray-700">No chat selected</h2>
              <p className="text-gray-500 mt-2">Select a conversation to start messaging</p>
            </div>
          </div>
        ) : (
          <>
            {/* Header */}
            <div className="bg-gradient-to-r from-pink-100/80 via-gray-100/50 to-purple-100/80 backdrop-blur-sm border-b border-gray-200 p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-pink-400 to-purple-500 flex items-center justify-center">
                    <span className="text-white font-bold">{selectedRoom.name?.[0] || "C"}</span>
                  </div>
                  <div>
                    <h2 className="text-gray-800 font-semibold">{selectedRoom.name || `Chat ${selectedRoom.id}`}</h2>
                    <p className="text-xs text-gray-500">{selectedRoom.participants_count || 2} participants</p>
                  </div>
                  {getContractStatusBadge()}
                </div>
                <div className="flex items-center gap-2">
                  {/* ✅ زر إنشاء عقد جديد - يظهر فقط إذا لا يوجد عقد */}
                  {!selectedRoom?.contract && selectedRoom && (
                    <button 
                      onClick={createContractFromChat} 
                      disabled={creatingContract}
                      className="p-2 rounded-full bg-gradient-to-r from-emerald-500 to-teal-600 hover:scale-105 transition shadow-md flex items-center gap-1 px-3"
                    >
                      {creatingContract ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <PlusCircle size={16} className="text-white" />
                      )}
                      <span className="text-white text-xs font-medium hidden sm:inline">
                        {creatingContract ? "Creating..." : "Create Contract"}
                      </span>
                    </button>
                  )}
                  
                  {/* ✅✅✅ زر تفاصيل العقد (يظهر دائماً إذا يوجد عقد) ✅✅✅ */}
                  {selectedRoom?.contract && (
                    <button 
                      onClick={goToContractDetails} 
                      className="p-2 rounded-full bg-gradient-to-r from-indigo-500 to-blue-600 hover:scale-105 transition shadow-md flex items-center gap-1 px-3"
                    >
                      <FileText size={16} className="text-white" />
                      <span className="text-white text-xs font-medium hidden sm:inline">Contract Details</span>
                    </button>
                  )}
                  
                  <button className="p-2 rounded-full hover:bg-white/50"><Phone size={18} className="text-gray-600" /></button>
                  <button className="p-2 rounded-full hover:bg-white/50"><Video size={18} className="text-gray-600" /></button>
                  <button className="p-2 rounded-full hover:bg-white/50"><MoreVertical size={18} className="text-gray-600" /></button>
                </div>
              </div>
            </div>

            {replyingTo && (
              <div className="bg-white/60 backdrop-blur-sm border-l-4 border-pink-400 p-3 mx-4 mt-2 rounded-lg flex justify-between">
                <div className="flex gap-2">
                  <Reply size={14} className="text-pink-500" />
                  <div>
                    <p className="text-xs text-pink-600">Reply to {replyingTo.sender}</p>
                    <p className="text-sm text-gray-600 truncate max-w-md">{replyingTo.text}</p>
                  </div>
                </div>
                <button onClick={() => setReplyingTo(null)} className="text-gray-500"><X size={14} /></button>
              </div>
            )}

            {uploading && (
              <div className="bg-white/60 backdrop-blur-sm p-3 mx-4 mt-2 rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 border-2 border-pink-500 border-t-transparent rounded-full animate-spin"></div>
                  <div className="flex-1">
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="h-full bg-gradient-to-r from-pink-400 to-purple-500 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }}></div>
                    </div>
                    <p className="text-xs text-gray-600 mt-1">Uploading... {uploadProgress}%</p>
                  </div>
                </div>
              </div>
            )}

            {/* Messages */}
            <div ref={messagesContainerRef} className="flex-1 overflow-y-auto p-6 space-y-3">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full">
                  <div className="text-center">
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-white/50 flex items-center justify-center">
                      <MessageCircleIcon className="text-gray-400" size={35} />
                    </div>
                    <p className="text-gray-500">No messages yet</p>
                    <p className="text-gray-400 text-sm">Send a message to start the conversation</p>
                  </div>
                </div>
              ) : (
                messages.map((msg, idx) => (
                  <motion.div key={msg.id} initial={{ opacity: 0, y: 20, scale: 0.95 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ delay: idx * 0.02 }} className={`flex ${msg.isMe ? "justify-end" : "justify-start"} group`} onContextMenu={(e) => { e.preventDefault(); setSelectedMessage(msg); setContextMenuPos({ x: e.clientX, y: e.clientY }); setShowContextMenu(true); }}>
                    <div className={`max-w-[80%] rounded-2xl px-4 py-2.5 shadow-md ${msg.isMe ? "bg-gradient-to-r from-pink-500 to-purple-600 text-white" : "bg-white text-gray-800 border border-gray-200"}`}>
                      {!msg.isMe && <p className="text-xs text-pink-500 mb-1 font-medium">{msg.sender}</p>}
                      {msg.reply_to && <div className="text-xs opacity-70 mb-2 p-1 bg-gray-100 rounded"><span>↩️ Reply to</span></div>}
                      {msg.message_type === 'system' ? (
                        <p className="text-xs italic opacity-70">{msg.text}</p>
                      ) : (
                        renderMessageContent(msg.text, msg.message_type, msg.file_url, msg.file_name, msg.file_size, msg.media_id)
                      )}
                      <div className="flex items-center justify-end gap-1 mt-1.5">
                        <span className="text-[10px] opacity-70">{msg.time}</span>
                        {msg.isMe && <CheckCheck size={12} className={msg.read ? "text-green-300" : "opacity-70"} />}
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
              {typingUser && (
                <div className="flex justify-start">
                  <div className="bg-white/60 backdrop-blur-sm rounded-2xl px-4 py-2.5">
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce delay-100"></div>
                      <div className="w-2 h-2 bg-pink-400 rounded-full animate-bounce delay-200"></div>
                      <span className="text-xs text-gray-500 ml-2">{typingUser} is typing...</span>
                    </div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {showContextMenu && selectedMessage && (
              <div className="fixed z-50 bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden" style={{ top: contextMenuPos.y, left: contextMenuPos.x }}>
                <button onClick={() => copyMessage(selectedMessage.text)} className="flex items-center gap-3 w-full px-4 py-2 hover:bg-gray-100 text-gray-700 text-sm">
                  <Copy size={14} /> Copy
                </button>
                <button onClick={() => replyToMessage(selectedMessage)} className="flex items-center gap-3 w-full px-4 py-2 hover:bg-gray-100 text-gray-700 text-sm">
                  <Reply size={14} /> Reply
                </button>
                <hr className="border-gray-100" />
                <button onClick={() => setShowContextMenu(false)} className="flex items-center gap-3 w-full px-4 py-2 hover:bg-gray-100 text-gray-500 text-sm">
                  <X size={14} /> Cancel
                </button>
              </div>
            )}
            {showContextMenu && <div className="fixed inset-0 z-40" onClick={() => setShowContextMenu(false)}></div>}

            {/* Input */}
            <div className="border-t border-gray-200 p-4 bg-white/60 backdrop-blur-md">
              <div className="flex items-center gap-3">
                <input type="file" ref={fileInputRef} className="hidden" onChange={(e) => handleFileUpload(e, "file")} />
                <button onClick={() => fileInputRef.current?.click()} className="p-2 rounded-full hover:bg-pink-100" disabled={uploading}>
                  <Paperclip size={20} className="text-gray-600" />
                </button>
                <input type="file" ref={imageInputRef} accept="image/*" className="hidden" onChange={(e) => handleFileUpload(e, "image")} />
                <button onClick={() => imageInputRef.current?.click()} className="p-2 rounded-full hover:bg-pink-100" disabled={uploading}>
                  <ImageIcon size={20} className="text-gray-600" />
                </button>
                <div className="relative">
                  <button onClick={() => setShowEmojiPicker(!showEmojiPicker)} className="p-2 rounded-full hover:bg-pink-100">
                    <Smile size={20} className="text-gray-600" />
                  </button>
                  {showEmojiPicker && (
                    <div className="absolute bottom-12 left-0 bg-white rounded-xl shadow-lg p-3 border border-gray-200 z-20 w-64">
                      <div className="grid grid-cols-8 gap-1">
                        {emojis.map(emoji => (
                          <button key={emoji} onClick={() => addEmoji(emoji)} className="text-xl hover:bg-pink-100 rounded-lg p-2 transition">
                            {emoji}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <input 
                  type="text" 
                  value={newMessage} 
                  onChange={(e) => setNewMessage(e.target.value)} 
                  onKeyDown={(e) => e.key === "Enter" && sendMessage()} 
                  onFocus={() => handleTyping(true)} 
                  onBlur={() => handleTyping(false)} 
                  placeholder="Type a message..." 
                  className="flex-1 bg-white border border-gray-300 rounded-full py-3 px-5 text-gray-700 placeholder-gray-400 focus:outline-none focus:border-pink-400 focus:ring-1 focus:ring-pink-400" 
                  disabled={uploading} 
                />
                <motion.button 
                  whileHover={{ scale: 1.05 }} 
                  whileTap={{ scale: 0.95 }} 
                  onClick={sendMessage} 
                  disabled={!newMessage.trim() || uploading} 
                  className={`p-3 rounded-full transition-all ${newMessage.trim() && !uploading ? "bg-gradient-to-r from-pink-500 to-purple-600 shadow-md" : "bg-gray-200 cursor-not-allowed"}`}
                >
                  <Send size={18} className="text-white" />
                </motion.button>
              </div>
            </div>
          </>
        )}
      </motion.div>

      <style>{`
        @keyframes ping-slow { 0% { transform: scale(0.95); opacity: 0.5; } 50% { transform: scale(1.5); opacity: 0.2; } 100% { transform: scale(0.95); opacity: 0.5; } }
        @keyframes pulse-slow { 0%, 100% { transform: scale(1); opacity: 0.3; } 50% { transform: scale(1.3); opacity: 0.1; } }
        @keyframes zoom { 0%, 100% { transform: scale(0.8); opacity: 0.3; } 50% { transform: scale(1.4); opacity: 0.1; } }
        @keyframes bounce-slow { 0%, 100% { transform: translateY(0) scale(1); opacity: 0.2; } 50% { transform: translateY(-30px) scale(1.1); opacity: 0.1; } }
        @keyframes float-slow { 0%, 100% { transform: translate(0,0); opacity: 0.2; } 50% { transform: translate(30px,-20px); opacity: 0.4; } }
        @keyframes float-particle { 0%, 100% { transform: translateY(0px) translateX(0px); opacity: 0; } 25% { opacity: 0.6; } 50% { transform: translateY(-60px) translateX(30px); opacity: 0.3; } 75% { opacity: 0.6; } }
        .animate-ping-slow { animation: ping-slow 5s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
        .animate-pulse-slow { animation: pulse-slow 4s ease-in-out infinite; }
        .animate-zoom { animation: zoom 6s ease-in-out infinite; }
        .animate-bounce-slow { animation: bounce-slow 7s ease-in-out infinite; }
        .animate-float-slow { animation: float-slow 8s ease-in-out infinite; }
        .animate-float-particle { animation: float-particle 8s linear infinite; }
        .delay-1000 { animation-delay: 1s; }
      `}</style>
    </div>
  );
}

// Icons
const MessageCircleIcon = ({ size, className }) => (
  <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
    <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8z"/>
  </svg>
);
