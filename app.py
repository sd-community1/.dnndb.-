import os
import io
from flask import Flask, render_template, request, send_file
import google.generativeai as genai
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import arabic_reshaper
from bidi.algorithm import get_display

app = Flask(__name__)

# --- إعداد مفتاح الـ API ---
# يفضل وضع المفتاح في متغيرات البيئة، لكن هنا للتوضيح:
# احصل على مفتاحك من: https://aistudio.google.com/
os.environ["GOOGLE_API_KEY"] = "YOUR_API_KEY_HERE"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

def process_text_with_ai(user_text):
    """دالة لإرسال النص للذكاء الاصطناعي لإعادة صياغته وإضافة الشروحات"""
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""
    قم بأداء المهام التالية على النص المقدم:
    1. أعد صياغة النص ليكون أكثر احترافية وتنظيماً.
    2. استخرج الكلمات الصعبة أو المفاهيم المهمة واشرحها في قسم منفصل بعنوان "نصوص توضيحية".
    
    النص هو:
    {user_text}
    
    اجعل الإجابة باللغة العربية وواضحة.
    """
    
    response = model.generate_content(prompt)
    return response.text

def create_pdf(text_content):
    """دالة لإنشاء ملف PDF يدعم العربية"""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # تسجيل الخط العربي (تأكد من وجود ملف font.ttf بجانب هذا الملف)
    try:
        pdfmetrics.registerFont(TTFont('ArabicFont', 'font.ttf'))
        c.setFont('ArabicFont', 14)
    except:
        print("Error: Font file not found. Using default font (Arabic won't work).")
    
    y_position = height - 50
    margin = 50
    
    # تقسيم النص إلى أسطر
    lines = text_content.split('\n')
    
    for line in lines:
        if y_position < 50:  # صفحة جديدة إذا انتهت الصفحة الحالية
            c.showPage()
            c.setFont('ArabicFont', 14)
            y_position = height - 50
            
        # معالجة النص العربي (التشكيل والاتجاه)
        reshaped_text = arabic_reshaper.reshape(line)
        bidi_text = get_display(reshaped_text)
        
        # رسم النص (محاذاة لليمين لأنه عربي)
        c.drawRightString(width - margin, y_position, bidi_text)
        y_position -= 20  # مسافة بين الأسطر

    c.save()
    buffer.seek(0)
    return buffer

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        raw_text = request.form['user_text']
        
        if not raw_text:
            return "الرجاء إدخال نص", 400
            
        # 1. المعالجة بالذكاء الاصطناعي
        ai_result = process_text_with_ai(raw_text)
        
        # 2. تحويل النتيجة إلى PDF
        pdf_file = create_pdf(ai_result)
        
        return send_file(pdf_file, as_attachment=True, download_name="ai_summary.pdf", mimetype='application/pdf')

    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
