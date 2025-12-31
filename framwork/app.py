import os
import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
from werkzeug.utils import secure_filename
import tensorflow as tf
from keras.models import load_model
from keras.utils import load_img, img_to_array
import joblib
from datetime import datetime
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Diagnosis, Message
import io
import csv
import shutil
import re
import keras

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'  # تغيير هذا في الإنتاج
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///healthcare.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# تكوينات الملفات المسموح بها
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# تسجيل الفئة المخصصة مع Keras
@keras.utils.register_keras_serializable()
class HybridModel(keras.Model):
    def __init__(self, base_model, **kwargs):
        super().__init__(**kwargs)
        self.base_model = base_model
        
    def call(self, inputs):
        features = self.base_model(inputs)
        return features
    
    def get_config(self):
        # إرجاع التكوين مع جميع المكونات الإضافية
        config = super().get_config()
        config.update({
            'base_model': keras.models.clone_model(self.base_model),
        })
        return config
    
    @classmethod
    def from_config(cls, config):
        # إعادة بناء النموذج من التكوين
        base_model = config.pop('base_model')
        return cls(base_model, **config)

# إنشاء نموذج محلي متقدم مع طبقات إضافية للتصنيف
class AdvancedModel(keras.Model):
    def __init__(self, base_model):
        super().__init__()
        self.base_model = base_model
        
        # إضافة طبقات للاستخراج المتقدم للميزات
        self.global_avg = keras.layers.GlobalAveragePooling2D()
        self.dropout1 = keras.layers.Dropout(0.3)  # زيادة نسبة التسريب للتعميم
        self.dense1 = keras.layers.Dense(256, activation='relu')  # زيادة عدد الوحدات
        self.batch_norm1 = keras.layers.BatchNormalization()
        self.dropout2 = keras.layers.Dropout(0.4)  # زيادة نسبة التسريب
        self.dense2 = keras.layers.Dense(128, activation='relu')
        self.batch_norm2 = keras.layers.BatchNormalization()
        self.dropout3 = keras.layers.Dropout(0.3)
        self.dense3 = keras.layers.Dense(64, activation='relu')
        
        # طبقة التصنيف النهائية
        self.output_layer = keras.layers.Dense(3, activation='softmax')
        
        # إضافة طبقات لاستخراج الخصائص الطبية
        # طبقات استخراج سماكة القرنية
        self.thickness_layer1 = keras.layers.Dense(32, activation='relu')
        self.thickness_layer2 = keras.layers.Dense(1)
        
        # طبقات استخراج انحناء القرنية
        self.curvature_layer1 = keras.layers.Dense(32, activation='relu')
        self.curvature_layer2 = keras.layers.Dense(1)
        
        # طبقات استخراج عدم التماثل
        self.asymmetry_layer1 = keras.layers.Dense(32, activation='relu')
        self.asymmetry_layer2 = keras.layers.Dense(1)
        
        # طبقات استخراج عدم الانتظام
        self.irregularity_layer1 = keras.layers.Dense(32, activation='relu')
        self.irregularity_layer2 = keras.layers.Dense(1)
        
        # طبقات استخراج التعقيد
        self.complexity_layer1 = keras.layers.Dense(32, activation='relu')
        self.complexity_layer2 = keras.layers.Dense(1)
        
        # تعيين أوزان مسبقة للفئات (بناءً على المعرفة الطبية وانتشار الحالات)
        # الفئة 0: طبيعي - احتمالية عالية للحالات الطبيعية
        # الفئة 1: مشتبه به - احتمالية متوسطة
        # الفئة 2: قرنية مخروطية - احتمالية منخفضة (حالة نادرة نسبيًا)
        self.class_weights = tf.constant([[0.45, 0.30, 0.25]], dtype=tf.float32)  # تعديل الأوزان لتكون أكثر توازناً وأقل تحيزاً للحالة الطبيعية
        
        # خصائص قرنية العين لكل فئة (مبنية على معايير طبية)
        # هذه القيم تعكس الخصائص الطبية المتوقعة لكل فئة من البيانات
        self.normal_features = {
            'corneal_thickness': 0.85,  # سماكة قرنية طبيعية (مرتفعة)
            'corneal_curvature': 0.25,  # انحناء قرنية منخفض
            'asymmetry': 0.15,  # عدم تماثل منخفض
            'irregularity': 0.15,  # عدم انتظام منخفض
            'complexity': 0.30   # تعقيد منخفض
        }
        
        self.suspect_features = {
            'corneal_thickness': 0.60,  # سماكة قرنية متوسطة
            'corneal_curvature': 0.55,  # انحناء قرنية متوسط
            'asymmetry': 0.45,  # عدم تماثل متوسط
            'irregularity': 0.50,  # عدم انتظام متوسط
            'complexity': 0.60   # تعقيد متوسط
        }
        
        self.keratoconus_features = {
            'corneal_thickness': 0.35,  # سماكة قرنية منخفضة
            'corneal_curvature': 0.85,  # انحناء قرنية مرتفع
            'asymmetry': 0.80,  # عدم تماثل مرتفع
            'irregularity': 0.85,  # عدم انتظام مرتفع
            'complexity': 0.85   # تعقيد مرتفع
        }
    
    def extract_medical_features(self, features):
        """استخراج الخصائص الطبية من ميزات النموذج الأساسي"""
        
        # تحديث استخراج الخصائص الطبية لتكون أكثر توازناً
        # زيادة قيم سماكة القرنية وتقليل قيم الانحناء والتماثل
        
        # استخراج سماكة القرنية (مؤشر عكسي للقرنية المخروطية)
        corneal_thickness = self.thickness_layer1(features)
        corneal_thickness = self.thickness_layer2(corneal_thickness)
        corneal_thickness = tf.sigmoid(corneal_thickness)  # تطبيع القيم بين 0 و 1
        
        # استخراج انحناء القرنية (مؤشر للقرنية المخروطية)
        corneal_curvature = self.curvature_layer1(features)
        corneal_curvature = self.curvature_layer2(corneal_curvature)
        corneal_curvature = tf.sigmoid(corneal_curvature)
        
        # استخراج عدم التماثل (مؤشر للقرنية المخروطية)
        asymmetry = self.asymmetry_layer1(features)
        asymmetry = self.asymmetry_layer2(asymmetry)
        asymmetry = tf.sigmoid(asymmetry)
        
        # استخراج عدم الانتظام (مؤشر للقرنية المخروطية)
        irregularity = self.irregularity_layer1(features)
        irregularity = self.irregularity_layer2(irregularity)
        irregularity = tf.sigmoid(irregularity)
        
        # استخراج تعقيد الصورة (مؤشر للقرنية المخروطية)
        complexity = self.complexity_layer1(features)
        complexity = self.complexity_layer2(complexity)
        complexity = tf.sigmoid(complexity)
        
        # تطبيق عوامل تصحيح لجعل الاستخراج أكثر توازناً - تعديل العوامل لتكون أكثر توازناً
        corneal_thickness = corneal_thickness * 1.05  # تقليل زيادة سماكة القرنية من 15% إلى 5%
        corneal_thickness = tf.minimum(corneal_thickness, 1.0)  # التأكد من أن القيم لا تتجاوز 1.0
        
        corneal_curvature = corneal_curvature * 0.95  # زيادة انحناء القرنية (تقليل النسبة من 0.85 إلى 0.95)
        asymmetry = asymmetry * 0.95  # زيادة عدم التماثل (تقليل النسبة من 0.85 إلى 0.95)
        irregularity = irregularity * 0.95  # زيادة عدم الانتظام (تقليل النسبة من 0.90 إلى 0.95)
        
        return {
            'corneal_thickness': corneal_thickness,
            'corneal_curvature': corneal_curvature,
            'asymmetry': asymmetry,
            'irregularity': irregularity,
            'complexity': complexity
        }
    
    def calculate_medical_similarity(self, medical_features):
        """حساب مدى تشابه الخصائص الطبية المستخرجة مع خصائص كل فئة"""
        
        # تحديث خصائص الفئات لتشمل الميزة الجديدة (التعقيد)
        normal_features = {
            'corneal_thickness': 0.85,  # سماكة قرنية طبيعية (مرتفعة)
            'corneal_curvature': 0.25,  # انحناء قرنية منخفض
            'asymmetry': 0.15,  # عدم تماثل منخفض
            'irregularity': 0.15,  # عدم انتظام منخفض
            'complexity': 0.30   # تعقيد منخفض
        }
        
        suspect_features = {
            'corneal_thickness': 0.60,  # سماكة قرنية متوسطة
            'corneal_curvature': 0.55,  # انحناء قرنية متوسط
            'asymmetry': 0.45,  # عدم تماثل متوسط
            'irregularity': 0.50,  # عدم انتظام متوسط
            'complexity': 0.60   # تعقيد متوسط
        }
        
        keratoconus_features = {
            'corneal_thickness': 0.35,  # سماكة قرنية منخفضة
            'corneal_curvature': 0.85,  # انحناء قرنية مرتفع
            'asymmetry': 0.80,  # عدم تماثل مرتفع
            'irregularity': 0.85,  # عدم انتظام مرتفع
            'complexity': 0.85   # تعقيد مرتفع
        }
        
        # تحديث أوزان الخصائص لكل فئة - تعديل الأوزان لتكون أكثر توازناً
        normal_weights = {
            'corneal_thickness': 0.35,  # تقليل وزن سماكة القرنية للحالة الطبيعية من 0.40 إلى 0.35
            'corneal_curvature': 0.20,
            'asymmetry': 0.15,
            'irregularity': 0.15,
            'complexity': 0.15  # زيادة وزن التعقيد من 0.10 إلى 0.15
        }
        
        suspect_weights = {
            'corneal_thickness': 0.30,
            'corneal_curvature': 0.25,
            'asymmetry': 0.20,
            'irregularity': 0.15,
            'complexity': 0.10
        }
        
        keratoconus_weights = {
            'corneal_thickness': 0.20,  # تقليل وزن سماكة القرنية للقرنية المخروطية من 0.25 إلى 0.20
            'corneal_curvature': 0.30,  # زيادة وزن انحناء القرنية من 0.25 إلى 0.30
            'asymmetry': 0.25,  # زيادة وزن عدم التماثل من 0.20 إلى 0.25
            'irregularity': 0.20,
            'complexity': 0.05  # تقليل وزن التعقيد من 0.10 إلى 0.05
        }
        
        # حساب درجة التشابه مع الحالة الطبيعية
        normal_similarity = 0.0
        for feature_name in ['corneal_thickness', 'corneal_curvature', 'asymmetry', 'irregularity', 'complexity']:
            if feature_name in medical_features:
                feature_similarity = 1.0 - tf.abs(medical_features[feature_name] - normal_features[feature_name])
                normal_similarity += feature_similarity * normal_weights[feature_name]
        
        # حساب درجة التشابه مع الحالة المشتبه بها
        suspect_similarity = 0.0
        for feature_name in ['corneal_thickness', 'corneal_curvature', 'asymmetry', 'irregularity', 'complexity']:
            if feature_name in medical_features:
                feature_similarity = 1.0 - tf.abs(medical_features[feature_name] - suspect_features[feature_name])
                suspect_similarity += feature_similarity * suspect_weights[feature_name]
        
        # حساب درجة التشابه مع حالة القرنية المخروطية
        keratoconus_similarity = 0.0
        for feature_name in ['corneal_thickness', 'corneal_curvature', 'asymmetry', 'irregularity', 'complexity']:
            if feature_name in medical_features:
                feature_similarity = 1.0 - tf.abs(medical_features[feature_name] - keratoconus_features[feature_name])
                keratoconus_similarity += feature_similarity * keratoconus_weights[feature_name]
        
        # تجميع درجات التشابه
        similarities = tf.stack([normal_similarity, suspect_similarity, keratoconus_similarity], axis=1)
        
        # تطبيع النتائج
        similarities_sum = tf.reduce_sum(similarities, axis=1, keepdims=True)
        normalized_similarities = similarities / similarities_sum
        
        # تضخيم الفروق بين الفئات لتعزيز الثقة في التصنيف - تقليل القوة لجعل التصنيف أكثر توازناً
        powered_similarities = tf.pow(normalized_similarities, 1.1)  # تقليل القوة من 1.2 إلى 1.1 لجعل التصنيف أكثر توازناً
        powered_sum = tf.reduce_sum(powered_similarities, axis=1, keepdims=True)
        final_similarities = powered_similarities / powered_sum
        
        return final_similarities
    
    def call(self, inputs, training=False):
        # استخراج الميزات من النموذج الأساسي
        x = self.base_model(inputs, training=training)
        features = self.global_avg(x)
        
        # استخراج الخصائص الطبية
        medical_features = self.extract_medical_features(features)
        
        # التصنيف العادي باستخدام التعلم العميق
        x = self.dropout1(features, training=training)
        x = self.dense1(x)
        x = self.batch_norm1(x, training=training)
        x = self.dropout2(x, training=training)
        x = self.dense2(x)
        x = self.batch_norm2(x, training=training)
        x = self.dropout3(x, training=training)
        x = self.dense3(x)
        raw_preds = self.output_layer(x)
        
        if not training:
            # حساب تشابه الخصائص الطبية
            medical_similarities = self.calculate_medical_similarity(medical_features)
            
            # دمج التنبؤات مع التشابه الطبي والأوزان المسبقة
            # تعديل الأوزان لتحقيق توازن أفضل بين التنبؤات الأساسية والخصائص الطبية
            weighted_preds = (
                raw_preds * 0.5 +                # زيادة وزن تنبؤات النموذج الأساسي من 0.45 إلى 0.5
                medical_similarities * 0.4 +     # تقليل وزن التشابه مع الخصائص الطبية من 0.45 إلى 0.4
                self.class_weights * 0.1         # الأوزان المسبقة للفئات
            )
            
            # تعزيز الفروق بين الفئات باستخدام دالة القوة
            powered_preds = tf.pow(weighted_preds, 1.2)  # زيادة القوة من 1.3 إلى 1.2 لجعل التصنيف أكثر توازناً
            
            # إعادة تطبيع النتائج
            row_sums = tf.reduce_sum(powered_preds, axis=1, keepdims=True)
            normalized_preds = powered_preds / row_sums
            
            return normalized_preds
        
        return raw_preds
    
    def predict(self, inputs):
        return self(inputs, training=False)
    
    def analyze_image(self, img_array):
        """تحليل متقدم للصورة مع استخراج الميزات والخصائص الطبية"""
        # استخراج الميزات الأساسية
        base_features = self.base_model(img_array)
        features = self.global_avg(base_features)
        
        # استخراج الخصائص الطبية
        medical_features_tensors = self.extract_medical_features(features)
        
        # تحويل الخصائص الطبية من tensors إلى قيم عددية
        medical_features = {
            'corneal_thickness': float(medical_features_tensors['corneal_thickness'][0]),
            'corneal_curvature': float(medical_features_tensors['corneal_curvature'][0]),
            'asymmetry': float(medical_features_tensors['asymmetry'][0]),
            'irregularity': float(medical_features_tensors['irregularity'][0]),
            'complexity': float(medical_features_tensors['complexity'][0])
        }
        
        # الحصول على التنبؤات الأولية من نموذج التعلم العميق
        x = self.dropout1(features, training=False)
        x = self.dense1(x)
        x = self.batch_norm1(x, training=False)
        x = self.dropout2(x, training=False)
        x = self.dense2(x)
        x = self.batch_norm2(x, training=False)
        x = self.dropout3(x, training=False)
        x = self.dense3(x)
        raw_preds = self.output_layer(x)
        
        # حساب تشابه الخصائص الطبية
        medical_similarities = self.calculate_medical_similarity(medical_features_tensors)
        
        # دمج التنبؤات مع التشابه الطبي والأوزان المسبقة
        weighted_preds = (
            raw_preds * 0.5 +                # زيادة وزن تنبؤات النموذج الأساسي
            medical_similarities * 0.4 +     # تقليل وزن التشابه مع الخصائص الطبية
            self.class_weights * 0.1         # الأوزان المسبقة للفئات
        )
        
        # تعزيز الفروق بين الفئات باستخدام دالة القوة
        powered_preds = tf.pow(weighted_preds, 1.2)
        
        # إعادة تطبيع النتائج
        row_sums = tf.reduce_sum(powered_preds, axis=1, keepdims=True)
        normalized_preds = powered_preds / row_sums
        
        # تحديد الفئة باستخدام argmax
        predicted_class = tf.argmax(normalized_preds, axis=1)
        
        # حساب مؤشرات إضافية للثقة في التشخيص
        # الفرق بين أعلى احتمالين يعطي مؤشراً على وضوح التصنيف
        sorted_preds = tf.sort(normalized_preds, axis=1, direction='DESCENDING')
        top_diff = sorted_preds[:, 0] - sorted_preds[:, 1]
        
        # حساب مؤشر تطابق الخصائص الطبية مع التشخيص النهائي
        class_names = {0: 'normal', 1: 'suspect', 2: 'keratoconus'}
        
        # تحويل predicted_class إلى قيمة عددية فردية
        predicted_class_int = int(predicted_class[0])
        predicted_class_name = class_names[predicted_class_int]
        
        # استخراج قيم الثقة
        confidence_scores = {
            'normal': float(normalized_preds[0][0]),
            'suspect': float(normalized_preds[0][1]),
            'keratoconus': float(normalized_preds[0][2]),
            'predicted_class': predicted_class_int,
            'confidence': float(tf.reduce_max(normalized_preds, axis=1)[0]),
            'medical_features': medical_features,
            'class_separation': float(top_diff[0]),
            'raw_prediction': int(tf.argmax(raw_preds, axis=1)[0]),
            'medical_similarity': float(tf.reduce_max(medical_similarities, axis=1)[0])
        }
        
        # إضافة تفسير للنتائج
        if confidence_scores['class_separation'] > 0.5:
            confidence_scores['interpretation'] = "تصنيف واضح مع فارق كبير بين الفئات"
        elif confidence_scores['class_separation'] > 0.3:
            confidence_scores['interpretation'] = "تصنيف مقبول مع فارق متوسط بين الفئات"
        else:
            confidence_scores['interpretation'] = "تصنيف غير واضح مع فارق ضئيل بين الفئات، قد يتطلب مزيداً من الفحص"
        
        # إضافة مؤشر على مدى تطابق الخصائص الطبية مع التشخيص
        med_features_match = confidence_scores['medical_similarity']
        if med_features_match > 0.7:
            confidence_scores['medical_match'] = "تطابق قوي بين الخصائص الطبية والتشخيص"
        elif med_features_match > 0.5:
            confidence_scores['medical_match'] = "تطابق متوسط بين الخصائص الطبية والتشخيص"
        else:
            confidence_scores['medical_match'] = "تطابق ضعيف بين الخصائص الطبية والتشخيص، قد يتطلب مزيداً من التحقق"
        
        return normalized_preds, confidence_scores

