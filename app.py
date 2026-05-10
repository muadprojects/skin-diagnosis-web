
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
    print("تحذير: مكتبات الذكاء الاصطناعي غير متوفرة. سيعمل التطبيق في وضع العرض فقط.")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dermascan_secret_2024')

# مسارات البيانات
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CASES_FILE = os.path.join(DATA_DIR, 'cases.json')
UPLOAD_FOLDER = os.path.join('static', 'uploads')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# دالات البيانات
def load_json(file_path, default_value):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return default_value
    except:
        return default_value

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def reload_data():
    global USERS_STORAGE, CASES_STORAGE
    USERS_STORAGE = load_json(USERS_FILE, [])
    CASES_STORAGE = load_json(CASES_FILE, [])

# تحميل البيانات الأولية
USERS_STORAGE = load_json(USERS_FILE, [])
CASES_STORAGE = load_json(CASES_FILE, [])

# نماذج الذكاء الاصطناعي
model = None
binary_model = None

if AI_AVAILABLE:
    model_paths = ['models/model (1).keras', 'model (1).keras']
    binary_paths = ['models/skin_binary_model.keras', 'skin_binary_model.keras']
    
    for mp in model_paths:
        if os.path.exists(mp):
            try:
                model = load_model(mp, compile=False)
                break
            except: continue
            
    for bp in binary_paths:
        if os.path.exists(bp):
            try:
                binary_model = load_model(bp, compile=False)
                break
            except: continue

# الثوابت
BINARY_CLASS_NAMES = ['non_skin', 'skin']
DISEASES = {
    'Actinic keratoses': 'التقرن الشعاعي',
    'Basal cell carcinoma': 'سرطان الخلايا القاعدية', 
    'Benign keratosis-like lesions': 'آفات شبيهة بالتقرن الحميد',
    'Dermatofibroma': 'الورم الليفي الجلدي',
    'Melanocytic nevi': 'الشامات الميلانينية',
    'Melanoma': 'سرطان الجلد الميلانيني',
    'Vascular lesions': 'آفات الأوعية الدموية'
}
DISEASE_CODES = {
    'akiec': 'Actinic keratoses', 'bcc': 'Basal cell carcinoma',
    'bkl': 'Benign keratosis-like lesions', 'df': 'Dermatofibroma',
    'nv': 'Melanocytic nevi', 'mel': 'Melanoma', 'vasc': 'Vascular lesions'
}
CLASS_NAMES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

# --- المسارات (Routes) ---

