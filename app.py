
import os
import json
import numpy as np
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

# محاولة تحميل مكتبات الذكاء الاصطناعي
try:
    from tensorflow.keras.models import load_model
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
    from PIL import Image
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dermascan_secret_2024')

# مسارات البيانات
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CASES_FILE = os.path.join(DATA_DIR, 'cases.json')
UPLOAD_FOLDER = os.path.join('static', 'uploads')

# إنشاء المجلدات والتأكد من وجود ملفات JSON
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

if not os.path.exists(CASES_FILE):
    with open(CASES_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

# متغيرات النماذج (ستحمل لاحقاً لتوفير الذاكرة)
model = None
binary_model = None

def get_models():
    global model, binary_model
    if AI_AVAILABLE and model is None:
        try:
            # استخدام مسارات مرنة والبحث عن الملفات الصحيحة
            m_path = 'models/model (1).keras' if os.path.exists('models/model (1).keras') else 'model (1).keras'
            b_path = 'models/skin_binary_model.keras' if os.path.exists('models/skin_binary_model.keras') else 'skin_binary_model.keras'
            
            if os.path.exists(m_path):
                model = load_model(m_path, compile=False)
            if os.path.exists(b_path):
                binary_model = load_model(b_path, compile=False)
        except Exception as e:
            print(f"Error loading models: {e}")
    return model, binary_model

# دالات البيانات
def load_json(file_path, default_value):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default_value
    except: return default_value

def save_json(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

# تحميل البيانات الأولية
USERS_STORAGE = load_json(USERS_FILE, [])
CASES_STORAGE = load_json(CASES_FILE, [])

# الثوابت
BINARY_CLASS_NAMES = ['non_skin', 'skin']
DISEASES = {
    'Actinic keratoses': 'التقرن الشعاعي', 'Basal cell carcinoma': 'سرطان الخلايا القاعدية', 
    'Benign keratosis-like lesions': 'آفات شبيهة بالتقرن الحميد', 'Dermatofibroma': 'الورم الليفي الجلدي',
    'Melanocytic nevi': 'الشامات الميلانينية', 'Melanoma': 'سرطان الجلد الميلانيني', 'Vascular lesions': 'آفات الأوعية الدموية'
}
DISEASE_CODES = {
    'akiec': 'Actinic keratoses', 'bcc': 'Basal cell carcinoma', 'bkl': 'Benign keratosis-like lesions',
    'df': 'Dermatofibroma', 'nv': 'Melanocytic nevi', 'mel': 'Melanoma', 'vasc': 'Vascular lesions'
}
CLASS_NAMES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

@app.route('/')
def dashboard():
    if 'user_email' not in session: return redirect(url_for('login'))
    user_type = session.get('user_type', 'patient')
    recent = sorted([c for c in CASES_STORAGE if c.get('created_at')], key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    return render_template('dashboard.html', recent_cases=recent, user_name=session.get('user_name'), user_type=user_type)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, pwd = request.form.get('email'), request.form.get('password')
        if email == 'admin@dermascan.com' and pwd == 'admin123':
            session.update({'user_email': email, 'user_name': 'الإدارة', 'user_type': 'admin'})
            return redirect(url_for('dashboard'))
        for u in USERS_STORAGE:
            if u['email'] == email and u.get('password') == pwd:
                session.update({'user_email': email, 'user_name': u['name'], 'user_type': u['type']})
                return redirect(url_for('dashboard'))
        return render_template('login.html', error="بيانات غير صحيحة")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, email, pwd = request.form.get('name'), request.form.get('email'), request.form.get('password')
        if any(u['email'] == email for u in USERS_STORAGE): return render_template('register.html', error="مسجل مسبقاً")
        USERS_STORAGE.append({'name': name, 'email': email, 'password': pwd, 'type': 'patient'})
        save_json(USERS_FILE, USERS_STORAGE)
        return render_template('register.html', success="تم التسجيل!")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    if 'user_email' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        m, bm = get_models()
        if not m: return render_template('diagnose.html', error="الموديل غير جاهز، انتظر ثواني.")
        file = request.files.get('image')
        if file:
            fname = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            path = os.path.join(UPLOAD_FOLDER, fname)
            file.save(path)
            try:
                img = Image.open(path).convert('RGB').resize((224, 224))
                if bm and BINARY_CLASS_NAMES[np.argmax(bm.predict(np.expand_dims(np.array(img)/255.0, 0), verbose=0)[0])] == 'non_skin':
                    return render_template('diagnose.html', error="ليست صورة جلدية.")
                pred = m.predict(preprocess_input(np.expand_dims(np.array(img), 0)), verbose=0)[0]
                idx = np.argmax(pred)
                res = {'code': CLASS_NAMES[idx], 'name': DISEASE_CODES.get(CLASS_NAMES[idx]), 'arabic_name': DISEASES.get(DISEASE_CODES.get(CLASS_NAMES[idx])), 'percentage': float(pred[idx]*100)}
                CASES_STORAGE.append({'id': str(uuid.uuid4()), 'user_id': session['user_email'], 'user_name': session['user_name'], 'image_path': fname, 'disease': res['code'], 'confidence': float(pred[idx]), 'created_at': datetime.now().isoformat()})
                save_json(CASES_FILE, CASES_STORAGE)
                return render_template('diagnose.html', result=res, image_path=fname)
            except Exception as e: return render_template('diagnose.html', error=str(e))
    return render_template('diagnose.html')

# باقي المسارات (بسيطة للويب)
@app.route('/cases')
def cases():
    u_cases = [c for c in CASES_STORAGE if (session['user_type'] in ['admin', 'doctor']) or c.get('user_id') == session['user_email']]
    return render_template('cases.html', cases=u_cases)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