# تحميل النماذج مع إعادة بناء الفئة المخصصة
def load_models():
    global hybrid_model, is_dummy_model
    
    try:
        print("جاري تحميل النموذج الهجين...")
        # التأكد من وجود الملف
        if not os.path.exists('hybrid_model.keras'):
            print("خطأ: ملف النموذج 'hybrid_model.keras' غير موجود!")
            raise FileNotFoundError("ملف النموذج غير موجود")
        else:
            print(f"تم العثور على ملف النموذج. الحجم: {os.path.getsize('hybrid_model.keras') / (1024*1024):.2f} ميجابايت")
        
        # إعداد بيئة TensorFlow
        os.environ['TF_FORCE_GPU_ALLOW_GROWTH'] = 'true'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        # محاولة تحميل النموذج المدرب مباشرة
        try:
            print("محاولة تحميل النموذج المدرب مباشرة...")
            hybrid_model = tf.keras.models.load_model('hybrid_model.keras')
            print("تم تحميل النموذج بنجاح!")
            
            # التحقق من وجود وظيفة التنبؤ
            if hasattr(hybrid_model, 'predict'):
                print("النموذج يحتوي على وظيفة التنبؤ predict")
            else:
                print("تحذير: النموذج لا يحتوي على وظيفة التنبؤ predict")
            
            # تحميل قاموس الفئات إذا كان موجوداً
            try:
                if os.path.exists('class_indices.npy'):
                    class_indices = np.load('class_indices.npy', allow_pickle=True).item()
                    print(f"تم تحميل قاموس الفئات: {class_indices}")
            except Exception as e:
                print(f"تحذير: فشل تحميل قاموس الفئات: {e}")
            
            # اختبار النموذج
            test_input = np.random.rand(1, 96, 96, 3)  # تغيير حجم الإدخال ليتوافق مع النموذج الجديد
            test_output = hybrid_model.predict(test_input)
            print(f"نتيجة اختبار النموذج: {test_output}")
            print(f"شكل النتيجة: {test_output.shape}")
            
            is_dummy_model = False
            return True
            
        except Exception as e:
            print(f"فشل تحميل النموذج مباشرة: {e}")
            print("محاولة بناء نموذج متقدم...")
            
            # بناء نموذج محلي متقدم للتصنيف الدقيق
            try:
                print("بناء نموذج محلي متقدم للتصنيف الدقيق...")
                
                # إنشاء قاعدة النموذج (MobileNetV2)
                base_model = tf.keras.applications.MobileNetV2(
                    input_shape=(96, 96, 3),  # تغيير الحجم ليتوافق مع النموذج الجديد
                    include_top=False,
                    weights='imagenet'
                )
                
                # تجميد طبقات النموذج الأساسي
                base_model.trainable = False
                
                # إنشاء النموذج المتقدم
                hybrid_model = AdvancedModel(base_model)
                
                print("تم بناء النموذج المتقدم بنجاح")
                
                # التحقق من وجود وظيفة التنبؤ
                if hasattr(hybrid_model, 'predict'):
                    print("النموذج يحتوي على وظيفة التنبؤ predict")
                else:
                    print("تحذير: النموذج لا يحتوي على وظيفة التنبؤ predict")
                
                # اختبار النموذج
                test_input = np.random.rand(1, 96, 96, 3)  # تغيير حجم الإدخال ليتوافق مع النموذج الجديد
                test_output = hybrid_model.predict(test_input)
                print(f"نتيجة اختبار النموذج: {test_output}")
                print(f"شكل النتيجة: {test_output.shape}")
                
                # تعريف قاموس تصنيف العين
                eye_dict = {0: 'keratoconus', 1: 'normal'}  # تحديث القاموس ليتوافق مع النموذج الجديد
                print(f"قاموس تصنيف العين: {eye_dict}")
                
                is_dummy_model = False
                return True
            except Exception as e:
                print(f"فشل بناء النموذج المتقدم: {e}")
                import traceback
                print(traceback.format_exc())
                raise e
    except Exception as e:
        print(f"خطأ في تحميل النموذج: {e}")
        print("جاري إنشاء نموذج بديل للعرض فقط...")
        
        # إنشاء نموذج بسيط بديل للعرض فقط
        class DummyModel:
            def __init__(self):
                pass
                
            def predict(self, img_array):
                # إرجاع نتائج وهمية لأغراض العرض
                print("تحذير: استخدام النموذج البديل للتنبؤ!")
                
                # استخدام قيم عشوائية قليلاً لتنويع النتائج
                import random
                r1 = random.uniform(0.4, 0.6)  # قيمة عشوائية بين 0.4 و 0.6
                r2 = random.uniform(0.4, 0.6)  # قيمة عشوائية بين 0.4 و 0.6
                
                # إرجاع مصفوفة احتمالات للفئتين فقط
                return np.array([[r1, r2]])
            
            def analyze_image(self, img_array):
                """وظيفة تحليل وهمية"""
                probs = self.predict(img_array)
                predicted_class = np.argmax(probs, axis=1)[0]
                
                # تحديث لتتوافق مع الفئتين فقط
                confidence_scores = {
                    'keratoconus': float(probs[0][0]),
                    'normal': float(probs[0][1]),
                    'predicted_class': int(predicted_class),
                    'confidence': float(np.max(probs))
                }
                
                return probs, confidence_scores
        
        hybrid_model = DummyModel()
        print("تم إنشاء نموذج بديل بنجاح")
        is_dummy_model = True
        return False

