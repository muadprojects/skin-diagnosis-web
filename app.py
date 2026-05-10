
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

def init_data():
    users = []
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r', encoding='utf-8') as f: users = json.load(f)
        except: users = []
    
    demo_accounts = [
        {'name': 'المدير العام', 'email': 'admin@dermascan.com', 'password': 'admin123', 'type': 'admin'},
        {'name': 'د. شعيب', 'email': 'doctor@test.com', 'password': '123', 'type': 'doctor'},
        {'name': 'مريض تجريبي', 'email': 'patient@test.com', 'password': '123', 'type': 'patient'}
    ]
    
    emails = [u['email'] for u in users]
    updated = False
    for acc in demo_accounts:
        if acc['email'] not in emails:
            users.append(acc)
            updated = True
    if updated or not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', encoding='utf-8') as f: json.dump(users, f, ensure_ascii=False, indent=2)
    if not os.path.exists(CASES_FILE):
        with open(CASES_FILE, 'w', encoding='utf-8') as f: json.dump([], f)

init_data()

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
    'akiec': 'التقرن الشعاعي', 'bcc': 'سرطان الخلايا القاعدية', 'bkl': 'آفات شبيهة بالتقرن الحميد',
    'df': 'الورم الليفي الجلدي', 'nv': 'الشامات الميلانينية', 'mel': 'سرطان الجلد الميلانيني', 'vasc': 'آفات الأوعية الدموية'
}
CLASS_NAMES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

@app.route('/')
def dashboard():
    if 'user_email' not in session: return redirect(url_for('login'))
    cases_data = load_json(CASES_FILE, [])
    u_type = session.get('user_type', 'patient')
    u_email = session.get('user_email')
    if u_type in ['admin', 'doctor']:
        recent = sorted([c for c in cases_data if 'created_at' in c], key=lambda x: x['created_at'], reverse=True)[:5]
    else:
        recent = sorted([c for c in cases_data if c.get('user_id') == u_email], key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    return render_template('dashboard.html', recent_cases=recent, user_name=session.get('user_name'), user_type=u_type)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, pwd = request.form.get('email'), request.form.get('password')
        users = load_json(USERS_FILE, [])
        for u in users:
            if u['email'] == email and u.get('password') == pwd:
                session.update({'user_email': u['email'], 'user_name': u['name'], 'user_type': u.get('type', 'patient')})
                return redirect(url_for('dashboard'))
        return render_template('login.html', error="بيانات غير صحيحة")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# تغيير اسم الدالة ليكون diagnosis ليتوافق مع القوالب
@app.route('/diagnose', methods=['GET', 'POST'])
@app.route('/diagnosis', methods=['GET', 'POST'])
def diagnosis():
    if 'user_email' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        m, bm = get_models()
        if not m: return render_template('diagnose.html', error="الموديل جاري تحميله...")
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
                res = {'code': code, 'arabic_name': DISEASES.get(code, code), 'percentage': float(pred[idx]*100)}
                cases_data = load_json(CASES_FILE, [])
                cases_data.append({'id': str(uuid.uuid4()), 'user_id': session['user_email'], 'user_name': session['user_name'], 'image_path': fname, 'disease': code, 'confidence': float(pred[idx]), 'created_at': datetime.now().isoformat()})
                save_json(CASES_FILE, cases_data)
                return render_template('diagnose.html', result=res, image_path=fname)
            except Exception as e: return render_template('diagnose.html', error=str(e))
    return render_template('diagnose.html')

@app.route('/statistics')
def statistics():
    if 'user_email' not in session: return redirect(url_for('login'))
    cases_data = load_json(CASES_FILE, [])
    counts = {v: 0 for v in DISEASES.values()}
    for c in cases_data:
        name = DISEASES.get(c.get('disease'), 'غير معروف')
        if name in counts: counts[name] += 1
    return render_template('statistics.html', total_cases=len(cases_data), diseases_count=counts, most_common=sorted(counts.items(), key=lambda x:x[1], reverse=True), avg_confidence=95)

@app.route('/settings')
def settings():
    if 'user_email' not in session: return redirect(url_for('login'))
    return render_template('settings.html', user={'name': session.get('user_name'), 'email': session.get('user_email'), 'type': session.get('user_type')})

@app.route('/add_case', methods=['GET', 'POST'])
def add_case():
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    if request.method == 'POST':
        cases_data = load_json(CASES_FILE, [])
        new_id = str(uuid.uuid4())
        cases_data.append({'id': new_id, 'patient_name': request.form.get('patient_name'), 'created_at': datetime.now().isoformat(), 'diagnoses': []})
        save_json(CASES_FILE, cases_data)
        return redirect(url_for('cases'))
    return render_template('add_case.html', next_case_number=1)

@app.route('/cases')
def cases():
    if 'user_email' not in session: return redirect(url_for('login'))
    cases_data = load_json(CASES_FILE, [])
    return render_template('cases.html', cases=cases_data)

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
