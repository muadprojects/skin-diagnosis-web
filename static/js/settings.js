// تطبيق الإعدادات على جميع صفحات التطبيق
class AppSettings {
    constructor() {
        this.settings = this.loadSettings();
        this.applySettings();
        this.setupEventListeners();
    }
    
    // تحميل الإعدادات من localStorage
    loadSettings() {
        const defaultSettings = {
            language: 'ar',
            theme: 'light',
            notifications: true,
            autoSave: true,
            twoFactor: false,
            sessionTimeout: false
        };
        
        const savedSettings = JSON.parse(localStorage.getItem('dermascan-settings') || '{}');
        return { ...defaultSettings, ...savedSettings };
    }
    
    // تطبيق الإعدادات
    applySettings() {
        this.applyLanguage();
        this.applyTheme();
        this.applyNotifications();
    }
    
    // تطبيق اللغة
    applyLanguage() {
        const language = this.settings.language;
        
        if (language === 'en') {
            document.documentElement.lang = 'en';
            document.documentElement.dir = 'ltr';
            // تأخير للتأكد من تحميل الصفحة بالكامل
            setTimeout(() => {
                this.changeLanguageToEnglish();
            }, 200);
        } else {
            document.documentElement.lang = 'ar';
            document.documentElement.dir = 'rtl';
            // تأخير للتأكد من تحميل الصفحة بالكامل
            setTimeout(() => {
                this.changeLanguageToArabic();
            }, 200);
        }
    }
    