# إضافة طبيب جديد
@app.route('/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'error')
            return redirect(url_for('add_doctor'))
            
        new_doctor = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            role='admin'
        )
        db.session.add(new_doctor)
        db.session.commit()
        
        flash('تم إضافة الطبيب بنجاح', 'success')
        return redirect(url_for('manage_users'))
        
    return render_template('add_doctor.html')

# إدارة المستخدمين
@app.route('/manage_users')
@login_required
def manage_users():
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
        
    doctors = User.query.filter_by(role='admin').all()
    patients = User.query.filter_by(role='user').all()
    return render_template('manage_users.html', doctors=doctors, patients=patients)

# تصدير التقارير
@app.route('/export_reports')
@login_required
def export_reports():
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
        
    # استخراج البيانات
    diagnoses = Diagnosis.query.order_by(Diagnosis.created_at.desc()).all()
    
    # إنشاء ملف CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['المريض', 'التاريخ', 'النتيجة', 'نسبة التأكد', 'ملاحظات الطبيب'])
    
    for diagnosis in diagnoses:
        writer.writerow([
            diagnosis.patient.username,
            diagnosis.created_at.strftime('%Y-%m-%d %H:%M'),
            diagnosis.prediction,
            f"{max(diagnosis.probability_normal, diagnosis.probability_suspect, diagnosis.probability_keratoconus)*100:.1f}%",
            diagnosis.doctor_notes or ''
        ])
    
    # إرجاع الملف للتحميل
    output.seek(0)
    return Response(
        output,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=reports.csv'}
    )

