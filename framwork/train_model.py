import numpy as np
import pandas as pd
import os
import tensorflow as tf
from tensorflow.keras.models import Sequential, Model
from tensorflow.keras.layers import Conv2D, MaxPooling2D, BatchNormalization, Flatten, LeakyReLU, Dense, Dropout, Input, GlobalAveragePooling2D
from tensorflow.keras.applications import MobileNetV2
import matplotlib.pyplot as plt
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
from tensorflow.keras.preprocessing.image import ImageDataGenerator
import glob
import math
import cv2

# تعيين مسار البيانات الرئيسي
BASE_DATA_DIR = "data"

print("="*50)
print("بدء تدريب نموذج للكشف عن القرنية المخروطية")
print("="*50)

# مسارات البيانات المعالجة (المقسمة مسبقاً)
train_path = os.path.join(BASE_DATA_DIR, "processed", "train")
val_path = os.path.join(BASE_DATA_DIR, "processed", "val")
test_path = os.path.join(BASE_DATA_DIR, "processed", "test")

print(f"مسار بيانات التدريب: {train_path}")
print(f"مسار بيانات التحقق: {val_path}")
print(f"مسار بيانات الاختبار: {test_path}")

# التحقق من وجود المسارات
if not os.path.exists(train_path):
    print(f"خطأ: مسار التدريب غير موجود: {train_path}")
if not os.path.exists(val_path):
    print(f"خطأ: مسار التحقق غير موجود: {val_path}")
if not os.path.exists(test_path):
    print(f"خطأ: مسار الاختبار غير موجود: {test_path}")

# التحقق من شكل الصورة باستخدام مثال
example_image_file = os.path.join(train_path, "keratoconus", os.listdir(os.path.join(train_path, "keratoconus"))[0])
if os.path.exists(example_image_file):
    x_shape_check_img = plt.imread(example_image_file)
    print(f"شكل صورة مثال ({example_image_file}): {x_shape_check_img.shape}")
else:
    print(f"تحذير: لم يتم العثور على صورة مثال للتحقق من الشكل في {example_image_file}")

# إعداد مولد البيانات مع تطبيق تقنيات زيادة البيانات
train_datagen = ImageDataGenerator(
    rescale=1/255.,
    rotation_range=15,
    width_shift_range=0.1,
    height_shift_range=0.1,
    zoom_range=0.1,
    horizontal_flip=True,
    brightness_range=[0.8, 1.2],
    fill_mode='nearest'
)

# مولد بيانات التحقق والاختبار بدون زيادة البيانات
val_test_datagen = ImageDataGenerator(rescale=1/255.)

# تحديد حجم أكبر للصور للحفاظ على التفاصيل المهمة
IMG_SIZE = 96

# إعداد مولد بيانات التدريب
print("إعداد مولد بيانات التدريب...")
train_generator = train_datagen.flow_from_directory(
    train_path,
    target_size=(IMG_SIZE, IMG_SIZE),
    class_mode="categorical",  # تغيير إلى categorical لتوافق مع categorical_crossentropy
    seed=42,
    color_mode="rgb",  # استخدام الألوان للاستفادة من نماذج التعلم المسبق
    batch_size=32  # حجم دفعة أصغر لتحسين التعلم
)

# إعداد مولد بيانات التحقق
print("إعداد مولد بيانات التحقق...")
val_generator = val_test_datagen.flow_from_directory(
    val_path,
    target_size=(IMG_SIZE, IMG_SIZE),
    class_mode="categorical",
    seed=42,
    color_mode="rgb",
    batch_size=32
)

# إعداد مولد بيانات الاختبار
print("إعداد مولد بيانات الاختبار...")
test_generator = val_test_datagen.flow_from_directory(
    test_path,
    target_size=(IMG_SIZE, IMG_SIZE),
    class_mode="categorical",
    seed=42,
    color_mode="rgb",
    batch_size=32
)

