import ctypes
import os

# إضافة مسار DLLs
os.add_dll_directory(r"E:\skillswap-ai\DLLs")

# تحميل المكتبة
dll_path = r"E:\skillswap-ai\DLLs\BS_SDK_V2.dll"
dll = ctypes.CDLL(dll_path)
print("✅ DLL loaded successfully")

# البحث عن دوال محتملة
possible_functions = [
    'BS_Initialize', 'BS_Init', 'Initialize', 'Init',
    'BS_Start', 'Start', 'Open', 'BS_Open',
    'BS_Scan', 'Scan', 'Capture', 'BS_Capture',
    'BS_Verify', 'Verify', 'Match', 'BS_Match',
    'BS_Close', 'Close', 'BS_Finalize', 'Finalize'
]

print("\n🔍 البحث عن الدوال:")
for func_name in possible_functions:
    try:
        func = getattr(dll, func_name)
        print(f"   ✅ موجود: {func_name}")
    except AttributeError:
        pass

print("\n✅ تم الانتهاء من البحث")