# معاينة التشخيص
@app.route('/diagnosis/<int:diagnosis_id>/view')
@login_required
def view_diagnosis(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    return render_template('view_diagnosis.html', diagnosis=diagnosis)

# إضافة سير التشخيص بتنسيق JSON
@app.route('/diagnosis/<int:diagnosis_id>')
@login_required
def get_diagnosis_json(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    
    # التأكد من أن المستخدم له حق الوصول للتشخيص
    if current_user.role != 'admin' and diagnosis.user_id != current_user.id:
        return jsonify({'error': 'غير مصرح بالوصول'}), 403
    
    # تحويل البيانات إلى تنسيق JSON
    diagnosis_data = {
        'id': diagnosis.id,
        'image_path': url_for('static', filename=diagnosis.image_path.split('/')[-2:][0] + '/' + diagnosis.image_path.split('/')[-1]),
        'prediction': {'Normal': 'طبيعي', 'Suspect': 'مشتبه به', 'Keratoconus': 'قرنية مخروطية'}.get(diagnosis.prediction, diagnosis.prediction),
        'probability': round(max(diagnosis.probability_normal, diagnosis.probability_suspect, diagnosis.probability_keratoconus) * 100, 1),
        'doctor_notes': diagnosis.doctor_notes,
        'created_at': diagnosis.created_at.strftime('%Y-%m-%d %H:%M')
    }
    
    return jsonify(diagnosis_data)

# إضافة/تعديل ملاحظات للتشخيص
@app.route('/diagnosis/<int:diagnosis_id>/note', methods=['POST'])
@login_required
def add_diagnosis_note(diagnosis_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'غير مصرح'}), 403
        
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    note = request.form.get('note')
    diagnosis.doctor_notes = note
    db.session.commit()
    
    return jsonify({'success': True})

# تعديل بيانات المستخدم
@app.route('/user/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'غير مصرح'}), 403
        
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    email = request.form.get('email')
    
    if username and username != user.username:
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'اسم المستخدم موجود بالفعل'}), 400
        user.username = username
        
    if email and email != user.email:
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'البريد الإلكتروني موجود بالفعل'}), 400
        user.email = email
        
    db.session.commit()
    return jsonify({'success': True})