# عرض مؤشرات الفئات
print(f"مؤشرات الفئات من مولد التدريب: {train_generator.class_indices}")
eye_dict = {v: k for k, v in train_generator.class_indices.items()}

# التحقق من شكل دفعة البيانات
x_batch, y_batch = train_generator.next()
print(f"شكل دفعة واحدة من صور التدريب: {x_batch.shape}, شكل التسميات: {y_batch.shape}")
train_generator.reset()

# استخدام نموذج معد مسبقاً (Transfer Learning)
# استخدام MobileNetV2 كنموذج أساسي لأنه خفيف وفعال
base_model = MobileNetV2(
    weights='imagenet',
    include_top=False,
    input_shape=(IMG_SIZE, IMG_SIZE, 3)
)

# تجميد طبقات النموذج الأساسي
base_model.trainable = False

# بناء النموذج الكامل
inputs = Input(shape=(IMG_SIZE, IMG_SIZE, 3))
x = base_model(inputs, training=False)
x = GlobalAveragePooling2D()(x)
x = BatchNormalization()(x)
x = Dense(256, activation='relu')(x)
x = Dropout(0.5)(x)
x = Dense(128, activation='relu')(x)
x = Dropout(0.3)(x)
outputs = Dense(len(train_generator.class_indices), activation='softmax')(x)
model = Model(inputs, outputs)

# عرض ملخص النموذج
model.summary()

# تجميع النموذج
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# إعداد آليات الإيقاف المبكر وجدولة معدل التعلم وحفظ أفضل نموذج
early_stopping = EarlyStopping(
    monitor='val_accuracy',
    min_delta=0.001,
    patience=10,
    verbose=1,
    restore_best_weights=True,
)

lr_scheduler = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=5,
    min_lr=1e-6,
    verbose=1,
)

checkpoint = ModelCheckpoint(
    'best_model_checkpoint.keras',
    monitor='val_accuracy',
    save_best_only=True,
    verbose=1
)

callbacks = [
    early_stopping,
    lr_scheduler,
    checkpoint
]

# بدء تدريب النموذج - المرحلة الأولى (تدريب الطبقات العليا فقط)
print("\nبدء تدريب المرحلة الأولى...")
train_generator.reset()
val_generator.reset()

history_1 = model.fit(
    train_generator, 
    validation_data=val_generator, 
    epochs=15, 
    callbacks=callbacks
)
print("انتهى تدريب المرحلة الأولى.")

# إلغاء تجميد بعض طبقات النموذج الأساسي للضبط الدقيق
base_model.trainable = True
# تجميد الطبقات الأولى وترك الطبقات العميقة للتدريب
for layer in base_model.layers[:-30]:
    layer.trainable = False

# إعادة تجميع النموذج بمعدل تعلم أصغر للضبط الدقيق
model.compile(
    optimizer=tf.keras.optimizers.Adam(learning_rate=1e-5),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)

# بدء تدريب النموذج - المرحلة الثانية (الضبط الدقيق)
print("\nبدء تدريب المرحلة الثانية (الضبط الدقيق)...")
train_generator.reset()
val_generator.reset()

history_2 = model.fit(
    train_generator, 
    validation_data=val_generator, 
    epochs=15, 
    callbacks=callbacks
)
print("انتهى تدريب المرحلة الثانية.")

# دمج تاريخ التدريب من المرحلتين
history = {}
history['accuracy'] = history_1.history['accuracy'] + history_2.history['accuracy']
history['val_accuracy'] = history_1.history['val_accuracy'] + history_2.history['val_accuracy']
history['loss'] = history_1.history['loss'] + history_2.history['loss']
history['val_loss'] = history_1.history['val_loss'] + history_2.history['val_loss']

# رسم منحنيات التدريب
plt.figure(figsize=(12, 5))

# رسم منحنى الدقة
plt.subplot(1, 2, 1)
plt.plot(history['accuracy'], label='تدريب')
plt.plot(history['val_accuracy'], label='تحقق')
plt.title('دقة النموذج')
plt.xlabel('عصر')
plt.ylabel('دقة')
plt.legend()

