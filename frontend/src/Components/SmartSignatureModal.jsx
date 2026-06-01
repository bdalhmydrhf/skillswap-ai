// @ts-nocheck
import React, { useRef, useState, useEffect } from "react";

const SmartSignatureModal = ({ isOpen, onClose, contractId }) => {
  const canvasRef = useRef(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [signatureData, setSignatureData] = useState(null);

  // 🔁 إعادة ضبط التوقيع عند إغلاق المودال
  useEffect(() => {
    if (!isOpen && canvasRef.current) {
      clearSignature();
    }
  }, [isOpen]);

  const getCanvasContext = () => {
    const canvas = canvasRef.current;
    return canvas ? canvas.getContext("2d") : null;
  };

  // ✏ بدء الرسم
  const startDrawing = (e) => {
    const ctx = getCanvasContext();
    if (!ctx) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const offsetX = e.nativeEvent?.offsetX ?? e.touches?.[0].clientX - rect.left;
    const offsetY = e.nativeEvent?.offsetY ?? e.touches?.[0].clientY - rect.top;
    ctx.beginPath();
    ctx.moveTo(offsetX, offsetY);
    setIsDrawing(true);
  };

  // 🔄 الرسم أثناء الحركة
  const draw = (e) => {
    if (!isDrawing) return;
    const ctx = getCanvasContext();
    if (!ctx) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const offsetX = e.nativeEvent?.offsetX ?? e.touches?.[0].clientX - rect.left;
    const offsetY = e.nativeEvent?.offsetY ?? e.touches?.[0].clientY - rect.top;
    ctx.lineWidth = 2;
    ctx.lineCap = "round";
    ctx.strokeStyle = "#000";
    ctx.lineTo(offsetX, offsetY);
    ctx.stroke();
  };

  // 🛑 إنهاء الرسم
  const stopDrawing = () => {
    if (!isDrawing) return;
    const canvas = canvasRef.current;
    const dataUrl = canvas.toDataURL("image/png");
    setSignatureData(dataUrl);
    setIsDrawing(false);
  };

  // 🧹 مسح التوقيع
  const clearSignature = () => {
    const ctx = getCanvasContext();
    if (ctx) {
      ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
      setSignatureData(null);
    }
  };

  // 📤 إرسال التوقيع
  const handleSubmit = async () => {
    if (!signatureData) {
      alert("الرجاء رسم التوقيع أولاً!");
      return;
    }

    try {
      const response = await fetch(`/api/signature/smart/${contractId}/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${localStorage.getItem("token")}`,
        },
        body: JSON.stringify({ signature_data: signatureData }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || "فشل في إرسال التوقيع.");
      }

      alert("تم حفظ التوقيع بنجاح ✅");
      onClose();
    } catch (error) {
      console.error("خطأ أثناء الإرسال:", error);
      alert("حدث خطأ أثناء إرسال التوقيع.");
    }
  };

  // 🚪 في حال المودال مغلق
  if (!isOpen) return null;

  // 🧩 واجهة المودال
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
      <div className="bg-white rounded-xl p-6 w-full max-w-md shadow-lg">
        <h2 className="text-xl font-bold mb-4 text-center">✍ التوقيع الذكي</h2>

        <canvas
          ref={canvasRef}
          width={400}
          height={200}
          className="border-2 border-gray-300 rounded-xl cursor-crosshair w-full touch-none"
          onMouseDown={startDrawing}
          onMouseMove={draw}
          onMouseUp={stopDrawing}
          onMouseLeave={stopDrawing}
          onTouchStart={startDrawing}
          onTouchMove={draw}
          onTouchEnd={stopDrawing}
        />

        <div className="flex justify-between mt-4">
          <button
            onClick={clearSignature}
            className="bg-gray-300 text-black py-2 px-4 rounded-lg hover:bg-gray-400 transition"
          >
            مسح
          </button>
          <button
            onClick={handleSubmit}
            className="bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 transition"
          >
            حفظ التوقيع
          </button>
          <button
            onClick={onClose}
            className="bg-red-500 text-white py-2 px-4 rounded-lg hover:bg-red-600 transition"
          >
            إغلاق
          </button>
        </div>

        {signatureData && (
          <p className="mt-2 text-green-600 text-sm text-center">
            ✅ تم إنشاء التوقيع، جاهز للإرسال
          </p>
        )}
      </div>
    </div>
  );
};

export default SmartSignatureModal;