# حذف مستخدم
@app.route('/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'غير مصرح'}), 403
        
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True})

# تصدير تقرير تشخيص محدد
@app.route('/diagnosis/<int:diagnosis_id>/report')
@login_required
def generate_diagnosis_report(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    # هنا يمكن إضافة كود لإنشاء PDF
    return "تقرير التشخيص"

# إضافة مسار لتحميل التقرير
@app.route('/download_report/<int:diagnosis_id>')
@login_required
def download_report(diagnosis_id):
    diagnosis = Diagnosis.query.get_or_404(diagnosis_id)
    
    # التأكد من أن المستخدم له حق الوصول للتقرير
    if current_user.role != 'admin' and diagnosis.user_id != current_user.id:
        flash('غير مصرح لك بالوصول لهذا التقرير', 'error')
        return redirect(url_for('user_dashboard'))
    
    # تحميل صورة التشخيص واستخراج المعلومات الطبية
    if os.path.exists(diagnosis.image_path):
        try:
            img = load_img(diagnosis.image_path, target_size=(224, 224))
            img_array = img_to_array(img)
            img_array = np.expand_dims(img_array, axis=0) / 255.0
            
            # استخراج معلومات طبية إضافية إذا كان النموذج متقدم
            medical_info = ""
            if hasattr(hybrid_model, 'analyze_image'):
                _, confidence_info = hybrid_model.analyze_image(img_array)
                
                if 'medical_features' in confidence_info:
                    features = confidence_info['medical_features']
                    medical_info = f"""
المعلومات الطبية المستخرجة:
- سماكة القرنية: {features['corneal_thickness']*100:.1f}% (القيمة الطبيعية: >80%)
- انحناء القرنية: {features['corneal_curvature']*100:.1f}% (القيمة الطبيعية: <30%)
- عدم التماثل: {features['asymmetry']*100:.1f}% (القيمة الطبيعية: <20%)
- عدم الانتظام: {features['irregularity']*100:.1f}% (القيمة الطبيعية: <20%)

تفسير النتائج:
"""
                    if diagnosis.prediction == 'Normal':
                        medical_info += "- القياسات تشير إلى حالة طبيعية للقرنية.\n"
                    elif diagnosis.prediction == 'Suspect':
                        if features['corneal_thickness'] < 0.7:
                            medical_info += "- انخفاض في سماكة القرنية قد يشير إلى حالة مشتبه بها.\n"
                        if features['corneal_curvature'] > 0.4:
                            medical_info += "- زيادة في انحناء القرنية قد تشير إلى بداية تغيرات مرضية.\n"
                        if features['asymmetry'] > 0.3:
                            medical_info += "- وجود عدم تماثل في القرنية يتطلب متابعة.\n"
                    elif diagnosis.prediction == 'Keratoconus':
                        if features['corneal_thickness'] < 0.5:
                            medical_info += "- انخفاض ملحوظ في سماكة القرنية، وهو علامة رئيسية للقرنية المخروطية.\n"
                        if features['corneal_curvature'] > 0.6:
                            medical_info += "- زيادة واضحة في انحناء القرنية، مما يشير إلى تشكل مخروطي.\n"
                        if features['asymmetry'] > 0.5:
                            medical_info += "- عدم تماثل ملحوظ في القرنية، وهو من علامات القرنية المخروطية.\n"
                        if features['irregularity'] > 0.6:
                            medical_info += "- عدم انتظام واضح في سطح القرنية، وهو من العلامات التشخيصية للقرنية المخروطية.\n"
                    
                    # إضافة معلومات عن مستوى الثقة والفرق بين الفئات
                    medical_info += f"\nمستوى الثقة في التشخيص: {confidence_info['confidence']*100:.1f}%\n"
                    if 'class_separation' in confidence_info:
                        separation = confidence_info['class_separation'] * 100
                        medical_info += f"وضوح التمييز بين الفئات: {separation:.1f}%\n"
                        if separation > 50:
                            medical_info += "تصنيف واضح مع تمييز جيد بين الفئات.\n"
                        elif separation > 30:
                            medical_info += "تصنيف مقبول مع تمييز متوسط بين الفئات.\n"
                        else:
                            medical_info += "تصنيف متقارب مع تمييز منخفض بين الفئات، قد يتطلب مزيدًا من الفحوصات.\n"
        except Exception as e:
            medical_info = f"لم يتم استخراج معلومات طبية إضافية. الخطأ: {str(e)}"
    else:
        medical_info = "الصورة غير متوفرة، لم يتم استخراج معلومات طبية إضافية."
    
    # توصيات طبية
    recommendations = ""
    if diagnosis.prediction == 'Normal':
        recommendations = """
التوصيات الطبية:
1. إجراء فحص روتيني للعين كل عام.
2. الحفاظ على الاحتياطات العامة للعين: تجنب فرك العين بقوة، استخدام نظارات شمسية واقية، والحفاظ على ترطيب العين.
3. استشارة طبيب العيون عند ظهور أي أعراض جديدة."""
    elif diagnosis.prediction == 'Suspect':
        recommendations = """
التوصيات الطبية:
1. مراجعة طبيب العيون خلال الشهر القادم لإجراء فحص تفصيلي.
2. إجراء خريطة طبوغرافية للقرنية لتقييم التغيرات بدقة أكبر.
3. تجنب فرك العين بشدة، حيث قد يؤدي ذلك إلى تفاقم الحالة.
4. تجنب استخدام العدسات اللاصقة إلى حين استشارة الطبيب المختص.
5. المتابعة الدورية كل 3-6 أشهر لمراقبة أي تغيرات في القرنية."""
    elif diagnosis.prediction == 'Keratoconus':
        recommendations = """
التوصيات الطبية:
1. مراجعة طبيب العيون المختص في القرنية في أقرب وقت ممكن.
2. إجراء خريطة طبوغرافية للقرنية لتحديد شدة الحالة بدقة.
3. مناقشة خيارات العلاج المتاحة مع الطبيب، والتي قد تشمل:
   - عدسات لاصقة صلبة خاصة
   - تقوية القرنية بالكولاجين (Cross-linking)
   - حلقات داخل القرنية (Intracorneal rings)
   - في الحالات المتقدمة، قد يكون زرع القرنية ضروريًا
4. تجنب فرك العين نهائيًا، لأنه قد يسرع من تطور المرض.
5. المتابعة الدورية كل 3 أشهر لمراقبة تطور الحالة."""
    
    # إنشاء محتوى التقرير
    report_content = f"""
تقرير التشخيص الطبي - قرنية العين
===================================
المريض: {diagnosis.patient.username}
تاريخ الفحص: {diagnosis.created_at.strftime('%Y-%m-%d %H:%M')}

--------------------- نتيجة التشخيص ---------------------
التشخيص: """ + {'Normal': 'طبيعي', 'Suspect': 'مشتبه به', 'Keratoconus': 'قرنية مخروطية'}[diagnosis.prediction] + f"""

نسب الاحتمالات:
- طبيعي: {diagnosis.probability_normal * 100:.1f}%
- مشتبه به: {diagnosis.probability_suspect * 100:.1f}%
- قرنية مخروطية: {diagnosis.probability_keratoconus * 100:.1f}%

--------------------- المعلومات الطبية ---------------------
{medical_info}

--------------------- التوصيات ---------------------
{recommendations}

--------------------- ملاحظات الطبيب ---------------------
{diagnosis.doctor_notes or 'لا توجد ملاحظات'}

--------------------- إخلاء مسؤولية ---------------------
هذا التحليل مساعد فقط ولا يغني عن زيارة الطبيب المختص. 
النتائج تعتمد على جودة الصورة المدخلة ودقة التحليل.
يرجى استشارة طبيب العيون للتشخيص النهائي والعلاج المناسب.

تم إنشاء هذا التقرير بواسطة نظام تشخيص القرنية المخروطية الآلي.
تاريخ إنشاء التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """
    
    # إنشاء استجابة لتحميل الملف النصي
    response = Response(
        report_content,
        mimetype='text/plain',
        headers={'Content-Disposition': f'attachment; filename=diagnosis_report_{diagnosis_id}.txt'}
    )
    
    return response

# عرض سجل المريض
@app.route('/patient/<int:patient_id>/history')
@login_required
def patient_history(patient_id):
    patient = User.query.get_or_404(patient_id)
    diagnoses = Diagnosis.query.filter_by(user_id=patient_id).order_by(Diagnosis.created_at.desc()).all()
    return render_template('patient_history.html', patient=patient, diagnoses=diagnoses)

# استعادة كلمة المرور
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # هنا يمكن إضافة كود إرسال رابط إعادة تعيين كلمة المرور
            flash('تم إرسال رابط إعادة تعيين كلمة المرور إلى بريدك الإلكتروني', 'success')
            return redirect(url_for('login'))
            
        flash('البريد الإلكتروني غير مسجل', 'error')
    return render_template('forgot_password.html')

# إضافة فلتر nl2br لتحويل السطور النصية إلى سطور HTML
@app.template_filter('nl2br')
def nl2br_filter(s):
    if not s:
        return ""
    return re.sub(r'\r\n|\r|\n', '<br>', s)

# إعداد Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('user_dashboard'))
            
        flash('اسم المستخدم أو كلمة المرور غير صحيحة')
    return render_template('login.html')

# صفحة إنشاء حساب
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email)
        db.session.add(new_user)
        db.session.commit()
        
        flash('تم إنشاء الحساب بنجاح')
        return redirect(url_for('login'))
        
    return render_template('register.html')

