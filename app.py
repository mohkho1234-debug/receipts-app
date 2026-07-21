import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
from PIL import Image

st.set_page_config(page_title="نظام الإشعارات المالية", layout="wide")

# جلب مفتاح API من Secrets أو من الشريط الجانبي
api_key = st.secrets.get("GEMINI_API_KEY", "")

if not api_key:
    st.sidebar.title("الإعدادات")
    api_key = st.sidebar.text_input("ادخل مفتاح Gemini API:", type="password")

st.title("🧾 النظام المباشر لمعالجة الإشعارات المالية")
st.write("رفع الإشعارات واستخراج البيانات فوراً ومشاركتها أونلاين")

if not api_key:
    st.warning("⚠️ في الشريط الجانبي ابدأ بإدخال مفتاح API")
else:
    genai.configure(api_key=api_key)
    
    uploaded_files = st.file_uploader("ارفع صور الإشعارات هنا (حتى 100+ صورة دفعة واحدة)", type=["jpg", "jpeg", "png"], accept_multiple_files=True)
    
    if uploaded_files:
        st.info(f"تم استقبال {len(uploaded_files)} إشعار.")
        
        if st.button("🚀 بدء المعالجة واستخراج البيانات"):
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # استخدام موديل رؤية حديث وسريع
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = """
            أنت خبير في قراءة وإدخال بيانات الإشعارات المالية والإيصالات البنكية (مثل تطبيق بنكك / Bankak).
            استخرج البيانات التالية بدقة من الصورة، وأرجع النتيجة بصيغة JSON فقط وبدون أي كود أو كلام إضافي:

            {
                "التاريخ": "تاريخ ووقت العملية",
                "المرسل إليه": "اسم المستلم أو المرسل إليه",
                "آخر 4 أرقام": "رقم الحساب أو آخر 4 أرقام منه",
                "المبلغ": "المبلغ بالأرقام فقط",
                "التعليق / الملاحظة": "مكتملة / ناجحة أو أي ملاحظة"
            }
            """

            for i, file in enumerate(uploaded_files):
                status_text.text(f"...تتم معالجة {i+1} من أصل {len(uploaded_files)} إشعار")
                try:
                    image = Image.open(file)
                    response = model.generate_content([prompt, image])
                    text = response.text.strip()
                    
                    # تنظيف النص واستخراج الـ JSON
                    if "json" in text:
                        text = text.split("json")[1].split("")[0].strip()
                    elif "" in text:
                        text = text.split("")[1].split("")[0].strip()
                        
                    data = json.loads(text)
                    results.append(data)
                except Exception as e:
                    results.append({
                        "التاريخ": "غير محدد",
                        "المرسل إليه": "تعذر الاستخراج",
                        "آخر 4 أرقام": "N/A",
                        "المبلغ": "0",
                        "التعليق / الملاحظة": "يرجى التأكد من وضوح الصورة"
                    })
                
                progress_bar.progress((i + 1) / len(uploaded_files))
                
            status_text.success("🎉 اكتمل استخراج البيانات بنجاح!")
            
            if results:
                df = pd.DataFrame(results)
                st.subheader("📊 جدول البيانات المعالجة حياً")
                st.dataframe(df, use_container_width=True)
                
                # زر تحميل Excel
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تحميل جدول البيانات (CSV / Excel)",
                    data=csv,
                    file_name="receipts_data.csv",
                    mime="text/csv",
                )
