import streamlit as st
import pandas as pd
from PIL import Image
import json
import io
from concurrent.futures import ThreadPoolExecutor
from google import genai
from google.genai import types

st.set_page_config(page_title="نظام الإشعارات المالية Live", page_icon="🧾", layout="wide")

st.sidebar.title("⚙️ الإعدادات")
api_key = st.sidebar.text_input("ادخل مفتاح Gemini API:", type="password")

if not api_key:
    if "GEMINI_API_KEY" in st.secrets:
        api_key = st.secrets["GEMINI_API_KEY"]

st.title("🧾 النظام المباشر لمعالجة الإشعارات المالية")
st.write("رفع الإشعارات واستخراج البيانات فورياً ومشاركتها أونلاين.")

if not api_key:
    st.warning("⚠️ يرجى إدخال مفتاح API في الشريط الجانبي للبدء.")
    st.stop()

client = genai.Client(api_key=api_key)

def process_receipt(uploaded_file):
    try:
        image = Image.open(uploaded_file)
        
        prompt = """
        اقرأ صورة الإشعار المالي واستخرج البيانات التالية بدقة باللغة العربية بصيغة JSON فقط:
        {
            "last_4_digits": "آخر 4 أرقام فقط من رقم العملية أو المرجع",
            "recipient": "اسم المرسل إليه / الحساب المحول له",
            "date": "تاريخ العملية فقط بصيغة YYYY-MM-DD",
            "comment": "التعليق أو الملاحظة (إذا لم يوجد اكتب: لا يوجد)"
        }
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        data = json.loads(response.text)
        return data
        
    except Exception as e:
        return {
            "last_4_digits": "غير واضح",
            "recipient": "غير واضح",
            "date": "غير واضح",
            "comment": "خطأ في القراءة"
        }

uploaded_files = st.file_uploader(
    "ارفع صور الإشعارات هنا (حتى 100+ صورة دفعة واحدة):", 
    type=["jpg", "jpeg", "png"], 
    accept_multiple_files=True
)

if uploaded_files:
    st.info(f"تم استقبال {len(uploaded_files)} إشعار.")
    
    if st.button("بدء المعالجة واستخراج البيانات 🚀"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        results = []
        total_files = len(uploaded_files)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(process_receipt, f) for f in uploaded_files]
            
            for idx, future in enumerate(futures):
                result = future.result()
                results.append(result)
                
                progress = (idx + 1) / total_files
                progress_bar.progress(progress)
                status_text.text(f"تمت معالجة {idx + 1} من أصل {total_files} إشعار...")

        st.success("🎉 اكتمل استخراج البيانات بنجاح!")
        
        df = pd.DataFrame(results)
        cols = ["last_4_digits", "recipient", "date", "comment"]
        df = df[cols]
        
        df.columns = [
            "آخر 4 أرقام من العملية", 
            "المرسل إليه", 
            "التاريخ", 
            "التعليق / الملاحظة"
        ]
        
        st.subheader("📊 جدول البيانات المعالجة حياً")
        st.dataframe(df, use_container_width=True)
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='بيانات الإشعارات')
        
        st.download_button(
            label="📥 تحميل جدول البيانات (Excel)",
            data=buffer.getvalue(),
            file_name="بيانات_الإشعارات_المالية.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