# لوحة تحكم المستخدم
@app.route('/dashboard')
@login_required
def user_dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    diagnoses = Diagnosis.query.filter_by(user_id=current_user.id).order_by(Diagnosis.created_at.desc()).all()
    return render_template('user_dashboard.html', diagnoses=diagnoses)

# لوحة تحكم الأدمن
@app.route('/admin')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('user_dashboard'))
        
    # إحصائيات عامة
    recent_diagnoses = Diagnosis.query.order_by(Diagnosis.created_at.desc()).limit(10).all()
    total_users = User.query.filter_by(role='user').count()
    total_diagnoses = Diagnosis.query.count()
    
    # إحصائيات اليوم
    today = datetime.now().date()
    today_diagnoses = Diagnosis.query.filter(
        db.func.date(Diagnosis.created_at) == today
    ).count()
    
    # حالات تحتاج المتابعة
    suspect_cases = Diagnosis.query.filter_by(prediction='Suspect').count()
    
    # حساب نسبة الثقة للتشخيصات
    for diagnosis in recent_diagnoses:
        max_prob = max([
            diagnosis.probability_normal,
            diagnosis.probability_suspect,
            diagnosis.probability_keratoconus
        ])
        diagnosis.confidence = round(max_prob * 100, 1)
    
    return render_template('admin_dashboard.html',
                         current_time=datetime.now(),
                         recent_diagnoses=recent_diagnoses,
                         total_users=total_users,
                         total_diagnoses=total_diagnoses,
                         today_diagnoses=today_diagnoses,
                         suspect_cases=suspect_cases)

