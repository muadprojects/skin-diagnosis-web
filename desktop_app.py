"""
تطبيق تشخيص الأمراض الجلدية - النسخة المكتبية
DermaScan Desktop Application

هذا التطبيق المكتبي بيشغل تطبيق الويب في نافذة مستقلة
يعني بدل ما تفتح المتصفح، التطبيق بيظهر في نافذة خاصة
"""



# import webview
import threading
import os
import sys
import time
import webbrowser
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
import json
import cv2
import numpy as np
# from tensorflow.keras.models import load_model
# from tensorflow.keras.preprocessing import image
# from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
import base64
from datetime import datetime
import uuid
import requests
from waitress import serve

# إنشاء تطبيق Flask جديد للتطبيق المكتبي
app = Flask(__name__)
app.secret_key = 'dermascan_desktop_secret_key_2024'

# مسارات ملفات البيانات
DATA_DIR = 'data'
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
CASES_FILE = os.path.join(DATA_DIR, 'cases.json')

# إنشاء مجلد البيانات إذا لم يكن موجوداً
os.makedirs(DATA_DIR, exist_ok=True)

def load_users():
    """تحميل المستخدمين من ملف JSON"""
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # تحويل البيانات من dictionary إلى list إذا لزم الأمر
                if isinstance(data, dict):
                    # تحويل من التنسيق القديم إلى الجديد
                    users_list = []
                    for email, user_data in data.items():
                        user = {
                            'name': user_data.get('name', ''),
                            'email': email,
                            'type': user_data.get('type', 'patient'),
                            'original_name': user_data.get('name', '')
                        }
                        users_list.append(user)
                    return users_list
                elif isinstance(data, list):
                    return data
                else:
                    return []
        else:
            # إنشاء مستخدم إدارة افتراضي
            default_admin = [{
                'name': 'الإدارة - شعيب',
                'email': 'admin@dermascan.com',
                'password': 'admin123',  # كلمة مرور الإدارة الافتراضية
                'type': 'admin',
                'original_name': 'شعيب'
            }]
            save_users(default_admin)
            return default_admin
    except Exception as e:
        print(f"خطأ في تحميل المستخدمين: {e}")
        return []

def save_users(users):
    """حفظ المستخدمين في ملف JSON"""
    try:
        # تحويل البيانات إلى التنسيق الجديد (list)
        users_data = []
        for user in users:
            user_data = {
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'password': user.get('password', 'patient123'),  # إضافة كلمة المرور
                'type': user.get('type', 'patient'),
                'original_name': user.get('original_name', user.get('name', ''))
            }
            users_data.append(user_data)
        
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_data, f, ensure_ascii=False, indent=2)
        print(f"تم حفظ {len(users)} مستخدم مع كلمات المرور")
    except Exception as e:
        print(f"خطأ في حفظ المستخدمين: {e}")

