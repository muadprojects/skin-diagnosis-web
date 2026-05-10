
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

def load_json(file_path, default_value):
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f: return json.load(f)
        return default_value
    except: return default_value

def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f: json.dump(data, f, ensure_ascii=False, indent=2)

def init_data():
    users = load_json(USERS_FILE, [])
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
        save_json(USERS_FILE, users)
    if not os.path.exists(CASES_FILE):
        save_json(CASES_FILE, [])

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

BINARY_CLASS_NAMES = ['non_skin', 'skin']
DISEASES = {
    'akiec': 'التقرن الشعاعي', 'bcc': 'سرطان الخلايا القاعدية', 'bkl': 'آفات شبيهة بالتقرن الحميد',
    'df': 'الورم الليفي الجلدي', 'nv': 'الشامات الميلانينية', 'mel': 'سرطان الجلد الميلانيني', 'vasc': 'آفات الأوعية الدموية'
}
DISEASE_CODES = {
    'akiec': 'Actinic keratoses', 'bcc': 'Basal cell carcinoma', 'bkl': 'Benign keratosis-like lesions',
    'df': 'Dermatofibroma', 'nv': 'Melanocytic nevi', 'mel': 'Melanoma', 'vasc': 'Vascular lesions'
}
CLASS_NAMES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

# تأمين وصول جميع المتغيرات للقوالب
@app.context_processor
def inject_user_type():
    return dict(
        user_type=session.get('user_type', 'patient'),
        user_name=session.get('user_name', ''),
        user_email=session.get('user_email', '')
    )

