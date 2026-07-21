import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import time
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
    uploaded_files = st.file_uploader("ارفع صور الإشعارات هنا (حتى 100+ صورة دفعة واحدة)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"تم استقبال {len(uploaded_files)} إشعار.")
        
        if st.button("🚀 بدء المعالجة واستخراج البيانات"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                genai.configure(api_key=api_key)
                
                # جلب قائمة الموديلات المتاحة وتصفية الاسم من بادئة models/
                all_models = [
                    m.name.replace('models/', '') 
                    for m in genai.list_models() 
                    if 'generateContent' in m.supported_generation_methods
                ]
                
                # قائمة النماذج المفضلة حسب الأحدث والأكثر استقراراً
                preferred_order = [
                    'gemini-1.5-flash',
                    'gemini-1.5-flash-latest',
                    'gemini-1.5-pro',
                    'gemini-2.0-flash-exp',
                    'gemini-1.0-pro-vision'
                ]
                
                selected_model = None
                for candidate in preferred_order:
                    if candidate in all_models:
                        selected_model = candidate
                        break
                
                if not selected_model and all_models:
                    selected_model = all_models[0]
                    
                if not selected_model:
                    selected_model = 'gemini-1.5-flash'

                model = genai.GenerativeModel(selected_model)
                
            except Exception as e:
                st.error(f"خطأ في تهيئة المفتاح أو جلب الموديلات: {e}")
                st.stop()
            
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
                status_text.text(f"جاري معالجة الإشعار رقم {i+1} من أصل {len(uploaded_files)}")
                
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
                
                time.sleep(1.5)
                progress_bar.progress((i + 1) / len(uploaded_files))
                
            status_text.success("🎉 اكتملت معالجة الصور بنجاح!")
            
            if results:
                df = pd.DataFrame(results)
                st.subheader("📊 جدول البيانات المعالجة حياً")
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تحميل جدول البيانات (CSV / Excel)",
                    data=csv,
                    file_name="receipts_data.csv",
                    mime="text/csv",
                )
