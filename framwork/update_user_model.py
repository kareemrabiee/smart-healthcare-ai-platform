import os
import sys
import sqlite3
from flask import Flask
from models import db, User

# إنشاء تطبيق Flask ليتم استخدامه للوصول إلى قاعدة البيانات
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def update_user_table():
    """تحديث جدول المستخدمين لإضافة الأعمدة الجديدة"""
    print("جاري تحديث جدول المستخدمين...")
    
    # اتصال مباشر بقاعدة البيانات SQLite
    try:
        conn = sqlite3.connect('healthcare.db')
        cursor = conn.cursor()
        
        # التحقق ما إذا كان العمود موجودًا بالفعل
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # إضافة عمود الاسم الكامل إذا لم يكن موجودًا
        if 'full_name' not in column_names:
            print("إضافة عمود full_name إلى جدول user...")
            cursor.execute("ALTER TABLE user ADD COLUMN full_name TEXT")
            print("تم إضافة عمود full_name بنجاح!")
        else:
            print("عمود full_name موجود بالفعل.")
        
        # إضافة عمود التخصص إذا لم يكن موجودًا
        if 'specialty' not in column_names:
            print("إضافة عمود specialty إلى جدول user...")
            cursor.execute("ALTER TABLE user ADD COLUMN specialty TEXT")
            print("تم إضافة عمود specialty بنجاح!")
        else:
            print("عمود specialty موجود بالفعل.")
        
        # حفظ التغييرات
        conn.commit()
        print("تم تحديث قاعدة البيانات بنجاح!")
        
        # تحديث بيانات الأطباء
        update_doctors_data(cursor, conn)
        
        # إغلاق الاتصال
        conn.close()
        
        return True
    except Exception as e:
        print(f"حدث خطأ أثناء تحديث قاعدة البيانات: {e}")
        return False

def update_doctors_data(cursor, conn):
    """تحديث بيانات الأطباء لإضافة الاسم الكامل والتخصص"""
    print("جاري تحديث بيانات الأطباء...")
    
    # قائمة ببيانات الأطباء
    doctors_data = [
        ('dr.mohamed', 'د. محمد أحمد', 'طب العيون'),
        ('dr.sara', 'د. سارة محمود', 'جراحة العيون'),
        ('dr.ahmed', 'د. أحمد خالد', 'شبكية العين'),
        ('dr.nora', 'د. نورا حسن', 'قرنية العين'),
        ('dr.omar', 'د. عمر فاروق', 'العدسات والنظارات'),
    ]
    
    for username, full_name, specialty in doctors_data:
        cursor.execute(
            "UPDATE user SET full_name = ?, specialty = ? WHERE username = ?",
            (full_name, specialty, username)
        )
    
    conn.commit()
    print("تم تحديث بيانات الأطباء بنجاح!")

if __name__ == "__main__":
    print("جاري تحديث نموذج المستخدم في قاعدة البيانات...")
    success = update_user_table()
    
    if success:
        print("تم تحديث نموذج المستخدم وبيانات الأطباء بنجاح!")
        print("الآن يمكن للتطبيق عرض أسماء الأطباء وتخصصاتهم بشكل صحيح.")
    else:
        print("حدث خطأ أثناء تحديث نموذج المستخدم. يرجى التحقق من سجلات الخطأ.") 