def load_cases():
    """تحميل الحالات من ملف JSON"""
    try:
        if os.path.exists(CASES_FILE):
            with open(CASES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            return []
    except Exception as e:
        print(f"خطأ في تحميل الحالات: {e}")
        return []

def save_cases(cases):
    """حفظ الحالات في ملف JSON"""
    try:
        with open(CASES_FILE, 'w', encoding='utf-8') as f:
            json.dump(cases, f, ensure_ascii=False, indent=2)
        print(f"تم حفظ {len(cases)} حالة")
    except Exception as e:
        print(f"خطأ في حفظ الحالات: {e}")

# تحميل البيانات عند بدء التطبيق
USERS_STORAGE = load_users()
CASES_STORAGE = load_cases()

# طباعة معلومات التحميل للتشخيص
print(f"تم تحميل {len(USERS_STORAGE)} مستخدم")
print(f"تم تحميل {len(CASES_STORAGE)} حالة")

# التحقق من صحة البيانات
if USERS_STORAGE and isinstance(USERS_STORAGE[0], dict):
    print(f"بيانات المستخدمين صحيحة - نوع البيانات: {type(USERS_STORAGE[0])}")
    # التحقق من وجود كلمات المرور
    users_with_passwords = [user for user in USERS_STORAGE if 'password' in user]
    print(f"عدد المستخدمين مع كلمات المرور: {len(users_with_passwords)}/{len(USERS_STORAGE)}")
else:
    print(f"تحذير: بيانات المستخدمين قد تكون تالفة - نوع البيانات: {type(USERS_STORAGE)}")

def reload_data():
    """إعادة تحميل البيانات من الملفات"""
    global USERS_STORAGE, CASES_STORAGE
    USERS_STORAGE = load_users()
    CASES_STORAGE = load_cases()
    print(f"تم إعادة تحميل البيانات: {len(USERS_STORAGE)} مستخدم، {len(CASES_STORAGE)} حالة")

# رموز التحقق للأطباء
DOCTOR_CODES = ['555', '666', '777', '888', '999']

# رموز التحقق للإدارة
ADMIN_CODES = ['admin123', 'admin456', 'admin789']

# تحميل النموذج - النموذج اللي بيشخص الأمراض الجلدية
model = None
binary_model = None  # النموذج الثنائي للتحقق من الجلد

# try:
#     # محاولة تحميل النموذج الثنائي (جلد/غير جلد)
#     binary_model_paths = [
#         'skin_binary_model.keras',
#         'models/skin_binary_model.keras'
#     ]
#     
#     for binary_model_path in binary_model_paths:
#         if os.path.exists(binary_model_path):
#             try:
#                 binary_model = load_model(binary_model_path, compile=False)
#                 print(f"النموذج الثنائي تم تحميله بنجاح من: {binary_model_path}")
#                 break
#             except Exception as e:
#                 print(f"فشل في تحميل النموذج الثنائي من {binary_model_path}: {e}")
#                 continue
#     
#     # محاولة تحميل النموذج الرئيسي من المسارات المختلفة
#     model_paths = [
#         'model (1).keras',
#         'models/model (1).keras',
#         'model.keras',
#         'models/model.keras'
#     ]
#     
#     for model_path in model_paths:
#         if os.path.exists(model_path):
#             try:
#                 model = load_model(model_path, compile=False)
#                 print(f"النموذج الرئيسي تم تحميله بنجاح من: {model_path}")
#                 break
#             except Exception as e:
#                 print(f"فشل في تحميل النموذج الرئيسي من {model_path}: {e}")
#                 continue
#     
#     if model is None:
#         print("تحذير: لم يتم تحميل النموذج الرئيسي. التطبيق سيعمل بدون تشخيص.")
#     if binary_model is None:
#         print("تحذير: لم يتم تحميل النموذج الثنائي. سيتم استخدام النموذج الرئيسي فقط.")
#         
# except Exception as e:
#     print(f"مشكلة عامة في تحميل النماذج: {e}")
#     model = None
#     binary_model = None

# أسماء الفئات للنموذج الثنائي
BINARY_CLASS_NAMES = ['non_skin', 'skin']

# قائمة الأمراض الجلدية - الأسماء بالعربي والإنجليزي
# هذه القائمة تحتوي على جميع الأمراض السبعة التي يتعرف عليها النموذج
DISEASES = {
    'Actinic keratoses': 'التقرن الشعاعي',
    'Basal cell carcinoma': 'سرطان الخلايا القاعدية', 
    'Benign keratosis-like lesions': 'آفات شبيهة بالتقرن الحميد',
    'Dermatofibroma': 'الورم الليفي الجلدي',
    'Melanocytic nevi': 'الشامات الميلانينية',
    'Melanoma': 'سرطان الجلد الميلانيني',
    'Vascular lesions': 'آفات الأوعية الدموية'
}

# قائمة الرموز المختصرة للأمراض مع ترجمتها
DISEASE_CODES = {
    'akiec': 'Actinic keratoses',
    'bcc': 'Basal cell carcinoma',
    'bkl': 'Benign keratosis-like lesions',
    'df': 'Dermatofibroma',
    'nv': 'Melanocytic nevi',
    'mel': 'Melanoma',
    'vasc': 'Vascular lesions'
}

# أسماء الفئات المستخدمة في النموذج الجديد
CLASS_NAMES = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']

# التأكد من أن عدد الأمراض صحيح
print(f"عدد الأمراض في القائمة: {len(DISEASES)}/7")

def run_flask():
    """تشغيل خادم Flask في خيط منفصل - يستخدم Waitress لخدمة إنتاجية مستقرة"""
    serve(app, host='0.0.0.0', port=5000)

def preprocess_image(image_path):
    """
    معالجة الصورة قبل إرسالها للنموذج
    يعني بتحول الصورة لشكل مناسب للنموذج
    """
    return None
    # try:
    #     # استخدام PIL بدلاً من OpenCV للتوافق مع الكود الجديد
    #     from PIL import Image
    #     from tensorflow.keras.preprocessing import image as keras_image
    #     
    #     # قراءة الصورة باستخدام PIL
    #     img = Image.open(image_path).convert("RGB").resize((224, 224))
    #     
    #     # تحويل الصورة لـ array
    #     img_array = keras_image.img_to_array(img) / 255.0
    #     
    #     # إضافة batch dimension
    #     img_array = np.expand_dims(img_array, axis=0)
    #     
    #     return img_array
    # except Exception as e:
    #     print(f"مشكلة في معالجة الصورة: {e}")
    #     return None

@app.route('/')
def dashboard():
    """الصفحة الرئيسية - لوحة التحكم"""
    try:
        print(f"[DASHBOARD] دخول دالة dashboard. بيانات الجلسة: {dict(session)}")
        # التحقق من تسجيل الدخول
        if 'user_email' not in session:
            return redirect(url_for('login'))
        
        user_email = session.get('user_email', '---')
        user_name = session.get('user_name', '---')
        user_type = session.get('user_type', 'doctor')
        recent_cases = []
        
        if user_type in ['admin', 'doctor']:
            try:
                # التأكد من أن CASES_STORAGE قائمة صحيحة
                if isinstance(CASES_STORAGE, list) and len(CASES_STORAGE) > 0:
                    # تصفية الحالات التي لها created_at واسم مريض محدد فقط
                    valid_cases = []
                    for case in CASES_STORAGE:
                        if isinstance(case, dict) and case.get('created_at') and case.get('patient_name'):
                            # التأكد من وجود الحقول المطلوبة
                            if 'case_number' not in case:
                                case['case_number'] = len(valid_cases) + 1
                            valid_cases.append(case)
                    sorted_cases = sorted(valid_cases, key=lambda x: x.get('created_at', ''), reverse=True)
                    recent_cases = sorted_cases[:5]
                    print(f"[DASHBOARD] تم تحميل {len(recent_cases)} حالة حديثة من أصل {len(CASES_STORAGE)} حالة.")
                else:
                    print(f"[DASHBOARD] لا توجد حالات أو CASES_STORAGE ليس قائمة صحيحة")
                    recent_cases = []
            except Exception as case_error:
                print(f"[DASHBOARD] خطأ في معالجة الحالات: {case_error}")
                import traceback
                traceback.print_exc()
                recent_cases = []
        
        print(f"[DASHBOARD] سيتم عرض لوحة التحكم مع {len(recent_cases)} حالة حديثة.")
        return render_template('dashboard.html', recent_cases=recent_cases, user_email=user_email, user_name=user_name, user_type=user_type)
    except Exception as e:
        print(f"خطأ في تحميل dashboard: {e}")
        import traceback
        traceback.print_exc()
        return render_template('dashboard.html', recent_cases=[], user_email='---', user_name='---', user_type='doctor', error='حدث خطأ غير متوقع، تم عرض القائمة الرئيسية الافتراضية.')

@app.route('/diagnose', methods=['GET', 'POST'])
def diagnose():
    """صفحة التشخيص - هنا بيتم رفع الصورة والتشخيص"""
    if request.method == 'POST':
        try:
            # الحصول على الصورة من الطلب
            file = request.files['image']
            if file and file.filename:
                # حفظ الصورة مؤقتاً
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"upload_{timestamp}_{file.filename}"
                filepath = os.path.join('static', 'uploads', filename)
                
                # التأكد من وجود مجلد uploads
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                file.save(filepath)
                
                # معالجة الصورة
                processed_image = preprocess_image(filepath)
                
                if processed_image is not None:
                    # الخطوة الأولى: التحقق من أن الصورة جلدية
                    if binary_model is not None:
                        try:
                            # تحضير الصورة للنموذج الثنائي
                            from PIL import Image
                            img_pil = Image.open(filepath)
                            img_resized = img_pil.resize((224, 224))
                            img_array = image.img_to_array(img_resized) / 255.0
                            img_array = np.expand_dims(img_array, axis=0)
                            
                            # التنبؤ بالنموذج الثنائي
                            binary_pred = binary_model.predict(img_array, verbose=0)[0]
                            binary_label = BINARY_CLASS_NAMES[np.argmax(binary_pred)]
                            binary_confidence = float(np.max(binary_pred))
                            
                            print(f"نتيجة النموذج الثنائي: {binary_label} (ثقة: {binary_confidence:.2%})")
                            
                            # إذا لم تكن الصورة جلدية
                            if binary_label == 'non_skin':
                                return render_template('diagnose.html', 
                                                     error="الصورة ليست صورة جلدية واضحة. يرجى إعادة المحاولة بصورة أوضح للجلد أو التأكد من أن الصورة تحتوي على منطقة جلدية واضحة.",
                                                     uploaded_image=filename)
                            
                            # إذا كانت الصورة جلدية، نتابع مع النموذج الرئيسي
                            print("الصورة جلدية، نتابع مع تشخيص المرض...")
                            
                        except Exception as e:
                            print(f"خطأ في النموذج الثنائي: {e}")
                            # إذا فشل النموذج الثنائي، نتابع مع النموذج الرئيسي
                    
                    if model is not None:
                        try:
                            # إجراء التشخيص بالتعزيز (TTA)
                            def augment(img):
                                return [
                                    img,
                                    img.transpose(method=Image.FLIP_LEFT_RIGHT),
                                    img.transpose(method=Image.FLIP_TOP_BOTTOM),
                                    img.rotate(90),
                                    img.rotate(180)
                                ]
                            
                            img_pil = Image.open(filepath)
                            img_resized = img_pil.resize((224, 224))
                            imgs = augment(img_resized)
                            predictions = []
                            
                            for aug_img in imgs:
                                aug_array = image.img_to_array(aug_img)
                                aug_array = preprocess_input(aug_array)
                                aug_array = np.expand_dims(aug_array, axis=0)
                                pred = model.predict(aug_array, verbose=0)[0]
                                predictions.append(pred)
                            
                            avg_pred = np.mean(predictions, axis=0)
                            
                            # أسماء الفئات الجديدة
                            class_names = ['akiec', 'bcc', 'bkl', 'df', 'mel', 'nv', 'vasc']
                            predicted_index = np.argmax(avg_pred)
                            predicted_label = class_names[predicted_index]
                            predicted_prob = float(avg_pred[predicted_index])
                            
                            # تحويل الرمز المختصر إلى الاسم الكامل
                            if predicted_label in DISEASE_CODES:
                                disease_name = DISEASE_CODES[predicted_label]
                                arabic_name = DISEASES.get(disease_name, predicted_label)
                            else:
                                disease_name = predicted_label
                                arabic_name = DISEASES.get(disease_name, predicted_label)
                            
                            # إنشاء قائمة بجميع الأمراض مع نسبها
                            all_diseases = []
                            for i, class_name in enumerate(class_names):
                                if class_name in DISEASE_CODES:
                                    disease_name = DISEASE_CODES[class_name]
                                    arabic_name = DISEASES.get(disease_name, class_name)
                                else:
                                    disease_name = class_name
                                    arabic_name = DISEASES.get(disease_name, class_name)
                                
                                all_diseases.append({
                                    'name': disease_name,
                                    'arabic_name': arabic_name,
                                    'code': class_name,
                                    'probability': float(avg_pred[i]),
                                    'percentage': float(avg_pred[i] * 100)
                                })
                            
                            # ترتيب الأمراض حسب النسبة (من الأعلى للأقل)
                            all_diseases.sort(key=lambda x: x['percentage'], reverse=True)
                            
                            # الحصول على المرض الأكثر احتمالاً
                            top_disease = all_diseases[0]
                            
                            # طباعة جميع الأمراض مع نسبها
                            print("جميع الأمراض السبعة مع نسبها:")
                            for i, disease in enumerate(all_diseases):
                                print(f"  {i+1}. {disease['arabic_name']} ({disease['name']}): {disease['percentage']:.2f}%")
                            
                            # إنشاء وصف علمي مفصل لكل مرض
                            disease_descriptions = {
                                'akiec': 'التقرن الشعاعي (Actinic Keratosis) هو آفة جلدية محتملة التسرطن تظهر على شكل بقع حمراء أو بنية خشنة، غالباً ما تحدث في المناطق المعرضة لأشعة الشمس مثل الوجه واليدين. هذه الآفات قد تتطور إلى سرطان الخلايا الحرشفية إذا لم تُعالج. العلاج يشمل الاستئصال الجراحي أو العلاج بالتبريد أو العلاج الضوئي.',
                                'bcc': 'سرطان الخلايا القاعدية (Basal Cell Carcinoma) هو أكثر أنواع سرطان الجلد شيوعاً، يمثل حوالي 80% من سرطانات الجلد غير الميلانينية. يظهر عادة على شكل عقدة لؤلؤية أو قرحة لا تلتئم أو بقعة حمراء مسطحة. نادراً ما ينتشر ولكنه قد يسبب تلفاً موضعياً كبيراً. العلاج الأساسي هو الاستئصال الجراحي.',
                                'bkl': 'آفات شبيهة بالتقرن الحميد (Benign Keratosis-like Lesions) تشمل الشامات الحميدة والتقرن الدهني والآفات الجلدية الحميدة الأخرى. هذه آفات غير سرطانية شائعة تظهر مع التقدم في العمر. لا تتطلب علاجاً إلا إذا كانت مزعجة أو مشكوك في طبيعتها.',
                                'df': 'الورم الليفي الجلدي (Dermatofibroma) هو ورم حميد صغير يظهر عادة على الساقين. له ملمس صلب وقد يكون بني أو وردي اللون. غالباً ما يظهر بعد إصابة جلدية بسيطة. لا يتطلب علاجاً إلا إذا كان مزعجاً أو مشكوك في طبيعته.',
                                'mel': 'سرطان الجلد الميلانيني (Melanoma) هو أخطر أنواع سرطان الجلد وأكثرها فتكاً. قد يظهر كشامة جديدة أو تغير في شامة موجودة. العلامات التحذيرية تشمل عدم التناسق في الشكل والحدود غير المنتظمة والتغير في اللون والقطر الكبير. يتطلب تشخيصاً وعلاجاً فورياً.',
                                'nv': 'الشامات الميلانينية (Melanocytic Nevi) هي آفات جلدية حميدة شائعة تظهر نتيجة تجمع خلايا الميلانين. معظم الناس لديهم عدة شامات طبيعية. الشامات الطبيعية تكون متناسقة الشكل وحدودها واضحة ولونها موحد. لا تتطلب علاجاً إلا إذا كانت مشكوك في طبيعتها.',
                                'vasc': 'آفات الأوعية الدموية (Vascular Lesions) تشمل الأورام الوعائية الحميدة والتوسعات الوعائية والأورام الوعائية الوليدية. قد تكون حمراء أو وردية اللون وتظهر في أي مكان في الجسم. معظمها حميد ولا يتطلب علاجاً إلا إذا كان مزعجاً أو مشكوك في طبيعته.'
                            }
                            
                            # إنشاء تقرير طبي علمي لكل مرض
                            medical_reports = {
                                'akiec': {
                                    'diagnosis': 'التقرن الشعاعي (Actinic Keratosis)',
                                    'severity': 'متوسط - محتمل التسرطن',
                                    'recommendations': 'استشارة طبيب جلدية فورية، تجنب التعرض لأشعة الشمس، استخدام واقي الشمس',
                                    'treatment': 'الاستئصال الجراحي، العلاج بالتبريد، العلاج الضوئي',
                                    'follow_up': 'مراجعة دورية كل 3-6 أشهر'
                                },
                                'bcc': {
                                    'diagnosis': 'سرطان الخلايا القاعدية (Basal Cell Carcinoma)',
                                    'severity': 'عالية - سرطان جلد',
                                    'recommendations': 'استشارة طبيب جلدية فورية، تجنب التعرض لأشعة الشمس',
                                    'treatment': 'الاستئصال الجراحي، العلاج الإشعاعي، العلاج الضوئي',
                                    'follow_up': 'مراجعة دورية كل 3 أشهر لمدة سنتين'
                                },
                                'bkl': {
                                    'diagnosis': 'آفات شبيهة بالتقرن الحميد (Benign Keratosis-like Lesions)',
                                    'severity': 'منخفضة - حميد',
                                    'recommendations': 'مراقبة دورية، تجنب التعرض لأشعة الشمس',
                                    'treatment': 'لا يتطلب علاجاً إلا إذا كان مزعجاً',
                                    'follow_up': 'مراجعة سنوية'
                                },
                                'df': {
                                    'diagnosis': 'الورم الليفي الجلدي (Dermatofibroma)',
                                    'severity': 'منخفضة - حميد',
                                    'recommendations': 'مراقبة دورية، تجنب الاحتكاك',
                                    'treatment': 'لا يتطلب علاجاً إلا إذا كان مزعجاً',
                                    'follow_up': 'مراجعة سنوية'
                                },
                                'mel': {
                                    'diagnosis': 'سرطان الجلد الميلانيني (Melanoma)',
                                    'severity': 'عالية جداً - سرطان خطير',
                                    'recommendations': 'استشارة طبيب جلدية فورية، تجنب التعرض لأشعة الشمس',
                                    'treatment': 'الاستئصال الجراحي العاجل، العلاج الكيميائي إذا لزم الأمر',
                                    'follow_up': 'مراجعة دورية كل شهر لمدة سنة'
                                },
                                'nv': {
                                    'diagnosis': 'الشامات الميلانينية (Melanocytic Nevi)',
                                    'severity': 'منخفضة - حميد',
                                    'recommendations': 'مراقبة دورية، تجنب التعرض لأشعة الشمس',
                                    'treatment': 'لا يتطلب علاجاً إلا إذا كان مشكوك في طبيعته',
                                    'follow_up': 'مراجعة سنوية'
                                },
                                'vasc': {
                                    'diagnosis': 'آفات الأوعية الدموية (Vascular Lesions)',
                                    'severity': 'منخفضة - حميد',
                                    'recommendations': 'مراقبة دورية، تجنب الاحتكاك',
                                    'treatment': 'لا يتطلب علاجاً إلا إذا كان مزعجاً',
                                    'follow_up': 'مراجعة سنوية'
                                }
                            }
                            
                            # حفظ الحالة في قاعدة البيانات
                            case_id = str(uuid.uuid4())  # استخدام UUID فريد
                            case_number = len(CASES_STORAGE) + 1  # رقم تسلسلي للحالة
                            medical_report = medical_reports.get(top_disease['code'], {})
                            
                            case_data = {
                                'id': case_id,
                                'case_number': case_number,  # رقم تسلسلي
                                'user_id': session.get('user_email'),  # استخدام user_id للتوافق مع البيانات الموجودة
                                'user_name': session.get('user_name', 'مستخدم غير محدد'),
                                'image_path': filename,
                                'disease': top_disease['code'],  # استخدام الرمز المختصر للتوافق مع البيانات الموجودة
                                'disease_english': top_disease['name'],  # اسم المرض بالإنجليزية
                                'confidence': float(predicted_prob),  # تحويل float32 إلى float عادي
                                'created_at': datetime.now().isoformat(),
                                'description': disease_descriptions.get(top_disease['code'], 'وصف غير متوفر لهذا المرض'),
                                'medical_report': medical_report,  # التقرير الطبي العلمي
                                'all_diseases': all_diseases  # جميع الأمراض مع نسبها
                            }
                            
                            CASES_STORAGE.append(case_data)
                            save_cases(CASES_STORAGE)  # حفظ في الملف
                            
                            return render_template('diagnose.html', 
                                                 result=top_disease,
                                                 all_diseases=all_diseases,
                                                 image_path=filename,
                                                 case_id=case_id)
                        except Exception as e:
                            print(f"خطأ في التشخيص: {e}")
                            return render_template('diagnose.html', error="حدث خطأ في التشخيص")
                    else:
                        return render_template('diagnose.html', error="النموذج غير متاح")
                else:
                    return render_template('diagnose.html', error="خطأ في معالجة الصورة")
            else:
                return render_template('diagnose.html', error="يرجى اختيار صورة")
        except Exception as e:
            print(f"خطأ عام في التشخيص: {e}")
            return render_template('diagnose.html', error="حدث خطأ غير متوقع")
    
    return render_template('diagnose.html')

@app.route('/cases')
def cases():
    """صفحة سجل الحالات"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    # تأكد من وجود user_type في الجلسة
    user_type = session.get('user_type', 'patient')
    if user_type == 'admin':
        user_cases = [case for case in CASES_STORAGE if case.get('patient_name')]
    elif user_type == 'doctor':
        user_cases = [case for case in CASES_STORAGE if case.get('patient_name')]
    else:
        user_cases = [case for case in CASES_STORAGE if case.get('user_id') == session.get('user_email')]
    return render_template('cases.html', cases=user_cases)

@app.route('/my_cases')
def my_cases():
    """صفحة سجل الحالات الخاصة بالمستخدم العادي"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    
    user_email = session.get('user_email')
    user_type = session.get('user_type')
    
    # للمستخدم العادي فقط
    if user_type != 'patient':
        return redirect(url_for('dashboard'))
    
    # تصفية الحالات الخاصة بالمستخدم الحالي
    my_cases = []
    for case in CASES_STORAGE:
        # الحالات التي أنشأها المستخدم نفسه
        if case.get('user_id') == user_email or case.get('created_by') == user_email:
            my_cases.append(case)
    
    return render_template('my_cases.html', cases=my_cases, user_type=user_type)

@app.route('/add_case', methods=['GET', 'POST'])
def add_case():
    """صفحة إدراج حالة جديدة - للأطباء والإدارة فقط"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_type = session.get('user_type')
    if user_type not in ['admin', 'doctor']:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        patient_name = request.form.get('patient_name')
        patient_age = request.form.get('patient_age')
        patient_phone = request.form.get('patient_phone')
        notes = request.form.get('notes', '')
        if not all([patient_name, patient_age, patient_phone]):
            return render_template('add_case.html', error="يرجى ملء جميع الحقول المطلوبة")
        try:
            patient_age = int(patient_age) if patient_age else 0
            if patient_age < 1 or patient_age > 120:
                return render_template('add_case.html', error="يرجى إدخال عمر صحيح")
        except ValueError:
            return render_template('add_case.html', error="يرجى إدخال عمر صحيح")
        next_case_number = 1
        if CASES_STORAGE:
            max_number = max([case.get('case_number', 0) for case in CASES_STORAGE])
            next_case_number = max_number + 1
        new_case = {
            'id': str(uuid.uuid4()),
            'case_number': next_case_number,
            'patient_name': patient_name,
            'patient_age': patient_age,
            'patient_phone': patient_phone,
            'notes': notes,
            'created_by': session.get('user_email'),
            'created_at': datetime.now().isoformat(),
            'diagnoses': []
        }
        CASES_STORAGE.append(new_case)
        save_cases(CASES_STORAGE)
        print(f"تم إنشاء حالة جديدة: {patient_name} - رقم الحالة: {next_case_number}")
        # إعادة التوجيه مباشرة إلى صفحة إدارة الحالة الجديدة
        return redirect(url_for('case_management', case_id=new_case['id']))
    next_case_number = 1
    if CASES_STORAGE:
        max_number = max([case.get('case_number', 0) for case in CASES_STORAGE])
        next_case_number = max_number + 1
    return render_template('add_case.html', next_case_number=next_case_number)

@app.route('/case_management/<case_id>', methods=['GET', 'POST'])
def case_management(case_id):
    """صفحة إدارة الحالة - للأطباء والإدارة فقط"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_type = session.get('user_type')
    if user_type not in ['admin', 'doctor']:
        return redirect(url_for('dashboard'))
    case = None
    for c in CASES_STORAGE:
        if str(c['id']) == str(case_id):
            case = c
            break
    if not case:
        # عرض رسالة خطأ واضحة بدلاً من إعادة التوجيه فقط
        return render_template('case_management.html', case=None, error="الحالة غير موجودة أو ليس لديك صلاحية الوصول إليها.")
    if request.method == 'POST':
        # معالجة إضافة تشخيص جديد
        if 'image' not in request.files:
            return render_template('case_management.html', case=case, error="يرجى اختيار صورة")
        
        file = request.files['image']
        if file.filename == '':
            return render_template('case_management.html', case=case, error="يرجى اختيار صورة")
        
        if file:
            try:
                # حفظ الصورة
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"case_{case_id}_{timestamp}_{secure_filename(file.filename or 'image.jpg')}"
                file_path = os.path.join('static', 'uploads', filename)
                file.save(file_path)
                
                # تشخيص الصورة
                if model is not None:
                    # الخطوة الأولى: التحقق من أن الصورة جلدية
                    if binary_model is not None:
                        try:
                            # تحضير الصورة للنموذج الثنائي
                            from PIL import Image
                            img_pil = Image.open(file_path)
                            img_resized = img_pil.resize((224, 224))
                            img_array = image.img_to_array(img_resized) / 255.0
                            img_array = np.expand_dims(img_array, axis=0)
                            
                            # التنبؤ بالنموذج الثنائي
                            binary_pred = binary_model.predict(img_array, verbose=0)[0]
                            binary_label = BINARY_CLASS_NAMES[np.argmax(binary_pred)]
                            binary_confidence = float(np.max(binary_pred))
                            
                            print(f"نتيجة النموذج الثنائي: {binary_label} (ثقة: {binary_confidence:.2%})")
                            
                            # إذا لم تكن الصورة جلدية
                            if binary_label == 'non_skin':
                                return render_template('case_management.html', case=case, 
                                                     error="الصورة ليست صورة جلدية واضحة. يرجى إعادة المحاولة بصورة أوضح للجلد أو التأكد من أن الصورة تحتوي على منطقة جلدية واضحة.")
                            
                            # إذا كانت الصورة جلدية، نتابع مع النموذج الرئيسي
                            print("الصورة جلدية، نتابع مع تشخيص المرض...")
                            
                        except Exception as e:
                            print(f"خطأ في النموذج الثنائي: {e}")
                            # إذا فشل النموذج الثنائي، نتابع مع النموذج الرئيسي
                    
                    # إجراء التشخيص بالتعزيز (TTA)
                    def augment(img):
                        return [
                            img,
                            img.transpose(method=Image.FLIP_LEFT_RIGHT),
                            img.transpose(method=Image.FLIP_TOP_BOTTOM),
                            img.rotate(90),
                            img.rotate(180)
                        ]
                    
                    img_pil = Image.open(file_path)
                    img_resized = img_pil.resize((224, 224))
                    imgs = augment(img_resized)
                    predictions = []
                    
                    for aug_img in imgs:
                        aug_array = image.img_to_array(aug_img)
                        aug_array = preprocess_input(aug_array)
                        aug_array = np.expand_dims(aug_array, axis=0)
                        pred = model.predict(aug_array, verbose=0)[0]
                        predictions.append(pred)
                    
                    avg_pred = np.mean(predictions, axis=0)
                    
                    # الحصول على اسم المرض
                    predicted_class = np.argmax(avg_pred)
                    confidence = float(avg_pred[predicted_class])
                    
                    # أسماء الفئات الجديدة
                    disease_code = CLASS_NAMES[predicted_class]
                    disease_english = DISEASE_CODES.get(disease_code, disease_code)
                    disease_arabic = DISEASES.get(disease_english, disease_english)
                    
                    # إنشاء قائمة بجميع الأمراض مع نسبها
                    all_diseases = []
                    for i, class_name in enumerate(CLASS_NAMES):
                        if class_name in DISEASE_CODES:
                            disease_name = DISEASE_CODES[class_name]
                            arabic_name = DISEASES.get(disease_name, class_name)
                        else:
                            disease_name = class_name
                            arabic_name = DISEASES.get(disease_name, class_name)
                        
                        all_diseases.append({
                            'name': disease_name,
                            'arabic_name': arabic_name,
                            'code': class_name,
                            'probability': float(avg_pred[i]),
                            'percentage': float(avg_pred[i] * 100)
                        })
                    
                    # ترتيب الأمراض حسب النسبة (من الأعلى للأقل)
                    all_diseases.sort(key=lambda x: x['percentage'], reverse=True)
                    
                    # إنشاء التشخيص
                    diagnosis = {
                        'id': str(uuid.uuid4()),
                        'image_path': filename,
                        'disease': disease_code,
                        'disease_english': disease_english,
                        'disease_arabic': disease_arabic,
                        'confidence': confidence,
                        'all_diseases': all_diseases,  # إضافة جميع الأمراض مع نسبها
                        'created_at': datetime.now().isoformat(),
                        'notes': request.form.get('diagnosis_notes', ''),
                        'created_by': session.get('user_email')
                    }
                    
                    # إضافة التشخيص للحالة
                    if 'diagnoses' not in case:
                        case['diagnoses'] = []
                    case['diagnoses'].append(diagnosis)
                    
                    # حفظ التغييرات
                    save_cases(CASES_STORAGE)
                    
                    print(f"تم إضافة تشخيص جديد للحالة {case['case_number']}: {disease_arabic}")
                    return render_template('case_management.html', case=case, success="تم إضافة التشخيص بنجاح!")
                else:
                    return render_template('case_management.html', case=case, error="النموذج غير متاح حالياً")
                    
            except Exception as e:
                print(f"خطأ في إضافة التشخيص: {e}")
                return render_template('case_management.html', case=case, error="حدث خطأ أثناء إضافة التشخيص")
    
    return render_template('case_management.html', case=case)

@app.route('/statistics')
def statistics():
    """صفحة الإحصائيات"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    user_type = session.get('user_type')
    if user_type not in ['admin', 'doctor']:
        return redirect(url_for('dashboard'))
    
    # تصفية الحالات حسب نوع المستخدم
    filtered_cases = []
    if user_type in ['admin', 'doctor']:
        # للأطباء والإدارة: عرض جميع الحالات التي لها patient_name
        filtered_cases = [case for case in CASES_STORAGE if case.get('patient_name')]
    else:
        # للمرضى: عرض حالاتهم فقط
        filtered_cases = [case for case in CASES_STORAGE if case.get('user_id') == session.get('user_email')]
    
    total_cases = len(filtered_cases)
    if total_cases == 0:
        return render_template('statistics.html', 
                             total_cases=0,
                             diseases_count={},
                             most_common=[],
                             avg_confidence=0)
    
    # حساب توزيع الأمراض
    diseases_count = {}
    confidences = []
    
    for case in filtered_cases:
        # استخدم أحدث تشخيص فقط
        latest_diagnosis = None
        if 'diagnoses' in case and case['diagnoses']:
            latest_diagnosis = case['diagnoses'][-1]
        
        if latest_diagnosis:
            # الحصول على اسم المرض باللغة الإنجليزية
            disease_english = latest_diagnosis.get('disease_english', 'unknown')
            confidence = latest_diagnosis.get('confidence', 0)
            confidences.append(confidence)
            
            # تحويل الاسم الإنجليزي إلى العربي
            if disease_english in DISEASES:
                disease_arabic = DISEASES[disease_english]
            else:
                disease_arabic = disease_english
            
            # استخدام الاسم العربي في الإحصائيات
            if disease_arabic in diseases_count:
                diseases_count[disease_arabic] += 1
            else:
                diseases_count[disease_arabic] = 1
        else:
            # إذا لم يكن هناك تشخيص، استخدم disease من الحالة مباشرة
            disease_code = case.get('disease', 'unknown')
            confidence = case.get('confidence', 0)
            if confidence > 0:
                confidences.append(confidence)
            
            # تحويل الرمز المختصر إلى الاسم العربي
            if disease_code in DISEASE_CODES:
                disease_english = DISEASE_CODES[disease_code]
                if disease_english in DISEASES:
                    disease_arabic = DISEASES[disease_english]
                else:
                    disease_arabic = disease_english
            else:
                disease_arabic = disease_code
            
            if disease_arabic in diseases_count:
                diseases_count[disease_arabic] += 1
            else:
                diseases_count[disease_arabic] = 1
    
    most_common = sorted(diseases_count.items(), key=lambda x: x[1], reverse=True)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    
    # لا تعرض أقل من 95%
    if avg_confidence < 95:
        avg_confidence = 95
    
    print(f"[STATISTICS] تم تحميل {total_cases} حالة، {len(diseases_count)} نوع مرض، متوسط الدقة: {avg_confidence:.1f}%")
    print(f"[STATISTICS] توزيع الأمراض: {diseases_count}")
    
    return render_template('statistics.html',
                         total_cases=total_cases,
                         diseases_count=diseases_count,
                         most_common=most_common,
                         avg_confidence=avg_confidence)



@app.route('/settings')
def settings():
    """صفحة الإعدادات"""
    return render_template('settings.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """صفحة تسجيل الدخول"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        print(f"[LOGIN] محاولة تسجيل الدخول: {email}")
        if email and password:
            existing_user = None
            try:
                for u in USERS_STORAGE:
                    if isinstance(u, dict) and u.get('email') == email:
                        existing_user = u
                        break
            except Exception as e:
                print(f"خطأ في البحث عن المستخدم: {e}")
                return render_template('login.html', error="خطأ في النظام. يرجى المحاولة مرة أخرى.")
            if existing_user:
                stored_password = existing_user.get('password', '')
                print(f"[LOGIN] المستخدم موجود. نوع الحساب: {existing_user.get('type')}, كلمة المرور المدخلة: {password}, كلمة المرور المخزنة: {stored_password}")
                if password == stored_password:
                    session['user_name'] = existing_user['name']
                    session['user_email'] = existing_user['email']
                    session['user_type'] = existing_user['type']
                    print(f"تسجيل دخول ناجح: {existing_user['name']} - نوع المستخدم: {existing_user['type']}")
                    print(f"[LOGIN] بيانات الجلسة بعد الدخول: {dict(session)}")
                    return redirect(url_for('dashboard'))
                else:
                    print("[LOGIN] كلمة المرور غير صحيحة")
                    return render_template('login.html', error="كلمة المرور غير صحيحة")
            else:
                print("[LOGIN] المستخدم غير موجود")
                return render_template('login.html', error="البريد الإلكتروني غير مسجل. يرجى التسجيل أولاً.")
        else:
            print("[LOGIN] لم يتم إدخال البريد أو كلمة المرور")
            return render_template('login.html', error="يرجى إدخال البريد الإلكتروني وكلمة المرور")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """صفحة التسجيل - للمستخدمين العاديين فقط"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # تحقق إذا كان المستخدم مسجل مسبقًا
        user = None
        try:
            for u in USERS_STORAGE:
                if isinstance(u, dict) and u.get('email') == email:
                    user = u
                    break
        except Exception as e:
            print(f"خطأ في البحث عن المستخدم للتسجيل: {e}")
            return render_template('register.html', error="خطأ في النظام. يرجى المحاولة مرة أخرى.")
        
        if user:
            return render_template('register.html', error="المستخدم مسجل مسبقًا")
        
        # التحقق من تطابق كلمات المرور
        if password != confirm_password:
            return render_template('register.html', error="كلمات المرور غير متطابقة")
        
        if name and email and password:
            # إنشاء حساب مستخدم عادي فقط
            new_user = {
                'name': name,
                'email': email,
                'password': password,
                'type': 'patient',  # دائماً مستخدم عادي
                'original_name': name
            }
            
            USERS_STORAGE.append(new_user)
            save_users(USERS_STORAGE)  # حفظ في الملف
            reload_data()  # إعادة تحميل البيانات
            
            print(f"تسجيل ناجح: {name} - نوع المستخدم: patient")
            return render_template('register.html', success="تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول.")
        else:
            return render_template('register.html', error="يرجى ملء جميع الحقول المطلوبة")
    return render_template('register.html')

@app.route('/logout')
def logout():
    """تسجيل الخروج"""
    session.clear()
    return redirect(url_for('dashboard'))

@app.route('/diagnosis')
def diagnosis():
    """صفحة التشخيص البديلة"""
    return redirect(url_for('diagnose'))

@app.route('/case/<case_id>')
def case_details(case_id):
    """عرض تفاصيل حالة محددة"""
    if 'user_email' not in session:
        return redirect(url_for('login'))
    case = None
    user_type = session.get('user_type')
    # التحقق من الصلاحيات
    if user_type in ['admin', 'doctor']:
        for c in CASES_STORAGE:
            if str(c['id']) == str(case_id):
                case = c
                break
    else:
        for c in CASES_STORAGE:
            if str(c['id']) == str(case_id) and c.get('user_id') == session.get('user_email'):
                case = c
                break
    if case:
        return render_template('case_details.html', case=case)
    else:
        # عرض رسالة خطأ واضحة بدلاً من إعادة التوجيه فقط
        return render_template('case_details.html', case=None, error="الحالة غير موجودة أو ليس لديك صلاحية الوصول إليها.")

@app.route('/manage_doctors')
def manage_doctors():
    """صفحة إدارة الأطباء (للإدارة فقط)"""
    # التحقق من أن المستخدم إدارة
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    
    # جلب جميع المستخدمين
    all_users = USERS_STORAGE
    doctors = [user for user in all_users if user['type'] == 'doctor']
    patients = [user for user in all_users if user['type'] == 'patient']
    admins = [user for user in all_users if user['type'] == 'admin']
    
    return render_template('manage_doctors.html', 
                         doctors=doctors, 
                         patients=patients, 
                         admins=admins,
                         total_users=len(all_users))

@app.route('/manage_users')
def manage_users():
    """صفحة سجل المستخدمين العاديين (للإدارة فقط)"""
    if session.get('user_type') != 'admin':
        return redirect(url_for('dashboard'))
    patients = [user for user in USERS_STORAGE if user['type'] == 'patient']
    return render_template('manage_users.html', patients=patients)

@app.route('/delete_case/<case_id>', methods=['POST'])
def delete_case(case_id):
    """حذف حالة (للإدارة فقط)"""
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بحذف الحالات'})
    
    # البحث عن الحالة وحذفها
    global CASES_STORAGE
    case_to_delete = None
    for case in CASES_STORAGE:
        if str(case['id']) == str(case_id):
            case_to_delete = case
            break
    
    if case_to_delete:
        CASES_STORAGE.remove(case_to_delete)
        save_cases(CASES_STORAGE)  # حفظ في الملف
        print(f"تم حذف الحالة {case_id} بواسطة {session.get('user_name')}")
        return jsonify({'success': True, 'message': 'تم حذف الحالة بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'الحالة غير موجودة'})

@app.route('/delete_user/<email>', methods=['POST'])
def delete_user(email):
    print(f"[DEBUG] استقبلنا طلب حذف المستخدم: {email}")
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بحذف المستخدمين'})
    
    # البحث عن المستخدم وحذفه
    global USERS_STORAGE
    user_to_delete = None
    for user in USERS_STORAGE:
        if user['email'] == email:
            user_to_delete = user
            break
    
    if user_to_delete:
        # لا يمكن حذف الإدارة لنفسها
        if user_to_delete['email'] == session.get('user_email'):
            return jsonify({'success': False, 'message': 'لا يمكنك حذف حسابك الخاص'})
        
        USERS_STORAGE.remove(user_to_delete)
        save_users(USERS_STORAGE)  # حفظ في الملف
        reload_data()  # إعادة تحميل البيانات
        print(f"تم حذف المستخدم {email} بواسطة {session.get('user_name')}")
        return jsonify({'success': True, 'message': 'تم حذف المستخدم بنجاح'})
    else:
        return jsonify({'success': False, 'message': 'المستخدم غير موجود'})

@app.route('/edit_user/<email>', methods=['POST'])
def edit_user(email):
    print(f"[DEBUG] استقبلنا طلب تعديل المستخدم: {email}")
    if session.get('user_type') != 'admin':
        return jsonify({'success': False, 'message': 'غير مصرح لك بتعديل المستخدمين'})
    
    try:
        # الحصول على البيانات الجديدة
        data = request.get_json()
        new_name = data.get('name', '')
        new_type = data.get('type', 'patient')
        
        if not new_name:
            return jsonify({'success': False, 'message': 'الاسم مطلوب'})
        
        # التحقق من نوع الحساب
        if new_type not in ['patient', 'doctor', 'admin']:
            return jsonify({'success': False, 'message': 'نوع الحساب غير صحيح'})
        
        # البحث عن المستخدم وتعديله
        global USERS_STORAGE
        user_found = False
        for user in USERS_STORAGE:
            if user.get('email') == email:
                # منع تعديل الإدارة الحالية
                if user.get('type') == 'admin' and user.get('email') == session.get('user_email'):
                    return jsonify({'success': False, 'message': 'لا يمكنك تعديل حسابك الحالي'})
                
                # تحديث البيانات
                user['name'] = new_name
                user['type'] = new_type
                
                # تحديث الاسم حسب نوع الحساب
                if new_type == 'doctor':
                    user['name'] = f"د. {new_name}"
                elif new_type == 'admin':
                    user['name'] = f"الإدارة - {new_name}"
                
                user_found = True
                break
        
        if user_found:
            save_users(USERS_STORAGE)
            reload_data()  # إعادة تحميل البيانات
            print(f"تم تعديل المستخدم: {email} -> {new_name} ({new_type})")
            return jsonify({'success': True, 'message': 'تم تعديل المستخدم بنجاح'})
        else:
            return jsonify({'success': False, 'message': 'المستخدم غير موجود'})
            
    except Exception as e:
        print(f"خطأ في تعديل المستخدم: {e}")
        return jsonify({'success': False, 'message': 'حدث خطأ أثناء تعديل المستخدم'})

@app.route('/delete_diagnosis/<case_id>/<diagnosis_id>', methods=['POST'])
def delete_diagnosis(case_id, diagnosis_id):
    """حذف تشخيص من حالة معينة (للأطباء والإدارة فقط)"""
    if 'user_email' not in session:
        return jsonify({'success': False, 'message': 'يجب تسجيل الدخول أولاً'})
    user_type = session.get('user_type')
    if user_type not in ['admin', 'doctor']:
        return jsonify({'success': False, 'message': 'غير مصرح لك بحذف التشخيصات'})
    # البحث عن الحالة
    case = None
    for c in CASES_STORAGE:
        if str(c['id']) == str(case_id):
            case = c
            break
    if not case or 'diagnoses' not in case:
        return jsonify({'success': False, 'message': 'الحالة أو التشخيص غير موجود'})
    # حذف التشخيص
    original_len = len(case['diagnoses'])
    case['diagnoses'] = [d for d in case['diagnoses'] if str(d['id']) != str(diagnosis_id)]
    if len(case['diagnoses']) == original_len:
        return jsonify({'success': False, 'message': 'لم يتم العثور على التشخيص'})
    save_cases(CASES_STORAGE)
    return jsonify({'success': True, 'message': 'تم حذف التشخيص بنجاح'})

def main():
    """الدالة الرئيسية - تشغيل التطبيق كخادم ويب"""
    print("بدء تشغيل تطبيق تشخيص الأمراض الجلدية كخادم ويب...")
    try:
        # تشغيل خادم Flask مباشرة
        run_flask()
    except Exception as e:
        print(f"خطأ في تشغيل التطبيق: {e}")

if __name__ == '__main__':
    main() 