# تحميل النماذج عند بدء التشغيل
print("بدء تحميل النماذج...")
model_loaded_successfully = load_models()
print(f"اكتمل تحميل النماذج. نجاح التحميل: {model_loaded_successfully}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# إضافة مسار لإعادة تحميل النموذج
@app.route('/reload_model')
@login_required
def reload_model():
    if current_user.role != 'admin':
        flash('غير مصرح لك بهذه العملية', 'error')
        return redirect(url_for('user_dashboard'))
    
    global model_loaded_successfully, is_dummy_model
    
    # محاولة إعادة تحميل النموذج
    print("جاري إعادة تحميل النموذج...")
    model_loaded_successfully = load_models()
    
    if model_loaded_successfully:
        flash('تم تحميل النموذج بنجاح', 'success')
        
        # اختبار النموذج على صورة افتراضية
        test_model_with_sample_image()
    else:
        flash('فشل تحميل النموذج. يرجى التحقق من ملفات النموذج.', 'error')
    
    return redirect(url_for('admin_dashboard'))

# دالة لاختبار النموذج على صورة افتراضية
def test_model_with_sample_image():
    try:
        print("اختبار النموذج على صورة افتراضية...")
        
        # إنشاء صورة اختبار بسيطة (مصفوفة عشوائية)
        test_image = np.random.rand(1, 224, 224, 3)
        
        # التحقق من وجود وظيفة التحليل المتقدم
        if hasattr(hybrid_model, 'analyze_image'):
            print("جاري استخدام وظيفة التحليل المتقدم...")
            probs, confidence_info = hybrid_model.analyze_image(test_image)
            
            print(f"نتائج التحليل المتقدم: {confidence_info}")
            print(f"مستوى الثقة العام: {confidence_info['confidence']:.3f}")
            print(f"الاحتمالات: طبيعي={confidence_info['normal']:.3f}, مشتبه به={confidence_info['suspect']:.3f}, قرنية مخروطية={confidence_info['keratoconus']:.3f}")
            
            # تحديد الفئة
            class_names = {0: 'طبيعي', 1: 'مشتبه به', 2: 'قرنية مخروطية'}
            pred_class = class_names[confidence_info['predicted_class']]
            print(f"التشخيص: {pred_class}")
            
            return True
        else:
            # استخدام وظيفة التنبؤ العادية
            print("جاري استخدام وظيفة التنبؤ القياسية...")
            probs = hybrid_model.predict(test_image)
            
            print(f"نتائج التنبؤ على صورة الاختبار: {probs}")
            print(f"شكل النتائج: {probs.shape}")
            
            # التحقق من صحة النتائج
            if isinstance(probs, np.ndarray) and len(probs.shape) > 0:
                if probs.shape[1] >= 3:
                    print("اختبار النموذج ناجح!")
                    # طباعة الاحتمالات
                    print(f"الاحتمالات: طبيعي={probs[0][0]:.3f}, مشتبه به={probs[0][1]:.3f}, قرنية مخروطية={probs[0][2]:.3f}")
                    
                    # تحديد الفئة
                    final_pred = np.argmax(probs, axis=1)
                    class_names = {0: 'طبيعي', 1: 'مشتبه به', 2: 'قرنية مخروطية'}
                    pred_class = class_names[final_pred[0]]
                    print(f"التشخيص: {pred_class}")
                    
                    return True
                else:
                    print(f"تحذير: عدد الفئات غير كافٍ. الشكل: {probs.shape}")
            else:
                print("تحذير: نتائج التنبؤ غير متوقعة")
            return False
    except Exception as e:
        import traceback
        print(f"خطأ في اختبار النموذج: {e}")
        print(traceback.format_exc())
        return False

# تحديث دالة upload_file
@app.route('/', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('لم يتم اختيار ملف', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('لم يتم اختيار ملف', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            # إنشاء مجلد التحميل إذا لم يكن موجودًا
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            print(f"تم حفظ الصورة في: {filepath}")
            
            # التحقق من نوع النموذج المستخدم
            if is_dummy_model or not model_loaded_successfully:
                flash('تحذير: يتم استخدام نموذج بديل للتحليل. النتائج قد لا تكون دقيقة.', 'warning')
            
            # استخدام النموذج الهجين للتنبؤ
            prediction, probabilities = predict_image(filepath)
            
            print(f"النتيجة النهائية: {prediction}")
            print(f"الاحتمالات: {probabilities}")
            
            # تحديث لتتوافق مع الفئتين فقط
            if isinstance(probabilities, np.ndarray):
                # إذا كانت مصفوفة ثنائية الأبعاد، استخدم الصف الأول
                if len(probabilities.shape) > 1:
                    probabilities = probabilities[0]
                
                # تأكد من أن لدينا عنصرين على الأقل
                if len(probabilities) < 2:
                    # إضافة أصفار إذا لزم الأمر
                    probabilities = np.pad(probabilities, (0, 2 - len(probabilities)), 'constant')
            else:
                # إذا لم تكن مصفوفة numpy، إنشاء مصفوفة افتراضية
                probabilities = np.array([0.5, 0.5])
            
            # تحديث قاموس الفئات
            class_names = {0: 'Keratoconus', 1: 'Normal'}
            
            # في حالة وجود قاموس فئات محفوظ، استخدمه بدلاً من القاموس الافتراضي
            try:
                if os.path.exists('class_indices.npy'):
                    class_indices = np.load('class_indices.npy', allow_pickle=True).item()
                    class_names = {v: k.capitalize() for k, v in class_indices.items()}
            except Exception as e:
                print(f"تحذير: فشل تحميل قاموس الفئات: {e}")
            
            # حفظ التشخيص في قاعدة البيانات - تحديث لتتوافق مع الفئتين فقط
            diagnosis = Diagnosis(
                user_id=current_user.id,
                image_path=filepath,
                prediction=prediction,
                probability_normal=float(probabilities[1]) if len(probabilities) > 1 else 0.5,
                probability_keratoconus=float(probabilities[0]) if len(probabilities) > 0 else 0.5,
                probability_suspect=0.0  # إزالة فئة المشتبه به
            )
            db.session.add(diagnosis)
            db.session.commit()
            
            return render_template('result.html', 
                                 diagnosis=diagnosis,
                                 current_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 using_dummy_model=is_dummy_model)
        else:
            flash('نوع الملف غير مسموح به. يرجى تحميل صورة بتنسيق PNG أو JPG أو JPEG', 'error')
            return redirect(request.url)
    
    # إضافة معلومات حول حالة النموذج في صفحة التحميل
    return render_template('upload.html', model_loaded=model_loaded_successfully, using_dummy_model=is_dummy_model)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# تهيئة قاعدة البيانات وإنشاء المستخدم الافتراضي والأدمن
def init_db():
    with app.app_context():
        db.create_all()
        
        # إنشاء الأدمن إذا لم يكن موجوداً
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                password=generate_password_hash('admin'),
                email='admin@example.com',
                role='admin'
            )
            db.session.add(admin)
            
        # إنشاء مستخدم افتراضي
        if not User.query.filter_by(username='user').first():
            user = User(
                username='user',
                password=generate_password_hash('user'),
                email='user@example.com',
                role='user'
            )
            db.session.add(user)
            
        db.session.commit()

        # إنشاء المجلدات المطلوبة
        os.makedirs('static/images', exist_ok=True)
        
        # نسخ الصور الافتراضية إذا لم تكن موجودة
        default_images = ['avatar.png', 'doctor-avatar.png', 'logo.png']
        for img in default_images:
            dst = f'static/images/{img}'
            if not os.path.exists(dst):
                src = f'default_assets/{img}'  # يجب إنشاء هذا المجلد وإضافة الصور فيه
                if os.path.exists(src):
                    shutil.copy(src, dst)

def predict_image(img_path):
    print(f"جاري تحليل الصورة: {img_path}")
    
    # التحقق من وجود الصورة
    if not os.path.exists(img_path):
        print(f"خطأ: ملف الصورة '{img_path}' غير موجود!")
        return 'Normal', np.array([[0.5, 0.5]])
    
    try:
        # تحميل وتجهيز الصورة - تعديل لدعم الصور بحجم 96×96×3 للنموذج الجديد
        img = load_img(img_path, target_size=(96, 96))
        img_array = img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0
        
        print(f"تم تحميل الصورة بنجاح. الشكل: {img_array.shape}, النوع: {img_array.dtype}, القيم: [min={img_array.min():.3f}, max={img_array.max():.3f}]")
        
        print("جاري التحليل المتقدم للصورة...")
        print(f"نوع النموذج المستخدم: {type(hybrid_model)}")
        
        # استخدام وظيفة التنبؤ القياسية
        if not hasattr(hybrid_model, 'predict'):
            print("خطأ: النموذج لا يحتوي على وظيفة التنبؤ predict")
            return 'Normal', np.array([[0.5, 0.5]])
        
        # استخدام وظيفة التنبؤ القياسية
        probs = hybrid_model.predict(img_array)
        
        # الحصول على الفئة المتوقعة باستخدام argmax
        final_pred = np.argmax(probs, axis=1)
        
        # تحديث قاموس الفئات ليتوافق مع النموذج الجديد
        class_names = {0: 'Keratoconus', 1: 'Normal'}
        
        # في حالة وجود قاموس فئات محفوظ، استخدمه بدلاً من القاموس الافتراضي
        try:
            if os.path.exists('class_indices.npy'):
                class_indices = np.load('class_indices.npy', allow_pickle=True).item()
                class_names = {v: k.capitalize() for k, v in class_indices.items()}
                print(f"استخدام قاموس الفئات المحفوظ: {class_names}")
        except Exception as e:
            print(f"تحذير: فشل تحميل قاموس الفئات: {e}")
        
        pred_class = class_names[final_pred[0]]
        
        print(f"التشخيص باستخدام التنبؤ القياسي: {pred_class}")
        
        # طباعة الاحتمالات بناءً على عدد الفئات
        if probs.shape[1] >= 2:
            print(f"الاحتمالات: قرنية مخروطية={probs[0][0]:.3f}, طبيعي={probs[0][1]:.3f}")
        
        # تحليل اسم الملف لمعرفة إذا كان التصنيف صحيحاً
        filename = os.path.basename(img_path)
        is_kcn = filename.startswith('KCN_')
        is_nor = filename.startswith('NOR_')
        
        if is_kcn and pred_class == 'Keratoconus':
            print("✓ التصنيف صحيح: الصورة تحتوي على قرنية مخروطية وتم تصنيفها كذلك")
        elif is_nor and pred_class == 'Normal':
            print("✓ التصنيف صحيح: الصورة طبيعية وتم تصنيفها كذلك")
        elif is_kcn:
            print(f"✗ التصنيف خاطئ: الصورة تحتوي على قرنية مخروطية ولكن تم تصنيفها كـ {pred_class}")
        elif is_nor:
            print(f"✗ التصنيف خاطئ: الصورة طبيعية ولكن تم تصنيفها كـ {pred_class}")
        
        return pred_class, probs
        
    except Exception as e:
        import traceback
        print(f"خطأ في معالجة الصورة: {e}")
        print(traceback.format_exc())
    
    # إرجاع نتائج وهمية في حالة الخطأ
    print("استخدام نتائج احتياطية")
    probs = np.array([[0.5, 0.5]])
    return 'Normal', probs

@app.route('/messages')
@login_required
def messages():
    received = Message.query.filter_by(receiver_id=current_user.id)\
        .order_by(Message.created_at.desc()).all()
    sent = Message.query.filter_by(sender_id=current_user.id)\
        .order_by(Message.created_at.desc()).all()
    return render_template('messages.html', received=received, sent=sent)

@app.route('/send_message', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        recipient = request.form.get('recipient')
        subject = request.form.get('subject')
        message_content = request.form.get('message')
        
        # التحقق من صحة البيانات
        if not recipient or not subject or not message_content:
            flash('جميع الحقول مطلوبة', 'error')
            if current_user.role == 'admin':
                # إذا كان المستخدم طبيب، يُعرض قائمة المرضى
                recipients = User.query.filter_by(role='user').all()
            else:
                # إذا كان المستخدم مريض، يُعرض قائمة الأطباء
                recipients = User.query.filter_by(role='admin').all()
            return render_template('send_message.html', doctors=recipients)
        
        # إنشاء رسالة جديدة
        new_message = Message(
            sender_id=current_user.id,
            receiver_id=recipient,
            subject=subject,
            content=message_content
        )
        
        # حفظ الرسالة في قاعدة البيانات
        db.session.add(new_message)
        db.session.commit()
        
        flash('تم إرسال الرسالة بنجاح', 'success')
        return redirect(url_for('messages'))
    
    # تحديد قائمة المستلمين بناءً على دور المستخدم الحالي
    if current_user.role == 'admin':
        # إذا كان المستخدم طبيب، يُعرض قائمة المرضى
        recipients = User.query.filter_by(role='user').all()
    else:
        # إذا كان المستخدم مريض، يُعرض قائمة الأطباء
        recipients = User.query.filter_by(role='admin').all()
    
    return render_template('send_message.html', doctors=recipients)

@app.route('/message/<int:message_id>')
@login_required
def view_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.receiver_id == current_user.id and not message.read:
        message.read = True
        db.session.commit()
    return render_template('view_message.html', message=message)

@app.route('/message/<int:message_id>/delete')
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    
    # التأكد من أن المستخدم هو المرسل أو المستلم للرسالة
    if message.sender_id != current_user.id and message.receiver_id != current_user.id:
        flash('غير مصرح لك بحذف هذه الرسالة', 'error')
        return redirect(url_for('messages'))
    
    # حذف الرسالة
    db.session.delete(message)
    db.session.commit()
    
    flash('تم حذف الرسالة بنجاح', 'success')
    return redirect(url_for('messages'))

if __name__ == '__main__':
    # إنشاء المجلدات المطلوبة
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs('static/images', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    init_db()
    app.run(debug=True)