    // تطبيق المظهر
    applyTheme() {
        const theme = this.settings.theme;
        
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
            document.documentElement.setAttribute('data-theme', 'dark');
        } else if (theme === 'auto') {
            if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                document.body.classList.add('dark-theme');
                document.documentElement.setAttribute('data-theme', 'dark');
            } else {
                document.body.classList.remove('dark-theme');
                document.documentElement.setAttribute('data-theme', 'light');
            }
        } else {
            document.body.classList.remove('dark-theme');
            document.documentElement.setAttribute('data-theme', 'light');
        }
    }
    
    // تطبيق الإشعارات
    applyNotifications() {
        if (this.settings.notifications && 'Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    // تغيير اللغة إلى الإنجليزية
    changeLanguageToEnglish() {
        console.log('تغيير اللغة إلى الإنجليزية');
        const translations = {
            // Navigation
            'الرئيسية': 'Home',
            'تشخيص جديد': 'New Diagnosis',
            'سجل الحالات': 'Cases Record',
            'الإحصائيات': 'Statistics',
            'الإعدادات': 'Settings',
            'تسجيل الخروج': 'Logout',
            'المستخدم': 'User',
            'طبيب': 'Doctor',
            'مستخدم': 'User',
            
            // Dashboard
            'مرحباً': 'Welcome',
            'د.': 'Dr.',
            'الطبيب': 'Doctor',
            'نحن هنا لمساعدتك في تشخيص الأمراض الجلدية بسهولة وأمان': 'We are here to help you diagnose skin diseases easily and safely',
            'نحن هنا لمساعدتك في تشخيص الأمراض الجلدية': 'We are here to help you diagnose skin diseases',
            'بدء التشخيص': 'Start Diagnosis',
            'عرض السجل': 'View Record',
            'عرض الإحصائيات': 'View Statistics',
            'آخر الحالات': 'Recent Cases',
            'لا توجد حالات حديثة': 'No recent cases',
            'إضافة حالة جديدة': 'Add New Case',
            'جميع البيانات محمية ومشفرة': 'All data is protected and encrypted',
            
            // Cases Page
            'البحث': 'Search',
            'ابحث في الحالات...': 'Search in cases...',
            'نوع المرض': 'Disease Type',
            'جميع الأمراض': 'All Diseases',
            'أكزيما': 'Eczema',
            'صدفية': 'Psoriasis',
            'حب الشباب': 'Acne',
            'التهاب الجلد التماسي': 'Contact Dermatitis',
            'الذئبة الحمامية': 'Lupus Erythematosus',
            'سرطان الجلد': 'Skin Cancer',
            'فطريات الجلد': 'Skin Fungus',
            'الحساسية الجلدية': 'Skin Allergy',
            'التاريخ': 'Date',
            'جميع التواريخ': 'All Dates',
            'اليوم': 'Today',
            'هذا الأسبوع': 'This Week',
            'هذا الشهر': 'This Month',
            'هذا العام': 'This Year',
            'مسح الفلاتر': 'Clear Filters',
            'صورة الحالة': 'Case Image',
            'عرض التفاصيل': 'View Details',
            'لا توجد حالات': 'No cases',
            'لم يتم تسجيل أي حالات بعد': 'No cases have been registered yet',
            'إحصائيات سريعة': 'Quick Statistics',
            'إجمالي الحالات': 'Total Cases',
            'أنواع الأمراض': 'Disease Types',
            'متوسط الثقة': 'Average Confidence',
            'حالات هذا العام': 'Cases This Year',
            'هل أنت متأكد من حذف هذه الحالة؟': 'Are you sure you want to delete this case?',
            'حذف الحالة': 'Delete Case',
            'تعديل الحالة': 'Edit Case',
            
            // Case Details
            'تفاصيل الحالة': 'Case Details',
            'العودة للسجل': 'Back to Record',
            'تعديل': 'Edit',
            'حذف': 'Delete',
            'تفاصيل التشخيص': 'Diagnosis Details',
            'المرض المشخص': 'Diagnosed Disease',
            'نسبة الثقة': 'Confidence Level',
            'وصف المرض': 'Disease Description',
            'تاريخ التشخيص': 'Diagnosis Date',
            'المريض': 'Patient',
            'ملاحظات الطبيب': 'Doctor Notes',
            'معلومات إضافية': 'Additional Information',
            'نوع الحساب': 'Account Type',
            'مستخدم عادي': 'Regular User',
            'مستوى الثقة': 'Confidence Level',
            'عالي جداً': 'Very High',
            'عالي': 'High',
            'متوسط': 'Medium',
            'منخفض': 'Low',
            'تنبيه مهم': 'Important Warning',
            'هذا التشخيص هو نتيجة تحليل آلي ولا يغني عن استشارة الطبيب المختص. يرجى مراجعة الطبيب للحصول على تشخيص دقيق وخطة علاج مناسبة.': 'This diagnosis is the result of automated analysis and does not replace consultation with a specialist doctor. Please consult a doctor for accurate diagnosis and appropriate treatment plan.',
            'ميزة التعديل قيد التطوير': 'Edit feature under development',
            'ميزة الحذف قيد التطوير': 'Delete feature under development',
            
            // Statistics Page
            'نظرة عامة على الحالات والأمراض المشخصة': 'Overview of cases and diagnosed diseases',
            'إحصائيات الحالات': 'Case Statistics',
            'توزيع الأمراض': 'Disease Distribution',
            'إحصائيات شهرية': 'Monthly Statistics',
            'إحصائيات سنوية': 'Annual Statistics',
            'أفضل التشخيصات': 'Top Diagnoses',
            'متوسط الثقة في التشخيص': 'Average Diagnosis Confidence',
            'إجمالي الحالات المشخصة': 'Total Diagnosed Cases',
            'حالات هذا الشهر': 'Cases This Month',
            'حالات هذا الأسبوع': 'Cases This Week',
            'حالات اليوم': 'Today\'s Cases',
            'أعلى نسبة ثقة': 'Highest Confidence',
            'أدنى نسبة ثقة': 'Lowest Confidence',
            'متوسط نسبة الثقة': 'Average Confidence Level',
            'عدد الحالات': 'Number of Cases',
            'نسبة الثقة': 'Confidence Percentage',
            'التاريخ': 'Date',
            'المرض': 'Disease',
            'النسبة': 'Percentage',
            'العدد': 'Count',
            'الشهر': 'Month',
            'السنة': 'Year',
            'الربع': 'Quarter',
            'الربع الأول': 'Q1',
            'الربع الثاني': 'Q2',
            'الربع الثالث': 'Q3',
            'الربع الرابع': 'Q4',
            'يناير': 'January',
            'فبراير': 'February',
            'مارس': 'March',
            'أبريل': 'April',
            'مايو': 'May',
            'يونيو': 'June',
            'يوليو': 'July',
            'أغسطس': 'August',
            'سبتمبر': 'September',
            'أكتوبر': 'October',
            'نوفمبر': 'November',
            'ديسمبر': 'December',
            
            // About Page
            'حول التطبيق': 'About App',
            'تطبيق تشخيص الأمراض الجلدية بالذكاء الاصطناعي': 'AI-powered skin disease diagnosis application',
            'الإصدار': 'Version',
            'معلومات التطبيق': 'App Information',
            'الوصف': 'Description',
            'DermaScan هو تطبيق متطور لتشخيص الأمراض الجلدية باستخدام تقنيات الذكاء الاصطناعي. يوفر التشخيص السريع والدقيق مع واجهة سهلة الاستخدام.': 'DermaScan is an advanced application for diagnosing skin diseases using artificial intelligence technologies. It provides fast and accurate diagnosis with an easy-to-use interface.',
            'المميزات الرئيسية': 'Main Features',
            'تشخيص سريع ودقيق للأمراض الجلدية': 'Fast and accurate diagnosis of skin diseases',
            'واجهة سهلة الاستخدام باللغة العربية': 'Easy-to-use interface in Arabic',
            'حفظ وتتبع الحالات الطبية': 'Save and track medical cases',
            'إحصائيات مفصلة للأطباء': 'Detailed statistics for doctors',
            'أمان عالي وحماية البيانات': 'High security and data protection',
            'التقنيات المستخدمة': 'Technologies Used',
            'فريق التطوير': 'Development Team',
            'المطور الرئيسي': 'Lead Developer',
            'فريق DermaScan': 'DermaScan Team',
            'تطوير وتصميم التطبيق': 'App development and design',
            'المستشارون الطبيون': 'Medical Consultants',
            'أطباء الجلدية المتخصصون': 'Specialized Dermatologists',
            'مراجعة وتطوير النماذج الطبية': 'Review and development of medical models',
            'فريق الجودة': 'Quality Team',
            'فريق اختبار الجودة': 'Quality Testing Team',
            'اختبار وضمان جودة التطبيق': 'Testing and ensuring app quality',
            'الدعم والاتصال': 'Support & Contact',
            'البريد الإلكتروني': 'Email',
            'الهاتف': 'Phone',
            'الموقع الإلكتروني': 'Website',
            'المراجع العلمية': 'Scientific References',
            'المصادر الطبية': 'Medical Sources',
            'المصادر التقنية': 'Technical Sources',
            'المعلومات القانونية': 'Legal Information',
            'شروط الاستخدام': 'Terms of Use',
            'هذا التطبيق مخصص للأغراض التعليمية والبحثية فقط. لا يغني عن استشارة الطبيب المختص.': 'This application is intended for educational and research purposes only. It does not replace consultation with a specialist doctor.',
            'سياسة الخصوصية': 'Privacy Policy',
            'نحن نحمي خصوصية المستخدمين ولا نشارك البيانات الشخصية مع أي طرف ثالث.': 'We protect user privacy and do not share personal data with any third party.',
            'جميع الحقوق محفوظة': 'All rights reserved',
            
            // Login/Register
            'تسجيل الدخول': 'Login',
            'أدخل بياناتك للوصول إلى حسابك': 'Enter your data to access your account',
            'البريد الإلكتروني': 'Email',
            'أدخل بريدك الإلكتروني': 'Enter your email',
            'كلمة المرور': 'Password',
            'أدخل كلمة المرور': 'Enter your password',
            'ليس لديك حساب؟': 'Don\'t have an account?',
            'إنشاء حساب جديد': 'Create new account',
            'إنشاء حساب': 'Create Account',
            'أدخل بياناتك لإنشاء حسابك': 'Enter your data to create your account',
            'الاسم الكامل': 'Full Name',
            'أدخل اسمك الكامل': 'Enter your full name',
            'تأكيد كلمة المرور': 'Confirm Password',
            'أعد إدخال كلمة المرور': 'Re-enter your password',
            'نوع الحساب': 'Account Type',
            'اختر نوع الحساب': 'Choose account type',
            'مستخدم عادي': 'Regular User',
            'رمز الطبيب': 'Doctor Code',
            'أدخل رمز الطبيب': 'Enter doctor code',
            'رمز الطبيب مطلوب للتحقق من هويتك كطبيب': 'Doctor code is required to verify your identity as a doctor',
            'إنشاء الحساب': 'Create Account',
            'لديك حساب بالفعل؟': 'Already have an account?',
            
            // Additional diagnosis page translations
            'طباعة التقرير': 'Print Report',
            'تحميل تقرير PDF': 'Download PDF Report',
            'المحاولة مرة أخرى': 'Try Again',
            'خطأ في التشخيص': 'Diagnosis Error',
            'نسبة الثقة': 'Confidence Level',
            'معلومات المرض': 'Disease Information',
            'الوصف': 'Description',
            'الخطورة': 'Severity',
            'التوصية': 'Recommendation',
            'المرض المشخص': 'Diagnosed Disease',
            'نسبة الثقة في التشخيص': 'Diagnosis Confidence Level',
            'احتمالية الإصابة': 'Infection Probability',
            'معلومات إضافية': 'Additional Information',
            'Data exported successfully': 'تم تصدير البيانات بنجاح'
        };
        
        this.translatePage(translations);
    }
    
    // تغيير اللغة إلى العربية
    changeLanguageToArabic() {
        console.log('تغيير اللغة إلى العربية');
        const translations = {
            // Navigation
            'Home': 'الرئيسية',
            'New Diagnosis': 'تشخيص جديد',
            'Cases Record': 'سجل الحالات',
            'Statistics': 'الإحصائيات',
            'Settings': 'الإعدادات',
            'Logout': 'تسجيل الخروج',
            'User': 'المستخدم',
            'Doctor': 'طبيب',
            
            // Dashboard
            'Welcome': 'مرحباً',
            'Dr.': 'د.',
            'We are here to help you diagnose skin diseases easily and safely': 'نحن هنا لمساعدتك في تشخيص الأمراض الجلدية بسهولة وأمان',
            'We are here to help you diagnose skin diseases': 'نحن هنا لمساعدتك في تشخيص الأمراض الجلدية',
            'Start Diagnosis': 'بدء التشخيص',
            'View Record': 'عرض السجل',
            'View Statistics': 'عرض الإحصائيات',
            'Recent Cases': 'آخر الحالات',
            'No recent cases': 'لا توجد حالات حديثة',
            'Add New Case': 'إضافة حالة جديدة',
            'All data is protected and encrypted': 'جميع البيانات محمية ومشفرة',
            
            // Cases Page
            'Search': 'البحث',
            'Search in cases...': 'ابحث في الحالات...',
            'Disease Type': 'نوع المرض',
            'All Diseases': 'جميع الأمراض',
            'Eczema': 'أكزيما',
            'Psoriasis': 'صدفية',
            'Acne': 'حب الشباب',
            'Contact Dermatitis': 'التهاب الجلد التماسي',
            'Lupus Erythematosus': 'الذئبة الحمامية',
            'Skin Cancer': 'سرطان الجلد',
            'Skin Fungus': 'فطريات الجلد',
            'Skin Allergy': 'الحساسية الجلدية',
            'Date': 'التاريخ',
            'All Dates': 'جميع التواريخ',
            'Today': 'اليوم',
            'This Week': 'هذا الأسبوع',
            'This Month': 'هذا الشهر',
            'This Year': 'هذا العام',
            'Clear Filters': 'مسح الفلاتر',
            'Case Image': 'صورة الحالة',
            'View Details': 'عرض التفاصيل',
            'No cases': 'لا توجد حالات',
            'No cases have been registered yet': 'لم يتم تسجيل أي حالات بعد',
            'Quick Statistics': 'إحصائيات سريعة',
            'Total Cases': 'إجمالي الحالات',
            'Disease Types': 'أنواع الأمراض',
            'Average Confidence': 'متوسط الثقة',
            'Cases This Year': 'حالات هذا العام',
            'Are you sure you want to delete this case?': 'هل أنت متأكد من حذف هذه الحالة؟',
            'Delete Case': 'حذف الحالة',
            'Edit Case': 'تعديل الحالة',
            
            // Case Details
            'Case Details': 'تفاصيل الحالة',
            'Back to Record': 'العودة للسجل',
            'Edit': 'تعديل',
            'Delete': 'حذف',
            'Diagnosis Details': 'تفاصيل التشخيص',
            'Diagnosed Disease': 'المرض المشخص',
            'Confidence Level': 'نسبة الثقة',
            'Disease Description': 'وصف المرض',
            'Diagnosis Date': 'تاريخ التشخيص',
            'Patient': 'المريض',
            'Doctor Notes': 'ملاحظات الطبيب',
            'Additional Information': 'معلومات إضافية',
            'Account Type': 'نوع الحساب',
            'Regular User': 'مستخدم عادي',
            'Very High': 'عالي جداً',
            'High': 'عالي',
            'Medium': 'متوسط',
            'Low': 'منخفض',
            'Important Warning': 'تنبيه مهم',
            'This diagnosis is the result of automated analysis and does not replace consultation with a specialist doctor. Please consult a doctor for accurate diagnosis and appropriate treatment plan.': 'هذا التشخيص هو نتيجة تحليل آلي ولا يغني عن استشارة الطبيب المختص. يرجى مراجعة الطبيب للحصول على تشخيص دقيق وخطة علاج مناسبة.',
            'Edit feature under development': 'ميزة التعديل قيد التطوير',
            'Delete feature under development': 'ميزة الحذف قيد التطوير',
            
            // Statistics Page
            'Overview of cases and diagnosed diseases': 'نظرة عامة على الحالات والأمراض المشخصة',
            'Case Statistics': 'إحصائيات الحالات',
            'Disease Distribution': 'توزيع الأمراض',
            'Monthly Statistics': 'إحصائيات شهرية',
            'Annual Statistics': 'إحصائيات سنوية',
            'Top Diagnoses': 'أفضل التشخيصات',
            'Average Diagnosis Confidence': 'متوسط الثقة في التشخيص',
            'Total Diagnosed Cases': 'إجمالي الحالات المشخصة',
            'Cases This Month': 'حالات هذا الشهر',
            'Cases This Week': 'حالات هذا الأسبوع',
            'Today\'s Cases': 'حالات اليوم',
            'Highest Confidence': 'أعلى نسبة ثقة',
            'Lowest Confidence': 'أدنى نسبة ثقة',
            'Average Confidence Level': 'متوسط نسبة الثقة',
            'Number of Cases': 'عدد الحالات',
            'Confidence Percentage': 'نسبة الثقة',
            'Date': 'التاريخ',
            'Disease': 'المرض',
            'Percentage': 'النسبة',
            'Count': 'العدد',
            'Month': 'الشهر',
            'Year': 'السنة',
            'Quarter': 'الربع',
            'Q1': 'الربع الأول',
            'Q2': 'الربع الثاني',
            'Q3': 'الربع الثالث',
            'Q4': 'الربع الرابع',
            'January': 'يناير',
            'February': 'فبراير',
            'March': 'مارس',
            'April': 'أبريل',
            'May': 'مايو',
            'June': 'يونيو',
            'July': 'يوليو',
            'August': 'أغسطس',
            'September': 'سبتمبر',
            'October': 'أكتوبر',
            'November': 'نوفمبر',
            'December': 'ديسمبر',
            
            // About Page
            'About App': 'حول التطبيق',
            'AI-powered skin disease diagnosis application': 'تطبيق تشخيص الأمراض الجلدية بالذكاء الاصطناعي',
            'Version': 'الإصدار',
            'App Information': 'معلومات التطبيق',
            'Description': 'الوصف',
            'DermaScan is an advanced application for diagnosing skin diseases using artificial intelligence technologies. It provides fast and accurate diagnosis with an easy-to-use interface.': 'DermaScan هو تطبيق متطور لتشخيص الأمراض الجلدية باستخدام تقنيات الذكاء الاصطناعي. يوفر التشخيص السريع والدقيق مع واجهة سهلة الاستخدام.',
            'Main Features': 'المميزات الرئيسية',
            'Fast and accurate diagnosis of skin diseases': 'تشخيص سريع ودقيق للأمراض الجلدية',
            'Easy-to-use interface in Arabic': 'واجهة سهلة الاستخدام باللغة العربية',
            'Save and track medical cases': 'حفظ وتتبع الحالات الطبية',
            'Detailed statistics for doctors': 'إحصائيات مفصلة للأطباء',
            'High security and data protection': 'أمان عالي وحماية البيانات',
            'Technologies Used': 'التقنيات المستخدمة',
            'Development Team': 'فريق التطوير',
            'Lead Developer': 'المطور الرئيسي',
            'DermaScan Team': 'فريق DermaScan',
            'App development and design': 'تطوير وتصميم التطبيق',
            'Medical Consultants': 'المستشارون الطبيون',
            'Specialized Dermatologists': 'أطباء الجلدية المتخصصون',
            'Review and development of medical models': 'مراجعة وتطوير النماذج الطبية',
            'Quality Team': 'فريق الجودة',
            'Quality Testing Team': 'فريق اختبار الجودة',
            'Testing and ensuring app quality': 'اختبار وضمان جودة التطبيق',
            'Support & Contact': 'الدعم والاتصال',
            'Email': 'البريد الإلكتروني',
            'Phone': 'الهاتف',
            'Website': 'الموقع الإلكتروني',
            'Scientific References': 'المراجع العلمية',
            'Medical Sources': 'المصادر الطبية',
            'Technical Sources': 'المصادر التقنية',
            'Legal Information': 'المعلومات القانونية',
            'Terms of Use': 'شروط الاستخدام',
            'This application is intended for educational and research purposes only. It does not replace consultation with a specialist doctor.': 'هذا التطبيق مخصص للأغراض التعليمية والبحثية فقط. لا يغني عن استشارة الطبيب المختص.',
            'Privacy Policy': 'سياسة الخصوصية',
            'We protect user privacy and do not share personal data with any third party.': 'نحن نحمي خصوصية المستخدمين ولا نشارك البيانات الشخصية مع أي طرف ثالث.',
            'All rights reserved': 'جميع الحقوق محفوظة',
            
            // Login/Register
            'Login': 'تسجيل الدخول',
            'Enter your data to access your account': 'أدخل بياناتك للوصول إلى حسابك',
            'Enter your email': 'أدخل بريدك الإلكتروني',
            'Password': 'كلمة المرور',
            'Enter your password': 'أدخل كلمة المرور',
            'Don\'t have an account?': 'ليس لديك حساب؟',
            'Create new account': 'إنشاء حساب جديد',
            'Create Account': 'إنشاء حساب',
            'Enter your data to create your account': 'أدخل بياناتك لإنشاء حسابك',
            'Full Name': 'الاسم الكامل',
            'Enter your full name': 'أدخل اسمك الكامل',
            'Confirm Password': 'تأكيد كلمة المرور',
            'Re-enter your password': 'أعد إدخال كلمة المرور',
            'Account Type': 'نوع الحساب',
            'Choose account type': 'اختر نوع الحساب',
            'Regular User': 'مستخدم عادي',
            'Doctor Code': 'رمز الطبيب',
            'Enter doctor code': 'أدخل رمز الطبيب',
            'Doctor code is required to verify your identity as a doctor': 'رمز الطبيب مطلوب للتحقق من هويتك كطبيب',
            'Create Account': 'إنشاء الحساب',
            'Already have an account?': 'لديك حساب بالفعل؟',
            
            // Additional diagnosis page translations
            'Print Report': 'طباعة التقرير',
            'Download PDF Report': 'تحميل تقرير PDF',
            'Try Again': 'المحاولة مرة أخرى',
            'Diagnosis Error': 'خطأ في التشخيص',
            'Disease Information': 'معلومات المرض',
            'Severity': 'الخطورة',
            'Recommendation': 'التوصية',
            'Diagnosis Confidence Level': 'نسبة الثقة في التشخيص',
            'Infection Probability': 'احتمالية الإصابة',
            'Data exported successfully': 'تم تصدير البيانات بنجاح'
        };
        
        this.translatePage(translations);
    }
    
    // ترجمة الصفحة
    translatePage(translations) {
        console.log('بدء الترجمة...', translations);
        
        // تأخير للتأكد من تحميل الصفحة بالكامل
        setTimeout(() => {
            // دالة محسنة للترجمة
            function translateElement(element) {
                // ترجمة النص المباشر
                if (element.childNodes.length === 1 && element.childNodes[0].nodeType === 3) {
                    const text = element.textContent.trim();
                    if (text && translations[text]) {
                        element.textContent = translations[text];
                        return;
                    }
                }
                
                // ترجمة innerHTML للعناصر التي تحتوي على HTML
                const originalHTML = element.innerHTML;
                let newHTML = originalHTML;
                
                // البحث عن النصوص العربية في المحتوى
                for (const [arabic, english] of Object.entries(translations)) {
                    if (originalHTML.includes(arabic)) {
                        newHTML = newHTML.replace(new RegExp(arabic, 'g'), english);
                    }
                }
                
                if (newHTML !== originalHTML) {
                    element.innerHTML = newHTML;
                }
                
                // ترجمة الخصائص
                const attributes = ['placeholder', 'title', 'alt', 'aria-label', 'data-original-title'];
                attributes.forEach(attr => {
                    if (element.hasAttribute(attr)) {
                        const value = element.getAttribute(attr);
                        if (value && translations[value]) {
                            element.setAttribute(attr, translations[value]);
                        }
                    }
                });
            }
            
            // تطبيق الترجمة على جميع العناصر المهمة
            const selectors = [
                'a', 'button', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 
                'p', 'label', 'li', 'td', 'th', 'option', 'select', '.form-text', 
                '.form-label', '.alert', '.card-title', '.card-text', '.navbar-brand', 
                '.nav-link', '.dropdown-item', '.dropdown-toggle', '.btn', '.btn-close',
                '.text-muted', '.text-primary', '.lead', '.display-4', '.navbar-nav',
                '.navbar-nav .nav-link', '.dropdown-menu', '.dropdown-menu .dropdown-item',
                '.card-body', '.card-header', '.modal-title', '.modal-body', '.modal-footer',
                '.table', '.table th', '.table td', '.badge', '.alert-heading',
                '.form-control', '.form-select', '.input-group-text', '.btn-group',
                '.btn-group .btn', '.nav-tabs', '.nav-tabs .nav-link', '.tab-content',
                '.tab-pane', '.accordion', '.accordion-item', '.accordion-header',
                '.accordion-body', '.list-group', '.list-group-item', '.breadcrumb',
                '.breadcrumb-item', '.pagination', '.page-link', '.page-item',
                '.progress', '.progress-bar', '.spinner-border', '.spinner-grow',
                '.toast', '.toast-header', '.toast-body', '.tooltip', '.popover',
                '.popover-header', '.popover-body', '.carousel', '.carousel-item',
                '.carousel-caption', '.jumbotron', '.media', '.media-body'
            ];
            
            selectors.forEach(selector => {
                document.querySelectorAll(selector).forEach(element => {
                    translateElement(element);
                });
            });
            
            // ترجمة إضافية للنصوص التي قد تحتوي على مسافات إضافية
            document.querySelectorAll('*').forEach(element => {
                if (element.childNodes.length === 1 && element.childNodes[0].nodeType === 3) {
                    const text = element.textContent.trim();
                    if (text) {
                        // البحث عن النص في الترجمات حتى لو كان جزءاً من نص أطول
                        for (const [arabic, english] of Object.entries(translations)) {
                            if (text === arabic || text.includes(arabic)) {
                                element.textContent = element.textContent.replace(arabic, english);
                                break;
                            }
                        }
                    }
                }
            });
            
            // ترجمة إضافية للخصائص
            document.querySelectorAll('input[placeholder], textarea[placeholder]').forEach(element => {
                const placeholder = element.getAttribute('placeholder');
                if (placeholder && translations[placeholder]) {
                    element.setAttribute('placeholder', translations[placeholder]);
                }
            });
            
            document.querySelectorAll('[title]').forEach(element => {
                const title = element.getAttribute('title');
                if (title && translations[title]) {
                    element.setAttribute('title', translations[title]);
                }
            });
            
            document.querySelectorAll('img[alt]').forEach(element => {
                const alt = element.getAttribute('alt');
                if (alt && translations[alt]) {
                    element.setAttribute('alt', translations[alt]);
                }
            });
            
            document.querySelectorAll('[aria-label]').forEach(element => {
                const ariaLabel = element.getAttribute('aria-label');
                if (ariaLabel && translations[ariaLabel]) {
                    element.setAttribute('aria-label', translations[ariaLabel]);
                }
            });
            
            console.log('تم الانتهاء من الترجمة');
        }, 100); // تأخير 100 مللي ثانية
    }
    
    // إعداد مستمعي الأحداث
    setupEventListeners() {
        // مراقبة تغيير الوضع المظلم في النظام
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addListener(() => {
                if (this.settings.theme === 'auto') {
                    this.applyTheme();
                }
            });
        }
    }
    
    // حفظ الإعدادات
    saveSettings(newSettings) {
        this.settings = { ...this.settings, ...newSettings };
        localStorage.setItem('dermascan-settings', JSON.stringify(this.settings));
        this.applySettings();
    }
    
    // إرسال إشعار
    sendNotification(title, body) {
        if (this.settings.notifications && 'Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body: body });
        }
    }
}

// تطبيق الإعدادات عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    window.appSettings = new AppSettings();
});

// تصدير الكلاس للاستخدام في ملفات أخرى
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AppSettings;
} 