# رسم منحنى الخسارة
plt.subplot(1, 2, 2)
plt.plot(history['loss'], label='تدريب')
plt.plot(history['val_loss'], label='تحقق')
plt.title('خسارة النموذج')
plt.xlabel('عصر')
plt.ylabel('خسارة')
plt.legend()

plt.tight_layout()
plt.savefig('training_history.png')
print("تم حفظ رسم تاريخ التدريب في: training_history.png")

# حفظ النموذج المدرب
model_save_path = 'hybrid_model.keras'
model.save(model_save_path)
print(f"تم حفظ النموذج المدرب في: {model_save_path}")

# اختبار النموذج على كامل مجموعة الاختبار
print("\nتقييم النموذج على مجموعة الاختبار الكاملة...")
test_generator.reset()
evaluation = model.evaluate(test_generator)
print(f"دقة النموذج على مجموعة الاختبار الكاملة: {evaluation[1]:.4f}")

# اختبار النموذج على عينة من بيانات الاختبار للعرض البصري
test_generator.reset()
x_test_batch, y_test_batch = test_generator.next()
preds = model.predict(x_test_batch)
idx_preds = np.argmax(preds, axis=1)
idx_true = np.argmax(y_test_batch, axis=1)

# حساب دقة النموذج على دفعة اختبار
correct_predictions = np.sum((idx_true == idx_preds) * 1)
batch_accuracy = correct_predictions / idx_true.shape[0]
print(f'الدقة على دفعة اختبار واحدة: {batch_accuracy:.4f} ({correct_predictions}/{idx_true.shape[0]})')

# إنشاء مصفوفة الارتباك
confusion = np.zeros((len(train_generator.class_indices), len(train_generator.class_indices)), dtype=np.int32)
for i in range(len(idx_true)):
    confusion[idx_true[i], idx_preds[i]] += 1

print("\nمصفوفة الارتباك:")
for i in range(len(train_generator.class_indices)):
    for j in range(len(train_generator.class_indices)):
        print(f"{confusion[i, j]:4d}", end=" ")
    print(f" <- {eye_dict[i]}")
print(" " * 5, end="")
for j in range(len(train_generator.class_indices)):
    print(f"{eye_dict[j]:4s}", end=" ")
print()

# عرض بعض التنبؤات بصرياً
num_images_to_plot = min(32, x_test_batch.shape[0])
plot_cols = 8
plot_rows = int(math.ceil(num_images_to_plot / plot_cols))

fig = plt.figure(figsize=(16, 12))
print(f"\nعرض التنبؤات لـ {num_images_to_plot} صورة اختبار:")

for j in range(num_images_to_plot):
    px = x_test_batch[j]
    ax = plt.subplot(plot_rows, plot_cols, j + 1)
    ax.imshow(px)
    ax.set_xticks([])
    ax.set_yticks([])

    true_label = eye_dict[idx_true[j]]
    pred_label = eye_dict[idx_preds[j]]
    confidence = np.max(preds[j]) * 100

    if true_label == pred_label:
        for axis_name in ['top','bottom','left','right']:
            ax.spines[axis_name].set_linewidth(3)
            ax.spines[axis_name].set_color('green')
        ax.set_title(f"{pred_label}\n{confidence:.1f}%", color='green', fontsize=10)
    else:
        for axis_name in ['top','bottom','left','right']:
            ax.spines[axis_name].set_linewidth(3)
            ax.spines[axis_name].set_color('red')
        ax.set_title(f"P:{pred_label} {confidence:.1f}%\nT:{true_label}", color='red', fontsize=8)
plt.tight_layout()
plt.savefig('predictions_visualization.png')
print("تم حفظ صورة التنبؤات في: predictions_visualization.png")

# حفظ قاموس الفئات لاستخدامه في التنبؤ
np.save('class_indices.npy', train_generator.class_indices)
print("تم حفظ قاموس الفئات في: class_indices.npy")

print("\nانتهى التنفيذ.") 