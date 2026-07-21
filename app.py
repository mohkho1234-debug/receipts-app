import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from PIL import Image

st.set_page_config(page_title="نظام الإشعارات المالية", layout="wide")

api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.sidebar.title("الإعدادات")
    api_key = st.sidebar.text_input("ادخل مفتاح Gemini API:", type="password")

st.title("🧾 النظام المباشر لمعالجة الإشعارات المالية")
st.write("رفع الإشعارات واستخراج البيانات فوراً ومشاركتها أونلاين")

if not api_key:
    st.warning("⚠️ في الشريط الجانبي ابدأ بإدخال مفتاح API")
else:
    try:
        genai.configure(api_key=api_key)
        
        # جلب الموديل المتاح تلقائياً لحسابك لمنع خطأ 404
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        active_model_name = "gemini-1.5-flash"
        # اختيار أفضل موديل متوفر في حسابك
        for preferred in ['models/gemini-2.0-flash', 'models/gemini-1.5-flash', 'models/gemini-1.5-flash-latest', 'models/gemini-pro-vision']:
            if preferred in available_models:
                active_model_name = preferred
                break
        elif available_models:
            active_model_name = available_models[0]

        model = genai.GenerativeModel(active_model_name)
    except Exception as err:
        st.error(f"خطأ في تهيئة النظام: {err}")

    uploaded_files = st.file_uploader("ارفع صور الإشعارات هنا (حتى 100+ صورة دفعة واحدة)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"تم استقبال {len(uploaded_files)} إشعار.")
        
        if st.button("🚀 بدء المعالجة واستخراج البيانات"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            prompt = """
            اقرأ صورة إشعار التحويل المالي البنكي واستخرج منه التفاصيل التالية.
            أرجع الإجابة بصيغة JSON خامة فقط وبدون أي أوسمة ماركداون:
            {
                "التاريخ": "التاريخ والوقت",
                "المرسل إليه": "اسم المستلم",
                "آخر 4 أرقام": "آخر أرقام رقم الحساب",
                "المبلغ": "المبلغ بالأرقام",
                "التعليق / الملاحظة": "ناجحة"
            }
            """

            for i, file in enumerate(uploaded_files):
                status_text.text(f"...تتم معالجة {i+1} من أصل {len(uploaded_files)} إشعار")
                try:
                    image = Image.open(file)
                    response = model.generate_content([prompt, image])
                    text = response.text.strip()
                    
                    start = text.find('{')
                    end = text.rfind('}') + 1
                    
                    if start != -1 and end != 0:
                        json_str = text[start:end]
                        data = json.loads(json_str)
                    else:
                        data = {
                            "التاريخ": "غير محدد",
                            "المرسل إليه": "تعذر القراءة",
                            "آخر 4 أرقام": "N/A",
                            "المبلغ": "0",
                            "التعليق / الملاحظة": "لم يتم التعرف على الصيغة"
                        }
                    results.append(data)
                except Exception as e:
                    results.append({
                        "التاريخ": "خطأ",
                        "المرسل إليه": "فشل الاستدعاء",
                        "آخر 4 أرقام": "N/A",
                        "المبلغ": "0",
                        "التعليق / الملاحظة": str(e)
                    })
                
                progress_bar.progress((i + 1) / len(uploaded_files))
                
            status_text.success("🎉 اكتملت معالجة الصور بنجاح!")
            
            if results:
                d…