@app.route('/')
def dashboard():
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session.get('user_email')
    user_name = session.get('user_name')
    user_type = session.get('user_type', 'patient')
    recent_cases = []
    
    if user_type in ['admin', 'doctor']:
        valid_cases = [c for c in CASES_STORAGE if c.get('created_at') and c.get('patient_name')]
        recent_cases = sorted(valid_cases, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    
    return render_template('dashboard.html', recent_cases=recent_cases, user_email=user_email, user_name=user_name, user_type=user_type)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # مستخدم إدارة افتراضي
        if email == 'admin@dermascan.com' and password == 'admin123':
            session['user_email'] = email
            session['user_name'] = 'الإدارة'
            session['user_type'] = 'admin'
            return redirect(url_for('dashboard'))
            
        for user in USERS_STORAGE:
            if user['email'] == email and user.get('password') == password:
                session['user_email'] = email
                session['user_name'] = user['name']
                session['user_type'] = user['type']
                return redirect(url_for('dashboard'))
                
        return render_template('login.html', error="بيانات الدخول غير صحيحة")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if any(u['email'] == email for u in USERS_STORAGE):
            return render_template('register.html', error="المستخدم مسجل مسبقًا")
        if password != confirm_password:
            return render_template('register.html', error="كلمات المرور غير متطابقة")
        
        if name and email and password:
            new_user = {'name': name, 'email': email, 'password': password, 'type': 'patient', 'original_name': name}
            USERS_STORAGE.append(new_user)
            save_json(USERS_FILE, USERS_STORAGE)
            return render_template('register.html', success="تم إنشاء الحساب بنجاح!")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    if 'user_email' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        if not AI_AVAILABLE or model is None:
            return render_template('diagnose.html', error="خدمة التشخيص غير متوفرة.")
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            try:
                img_pil = Image.open(filepath).convert('RGB').resize((224, 224))
                if binary_model:
                    b_img = np.expand_dims(np.array(img_pil)/255.0, axis=0)
                    if BINARY_CLASS_NAMES[np.argmax(binary_model.predict(b_img, verbose=0)[0])] == 'non_skin':
                        return render_template('diagnose.html', error="ليست صورة جلدية واضحة.")
                
                img_array = preprocess_input(np.array(img_pil))
                img_array = np.expand_dims(img_array, axis=0)
                pred = model.predict(img_array, verbose=0)[0]
                idx = np.argmax(pred)
                code = CLASS_NAMES[idx]
                
                result = {'code': code, 'name': DISEASE_CODES.get(code, code), 'arabic_name': DISEASES.get(DISEASE_CODES.get(code, code), code), 'probability': float(pred[idx]), 'percentage': float(pred[idx] * 100)}
                
                case_id = str(uuid.uuid4())
                CASES_STORAGE.append({'id': case_id, 'user_id': session['user_email'], 'user_name': session['user_name'], 'image_path': filename, 'disease': code, 'confidence': result['probability'], 'created_at': datetime.now().isoformat()})
                save_json(CASES_FILE, CASES_STORAGE)
                return render_template('diagnose.html', result=result, image_path=filename, case_id=case_id)
            except Exception as e: return render_template('diagnose.html', error=str(e))
    return render_template('diagnose.html')

@app.route('/cases')
def cases():
    if 'user_email' not in session: return redirect(url_for('login'))
    u_type = session.get('user_type')
    if u_type in ['admin', 'doctor']:
        u_cases = [c for c in CASES_STORAGE if c.get('patient_name')]
    else:
        u_cases = [c for c in CASES_STORAGE if c.get('user_id') == session.get('user_email')]
    return render_template('cases.html', cases=u_cases)

@app.route('/my_cases')
def my_cases():
    if session.get('user_type') != 'patient': return redirect(url_for('dashboard'))
    m_cases = [c for c in CASES_STORAGE if c.get('user_id') == session.get('user_email') or c.get('created_by') == session.get('user_email')]
    return render_template('my_cases.html', cases=m_cases)

@app.route('/add_case', methods=['GET', 'POST'])
def add_case():
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        p_name, p_age, p_phone = request.form.get('patient_name'), request.form.get('patient_age'), request.form.get('patient_phone')
        if p_name and p_age and p_phone:
            new_id = str(uuid.uuid4())
            new_case = {'id': new_id, 'case_number': len(CASES_STORAGE)+1, 'patient_name': p_name, 'patient_age': p_age, 'patient_phone': p_phone, 'notes': request.form.get('notes', ''), 'created_by': session['user_email'], 'created_at': datetime.now().isoformat(), 'diagnoses': []}
            CASES_STORAGE.append(new_case)
            save_json(CASES_FILE, CASES_STORAGE)
            return redirect(url_for('case_management', case_id=new_id))
    return render_template('add_case.html', next_case_number=len(CASES_STORAGE)+1)

@app.route('/case_management/<case_id>', methods=['GET', 'POST'])
def case_management(case_id):
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    case = next((c for c in CASES_STORAGE if str(c['id']) == str(case_id)), None)
    if not case: return render_template('case_management.html', error="الحالة غير موجودة")
    if request.method == 'POST':
        file = request.files.get('image')
        if file and file.filename:
            filename = secure_filename(f"case_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            if model:
                img_pil = Image.open(os.path.join(UPLOAD_FOLDER, filename)).convert('RGB').resize((224, 224))
                pred = model.predict(preprocess_input(np.expand_dims(np.array(img_pil), axis=0)), verbose=0)[0]
                idx = np.argmax(pred)
                code = CLASS_NAMES[idx]
                case.setdefault('diagnoses', []).append({'id': str(uuid.uuid4()), 'image_path': filename, 'disease': code, 'disease_english': DISEASE_CODES.get(code, code), 'disease_arabic': DISEASES.get(DISEASE_CODES.get(code, code), code), 'confidence': float(pred[idx]), 'created_at': datetime.now().isoformat(), 'notes': request.form.get('diagnosis_notes', ''), 'created_by': session['user_email']})
                save_json(CASES_FILE, CASES_STORAGE)
                return render_template('case_management.html', case=case, success="تم إضافة التشخيص")
    return render_template('case_management.html', case=case)

@app.route('/case/<case_id>')
def case_details(case_id):
    if 'user_email' not in session: return redirect(url_for('login'))
    case = next((c for c in CASES_STORAGE if str(c['id']) == str(case_id)), None)
    if case and (session['user_type'] in ['admin', 'doctor'] or case.get('user_id') == session['user_email']):
        return render_template('case_details.html', case=case)
    return render_template('case_details.html', error="غير مصرح أو غير موجود")

@app.route('/manage_doctors')
def manage_doctors():
    if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
    return render_template('manage_doctors.html', doctors=[u for u in USERS_STORAGE if u['type'] == 'doctor'], patients=[u for u in USERS_STORAGE if u['type'] == 'patient'], admins=[u for u in USERS_STORAGE if u['type'] == 'admin'], total_users=len(USERS_STORAGE))

@app.route('/manage_users')
def manage_users():
    if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
    return render_template('manage_users.html', patients=[u for u in USERS_STORAGE if u['type'] == 'patient'])

@app.route('/settings')
def settings(): return render_template('settings.html')

@app.route('/statistics')
def statistics():
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    f_cases = [c for c in CASES_STORAGE if c.get('patient_name')]
    counts = {}
    for c in f_cases:
        diag = c['diagnoses'][-1] if c.get('diagnoses') else None
        name = DISEASES.get(DISEASE_CODES.get(diag['disease'] if diag else c.get('disease')), 'unknown')
        counts[name] = counts.get(name, 0) + 1
    return render_template('statistics.html', total_cases=len(f_cases), diseases_count=counts, most_common=sorted(counts.items(), key=lambda x:x[1], reverse=True), avg_confidence=95)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