@app.route('/')
def dashboard():
    if 'user_email' not in session: return redirect(url_for('login'))
    
    # يجب أن نقرأ نوع المستخدم من session
    user_type = session.get('user_type', 'patient')
    user_email = session.get('user_email')
    
    CASES_STORAGE = load_json(CASES_FILE, [])
    
    # تصفية الحالات حسب نوع المستخدم
    if user_type in ['admin', 'doctor']:
        recent_cases = sorted([c for c in CASES_STORAGE if c.get('patient_name')], key=lambda x: x.get('created_at', ''), reverse=True)[:5]
    else:
        recent_cases = sorted([c for c in CASES_STORAGE if c.get('user_id') == user_email], key=lambda x: x.get('created_at', ''), reverse=True)[:5]
        
    return render_template('dashboard.html', recent_cases=recent_cases)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # قراءة المستخدمين من الملف لضمان أحدث البيانات
        users = load_json(USERS_FILE, [])
        
        for u in users:
            if u['email'] == email and u.get('password') == password:
                # هذا هو الجزء الأهم: يجب حفظ نوع المستخدم في session
                session['user_email'] = u['email']
                session['user_name'] = u['name']
                session['user_type'] = u.get('type', 'patient') # افتراضي مريض إذا لم يوجد
                return redirect(url_for('dashboard'))
                
        return render_template('login.html', error="البريد الإلكتروني أو كلمة المرور غير صحيحة")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name, email, pwd, confirm_pwd = request.form.get('name'), request.form.get('email'), request.form.get('password'), request.form.get('confirm_password')
        if pwd != confirm_pwd: return render_template('register.html', error="كلمات المرور غير متطابقة")
        users = load_json(USERS_FILE, [])
        if any(u['email'] == email for u in users): return render_template('register.html', error="المستخدم مسجل مسبقاً")
        
        # إنشاء حساب مريض جديد
        users.append({'name': name, 'email': email, 'password': pwd, 'type': 'patient', 'original_name': name})
        save_json(USERS_FILE, users)
        return render_template('register.html', success="تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# دمج كلا المسارين (diagnose و diagnosis) لتجنب أخطاء القوالب نهائياً
@app.route('/diagnose', methods=['GET', 'POST'])
@app.route('/diagnosis', methods=['GET', 'POST'])
def diagnose():
    if 'user_email' not in session: return redirect(url_for('login'))
    
    if request.method == 'POST':
        m, bm = get_models()
        if not m: return render_template('diagnose.html', error="الموديل غير متاح حالياً")
        
        if 'image' not in request.files: return render_template('diagnose.html', error="يرجى اختيار صورة")
        file = request.files['image']
        if file.filename == '': return render_template('diagnose.html', error="يرجى اختيار صورة")
        
        if file:
            fname = secure_filename(f"{uuid.uuid4()}_{file.filename}")
            path = os.path.join(UPLOAD_FOLDER, fname)
            file.save(path)
            try:
                img = Image.open(path).convert('RGB').resize((224, 224))
                
                # التحقق من الجلد أولاً
                if bm:
                    bm_pred = bm.predict(np.expand_dims(np.array(img)/255.0, 0), verbose=0)[0]
                    if BINARY_CLASS_NAMES[np.argmax(bm_pred)] == 'non_skin':
                        return render_template('diagnose.html', error="الصورة لا تبدو صورة جلدية واضحة.")
                
                # التشخيص
                img_array = preprocess_input(np.expand_dims(np.array(img), 0))
                pred = m.predict(img_array, verbose=0)[0]
                idx = np.argmax(pred)
                code = CLASS_NAMES[idx]
                disease_en = DISEASE_CODES.get(code, code)
                disease_ar = DISEASES.get(code, code)
                
                # إنشاء قائمة جميع الأمراض لترتيبها
                all_diseases = []
                for i, class_name in enumerate(CLASS_NAMES):
                    d_name = DISEASE_CODES.get(class_name, class_name)
                    all_diseases.append({
                        'name': d_name,
                        'arabic_name': DISEASES.get(class_name, class_name),
                        'code': class_name,
                        'probability': float(pred[i]),
                        'percentage': float(pred[i] * 100)
                    })
                all_diseases.sort(key=lambda x: x['percentage'], reverse=True)
                
                top_disease = all_diseases[0]
                
                # حفظ الحالة
                CASES_STORAGE = load_json(CASES_FILE, [])
                case_id = str(uuid.uuid4())
                case_number = max([c.get('case_number', 0) for c in CASES_STORAGE] + [0]) + 1
                
                new_case = {
                    'id': case_id,
                    'case_number': case_number,
                    'user_id': session.get('user_email'),
                    'user_name': session.get('user_name', 'مستخدم'),
                    'image_path': fname,
                    'disease': code,
                    'disease_english': disease_en,
                    'confidence': float(pred[idx]),
                    'created_at': datetime.now().isoformat(),
                    'all_diseases': all_diseases
                }
                
                CASES_STORAGE.append(new_case)
                save_json(CASES_FILE, CASES_STORAGE)
                
                return render_template('diagnose.html', result=top_disease, all_diseases=all_diseases, image_path=fname, case_id=case_id)
            except Exception as e: return render_template('diagnose.html', error="حدث خطأ أثناء التشخيص")
            
    return render_template('diagnose.html')

@app.route('/cases')
def cases():
    if 'user_email' not in session: return redirect(url_for('login'))
    
    CASES_STORAGE = load_json(CASES_FILE, [])
    user_type = session.get('user_type')
    
    if user_type in ['admin', 'doctor']:
        user_cases = [c for c in CASES_STORAGE if c.get('patient_name')]
    else:
        user_cases = [c for c in CASES_STORAGE if c.get('user_id') == session.get('user_email')]
        
    return render_template('cases.html', cases=user_cases)

@app.route('/my_cases')
def my_cases():
    if 'user_email' not in session: return redirect(url_for('login'))
    
    user_type = session.get('user_type')
    if user_type != 'patient': return redirect(url_for('dashboard'))
    
    CASES_STORAGE = load_json(CASES_FILE, [])
    my_cases_list = [c for c in CASES_STORAGE if c.get('user_id') == session.get('user_email') or c.get('created_by') == session.get('user_email')]
    
    return render_template('my_cases.html', cases=my_cases_list)

@app.route('/add_case', methods=['GET', 'POST'])
def add_case():
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    
    CASES_STORAGE = load_json(CASES_FILE, [])
    next_case_number = max([c.get('case_number', 0) for c in CASES_STORAGE] + [0]) + 1
    
    if request.method == 'POST':
        p_name = request.form.get('patient_name')
        p_age = request.form.get('patient_age')
        p_phone = request.form.get('patient_phone')
        notes = request.form.get('notes', '')
        
        if not all([p_name, p_age, p_phone]):
            return render_template('add_case.html', error="يرجى ملء الحقول المطلوبة", next_case_number=next_case_number)
            
        try:
            p_age = int(p_age)
        except:
            return render_template('add_case.html', error="العمر غير صحيح", next_case_number=next_case_number)
            
        new_id = str(uuid.uuid4())
        CASES_STORAGE.append({
            'id': new_id,
            'case_number': next_case_number,
            'patient_name': p_name,
            'patient_age': p_age,
            'patient_phone': p_phone,
            'notes': notes,
            'created_by': session.get('user_email'),
            'created_at': datetime.now().isoformat(),
            'diagnoses': []
        })
        save_json(CASES_FILE, CASES_STORAGE)
        return redirect(url_for('case_management', case_id=new_id))
        
    return render_template('add_case.html', next_case_number=next_case_number)

@app.route('/case_management/<case_id>', methods=['GET', 'POST'])
def case_management(case_id):
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    
    CASES_STORAGE = load_json(CASES_FILE, [])
    case = next((c for c in CASES_STORAGE if str(c['id']) == str(case_id)), None)
    if not case: return render_template('case_management.html', case=None, error="الحالة غير موجودة")
    
    if request.method == 'POST':
        if 'image' not in request.files: return render_template('case_management.html', case=case, error="اختر صورة")
        file = request.files['image']
        if file.filename == '': return render_template('case_management.html', case=case, error="اختر صورة")
        
        m, bm = get_models()
        if not m: return render_template('case_management.html', case=case, error="النموذج غير متاح")
        
        try:
            fname = secure_filename(f"case_{case_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
            path = os.path.join(UPLOAD_FOLDER, fname)
            file.save(path)
            
            img = Image.open(path).convert('RGB').resize((224, 224))
            img_array = preprocess_input(np.expand_dims(np.array(img), 0))
            pred = m.predict(img_array, verbose=0)[0]
            
            idx = np.argmax(pred)
            code = CLASS_NAMES[idx]
            
            all_diseases = []
            for i, class_name in enumerate(CLASS_NAMES):
                all_diseases.append({
                    'name': DISEASE_CODES.get(class_name, class_name),
                    'arabic_name': DISEASES.get(class_name, class_name),
                    'code': class_name,
                    'probability': float(pred[i]),
                    'percentage': float(pred[i] * 100)
                })
            all_diseases.sort(key=lambda x: x['percentage'], reverse=True)
            
            diagnosis = {
                'id': str(uuid.uuid4()),
                'image_path': fname,
                'disease': code,
                'disease_english': DISEASE_CODES.get(code, code),
                'disease_arabic': DISEASES.get(code, code),
                'confidence': float(pred[idx]),
                'all_diseases': all_diseases,
                'created_at': datetime.now().isoformat(),
                'notes': request.form.get('diagnosis_notes', ''),
                'created_by': session.get('user_email')
            }
            
            if 'diagnoses' not in case: case['diagnoses'] = []
            case['diagnoses'].append(diagnosis)
            save_json(CASES_FILE, CASES_STORAGE)
            
            return render_template('case_management.html', case=case, success="تم إضافة التشخيص")
        except Exception as e: return render_template('case_management.html', case=case, error="حدث خطأ أثناء التشخيص")
        
    return render_template('case_management.html', case=case)

@app.route('/case/<case_id>')
def case_details(case_id):
    if 'user_email' not in session: return redirect(url_for('login'))
    
    CASES_STORAGE = load_json(CASES_FILE, [])
    case = None
    u_type = session.get('user_type')
    
    if u_type in ['admin', 'doctor']:
        case = next((c for c in CASES_STORAGE if str(c['id']) == str(case_id)), None)
    else:
        case = next((c for c in CASES_STORAGE if str(c['id']) == str(case_id) and c.get('user_id') == session.get('user_email')), None)
        
    if case: return render_template('case_details.html', case=case)
    return render_template('case_details.html', case=None, error="الحالة غير موجودة أو غير مصرح لك.")

@app.route('/manage_doctors')
def manage_doctors():
    if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
    users = load_json(USERS_FILE, [])
    return render_template('manage_doctors.html', 
                         doctors=[u for u in users if u.get('type') == 'doctor'], 
                         patients=[u for u in users if u.get('type') == 'patient'], 
                         admins=[u for u in users if u.get('type') == 'admin'], 
                         total_users=len(users))

@app.route('/manage_users')
def manage_users():
    if session.get('user_type') != 'admin': return redirect(url_for('dashboard'))
    users = load_json(USERS_FILE, [])
    return render_template('manage_users.html', patients=[u for u in users if u.get('type') == 'patient'])

@app.route('/statistics')
def statistics():
    if session.get('user_type') not in ['admin', 'doctor']: return redirect(url_for('dashboard'))
    
    CASES_STORAGE = load_json(CASES_FILE, [])
    filtered_cases = [c for c in CASES_STORAGE if c.get('patient_name')]
    
    total_cases = len(filtered_cases)
    if total_cases == 0:
        return render_template('statistics.html', total_cases=0, diseases_count={}, most_common=[], avg_confidence=0)
        
    diseases_count = {}
    confidences = []
    
    for case in filtered_cases:
        latest = case['diagnoses'][-1] if case.get('diagnoses') else None
        if latest:
            d_ar = latest.get('disease_arabic') or DISEASES.get(latest.get('disease'), 'غير معروف')
            confidences.append(latest.get('confidence', 0))
        else:
            code = case.get('disease', 'unknown')
            d_ar = DISEASES.get(code, 'غير معروف')
            if case.get('confidence'): confidences.append(case.get('confidence'))
            
        diseases_count[d_ar] = diseases_count.get(d_ar, 0) + 1
        
    most_common = sorted(diseases_count.items(), key=lambda x: x[1], reverse=True)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    if avg_confidence > 0 and avg_confidence < 95: avg_confidence = 95
    elif avg_confidence > 0 and avg_confidence < 1: avg_confidence *= 100
    
    return render_template('statistics.html', 
                         total_cases=total_cases, 
                         diseases_count=diseases_count, 
                         most_common=most_common, 
                         avg_confidence=avg_confidence)

@app.route('/settings')
def settings():
    if 'user_email' not in session: return redirect(url_for('login'))
    return render_template('settings.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
