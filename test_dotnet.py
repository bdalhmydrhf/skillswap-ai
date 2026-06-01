import sys
import clr
import os

# أضف مسار DLLs
sys.path.append(r"E:\skillswap-ai\DLLs")

try:
    # تحميل المكتبة كـ .NET assembly
    clr.AddReference("BS_SDK_V2")
    print("✅ تم تحميل المكتبة كـ .NET assembly")
    
    # استيراد namespace
    from BS_SDK_V2 import *
    
    print("✅ تم استيراد الدوال")
    
    # جربي إنشاء كائن من الكلاس الرئيسي
    # (الأسماء قد تختلف، جربي)
    # sdk = BiostarSDK()
    
except Exception as e:
    print(f"❌ فشل التحميل: {e}")