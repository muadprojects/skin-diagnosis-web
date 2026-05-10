
import os
import json
import numpy as np
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename

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

DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CASES_FILE = os.path.join(DATA_DIR, 'cases.json')
UPLOAD_FOLDER = os.path.join('static', 'uploads')

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

for f_path in [USERS_FILE, CASES_FILE]:
    if not os.path.exists(f_path):
        with open(f_path, 'w', encoding='utf-8') as f: json.dump([], f)

model = None
binary_model = None

def get_models():
    global model, binary_model
    if AI_AVAILABLE and model is None:
        try:
            m_path = 'models/model (1).keras' if os.path.exists('models/model (1).keras') else 'model (1).keras'
            b_path = 'models/skin_binary_model.keras' if os.path.exists('models/skin_binary_model.keras') else 'skin_binary_model.keras'
            if os.path.exists(m_path): model = load_model(m_path, compile=False)
            if os.path.exists(b_path): binary_model = load_model(b_path, compile=False)
        except: pass
    return model, binary_model

def load_json(file_path, default_value):
    try:
        with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
    except: return default_value

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

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
    cases_data = load_json(CASES_FILE, [])
    user_type = session.get('user_type', 'patient')
    user_email = session.get('user_email')
    
    if user_type in ['admin', 'doctor']:
        recent = sorted([c for c in cases_data if c.get('created_at')], key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    else:
        recent = sorted([c for c in cases_data if c.get('user_id') == user_email], key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
    return render_template('dashboard.html', recent_cases=recent, user_name=session.get('user_name'), user_type=user_type)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, pwd = request.form.get('email'), request.form.get('password')
        if email == 'admin@dermascan.com' and pwd == 'admin123':
            session.update({'user_email': email, 'user_name': 'الإدارة', 'user_type': 'admin'})
            return redirect(url_for('dashboard'))
        users = load_json(USERS_FILE, [])
        for u in users:
            if u['email'] == email and u.get('password') == pwd:
                session.update({'user_email': email, 'user_name': u['name'], 'user_type': u.get('type', 'patient')})
                return redirect(url_for('dashboard'))
        return render_template('login.html', error="بيانات غير صحيحة")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, email, pwd = request.form.get('name'), request.form.get('email'), request.form.get('password')
        users = load_json(USERS_FILE, [])
        if any(u['email'] == email for u in users): return render_template('register.html', error="مسجل مسبقاً")
        users.append({'name': name, 'email': email, 'password': pwd, 'type': 'patient'})
        save_json(USERS_FILE, users)
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
        if not m: return render_template('diagnose.html', error="الموديل غير جاهز")
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
                code = CLASS_NAMES[idx]
                res = {'code': code, 'name': DISEASE_CODES.get(code), 'arabic_name': DISEASES.get(DISEASE_CODES.get(code)), 'percentage': float(pred[idx]*100)}
                cases_data = load_json(CASES_FILE, [])
                cases_data.append({'id': str(uuid.uuid4()), 'user_id': session['user_email'], 'user_name': session['user_name'], 'image_path': fname, 'disease': code, 'confidence': float(pred[idx]), 'created_at': datetime.now().isoformat()})
                save_json(CASES_FILE, cases_data)
                return render_template('diagnose.html', result=res, image_path=fname)
            except Exception as e: return render_template('diagnose.html', error=str(e))
    return render_template('diagnose.html')

@app.route('/cases')
def cases():
    if 'user_email' not in session: return redirect(url_for('login'))
    cases_data = load_json(CASES_FILE, [])
    u_type = session.get('user_type')
    if u_type in ['admin', 'doctor']:
        u_cases = [c for c in cases_data if c.get('patient_name')]
    else:
        u_cases = [c for c in cases_data if c.get('user_id') == session.get('user_email')]
    return render_template('cases.html', cases=u_cases)

@app.route('/add_case', methods=['GET', 'POST'])
def add_case():
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    cases_data = load_json(CASES_FILE, [])
    if request.method == 'POST':
        p_name = request.form.get('patient_name')
        new_id = str(uuid.uuid4())
        cases_data.append({'id': new_id, 'patient_name': p_name, 'patient_age': request.form.get('patient_age'), 'patient_phone': request.form.get('patient_phone'), 'created_by': session['user_email'], 'created_at': datetime.now().isoformat(), 'diagnoses': []})
        save_json(CASES_FILE, cases_data)
        return redirect(url_for('cases'))
    return render_template('add_case.html', next_case_number=len(cases_data)+1)

@app.route('/manage_doctors')
def manage_doctors():
    if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
    users = load_json(USERS_FILE, [])
    return render_template('manage_doctors.html', doctors=[u for u in users if u.get('type') == 'doctor'], patients=[u for u in users if u.get('type') == 'patient'], admins=[u for u in users if u.get('type') == 'admin'], total_users=len(users))

@app.route('/manage_users')
def manage_users():
    if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
    users = load_json(USERS_FILE, [])
    return render_template('manage_users.html', patients=[u for u in users if u.get('type') == 'patient'])

@app.route('/statistics')
def statistics():
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    cases_data = load_json(CASES_FILE, [])
    f_cases = [c for c in cases_data if c.get('patient_name')]
    counts = {}
    for c in f_cases:
        diag = c['diagnoses'][-1] if c.get('diagnoses') else None
        code = diag['disease'] if diag else c.get('disease')
        name = DISEASES.get(DISEASE_CODES.get(code), 'غير معروف')
        counts[name] = counts.get(name, 0) + 1
    
    return render_template('statistics.html', 
                         total_cases=len(f_cases), 
                         diseases_count=counts, 
                         most_common=sorted(counts.items(), key=lambda x:x[1], reverse=True), 
                         avg_confidence=95)

@app.route('/settings')
def settings():
    if 'user_email' not in session: return redirect(url_for('login'))
    user_email = session.get('user_email')
    users = load_json(USERS_FILE, [])
    current_user = next((u for u in users if u['email'] == user_email), {'name': session.get('user_name'), 'email': user_email})
    return render_template('settings.html', user=current_user)

@app.route('/my_cases')
def my_cases():
    if 'user_email' not in session: return redirect(url_for('login'))
    cases_data = load_json(CASES_FILE, [])
    m_cases = [c for c in cases_data if c.get('user_id') == session['user_email']]
    return render_template('my_cases.html', cases=m_cases)

@app.route('/case/<case_id>')
def case_details(case_id):
    if 'user_email' not in session: return redirect(url_for('login'))
    cases_data = load_json(CASES_FILE, [])
    case = next((c for c in cases_data if str(c['id']) == str(case_id)), None)
    return render_template('case_details.html', case=case)

@app.route('/case_management/<case_id>')
def case_management(case_id):
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    cases_data = load_json(CASES_FILE, [])
    case = next((c for c in cases_data if str(c['id']) == str(case_id)), None)
    return render_template('case_management.html', case=case)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
