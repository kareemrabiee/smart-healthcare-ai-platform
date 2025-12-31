import os
import sys
from flask import Flask
from werkzeug.security import generate_password_hash
from models import db, User

# إنشاء تطبيق Flask ليتم استخدامه للوصول إلى قاعدة البيانات
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# قائمة الأطباء المراد إضافتهم
DOCTORS = [
    {
        'username': 'dr.mohamed',
        'email': 'dr.mohamed@eyeclinic.com',
        'password': 'doctor123',
        'full_name': 'د. محمد أحمد',
        'specialty': 'طب العيون'
    },
    {
        'username': 'dr.sara',
        'email': 'dr.sara@eyeclinic.com',
        'password': 'doctor123',
        'full_name': 'د. سارة محمود',
        'specialty': 'جراحة العيون'
    },
    {
        'username': 'dr.ahmed',
        'email': 'dr.ahmed@eyeclinic.com',
        'password': 'doctor123',
        'full_name': 'د. أحمد خالد',
        'specialty': 'شبكية العين'
    },
    {
        'username': 'dr.nora',
        'email': 'dr.nora@eyeclinic.com',
        'password': 'doctor123',
        'full_name': 'د. نورا حسن',
        'specialty': 'قرنية العين'
    },
    {
        'username': 'dr.omar',
        'email': 'dr.omar@eyeclinic.com',
        'password': 'doctor123',
        'full_name': 'د. عمر فاروق',
        'specialty': 'العدسات والنظارات'
    },
]

def create_doctors():
    """إنشاء حسابات الأطباء في قاعدة البيانات"""
    with app.app_context():
        print("جاري التحقق من قاعدة البيانات...")
        
        # إنشاء الجداول إذا لم تكن موجودة
        db.create_all()
        
        # إضافة خصائص إضافية للأطباء (إذا لم تكن موجودة بالفعل)
        try:
            # التحقق مما إذا كانت الأعمدة موجودة بالفعل
            user = User.query.first()
            if not hasattr(user, 'full_name'):
                print("جاري إضافة حقل الاسم الكامل للمستخدمين...")
                try:
                    db.engine.execute('ALTER TABLE user ADD COLUMN full_name VARCHAR(100)')
                except Exception as e:
                    print(f"خطأ في إضافة حقل الاسم الكامل: {e}")
            
            if not hasattr(user, 'specialty'):
                print("جاري إضافة حقل التخصص للمستخدمين...")
                try:
                    db.engine.execute('ALTER TABLE user ADD COLUMN specialty VARCHAR(100)')
                except Exception as e:
                    print(f"خطأ في إضافة حقل التخصص: {e}")
        except Exception as e:
            print(f"حدث خطأ أثناء فحص هيكل الجدول: {e}")
            # إذا لم يكن هناك مستخدمين بعد، فسنواصل المحاولة لإضافة الحقول عند إضافة المستخدمين
        
        # إضافة الأطباء
        doctors_count = 0
        
        for doctor_data in DOCTORS:
            # التحقق مما إذا كان الطبيب موجودًا بالفعل
            existing_doctor = User.query.filter_by(username=doctor_data['username']).first()
            
            if existing_doctor:
                print(f"الطبيب {doctor_data['username']} موجود بالفعل. جاري تحديث البيانات...")
                
                # تحديث بيانات الطبيب
                existing_doctor.email = doctor_data['email']
                
                # إضافة الخصائص الإضافية إذا أمكن
                try:
                    existing_doctor.full_name = doctor_data['full_name']
                    existing_doctor.specialty = doctor_data['specialty']
                except Exception as e:
                    print(f"تعذر تحديث الخصائص الإضافية: {e}")
                
                # تأكد من أن دور الطبيب هو 'admin'
                existing_doctor.role = 'admin'
                
                db.session.commit()
                print(f"تم تحديث بيانات الطبيب {doctor_data['username']} بنجاح.")
            else:
                print(f"جاري إنشاء حساب للطبيب {doctor_data['username']}...")
                
                # إنشاء حساب جديد للطبيب
                new_doctor = User(
                    username=doctor_data['username'],
                    email=doctor_data['email'],
                    password=generate_password_hash(doctor_data['password']),
                    role='admin'  # الأطباء يأخذون دور المشرف للوصول إلى الميزات الإدارية
                )
                
                # إضافة الخصائص الإضافية إذا أمكن
                try:
                    new_doctor.full_name = doctor_data['full_name']
                    new_doctor.specialty = doctor_data['specialty']
                except Exception as e:
                    print(f"تعذر إضافة الخصائص الإضافية: {e}")
                
                db.session.add(new_doctor)
                doctors_count += 1
        
        # حفظ التغييرات في قاعدة البيانات
        try:
            db.session.commit()
            print(f"تم إنشاء {doctors_count} حسابات جديدة للأطباء بنجاح.")
        except Exception as e:
            db.session.rollback()
            print(f"حدث خطأ أثناء حفظ البيانات: {e}")
            return False
        
        return True

if __name__ == "__main__":
    # تشغيل البرنامج
    print("جاري إنشاء حسابات الأطباء...")
    success = create_doctors()
    
    if success:
        print("تم إنشاء جميع حسابات الأطباء بنجاح!")
        print("يمكن للمستخدمين الآن التواصل مع الأطباء من خلال نظام الرسائل.")
        print("\nبيانات تسجيل الدخول للأطباء:")
        for doctor in DOCTORS:
            print(f"- اسم المستخدم: {doctor['username']}")
            print(f"  كلمة المرور: {doctor['password']}")
            print(f"  التخصص: {doctor['specialty']}")
            print()
    else:
        print("حدث خطأ أثناء إنشاء حسابات الأطباء. يرجى التحقق من سجلات الخطأ.") 