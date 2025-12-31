// التعامل مع رفع الملفات بالسحب والإفلات
document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');

    if (dropZone) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, highlight, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, unhighlight, false);
        });

        dropZone.addEventListener('drop', handleDrop, false);
    }

    if (fileInput) {
        fileInput.addEventListener('change', function() {
            handleFiles(this.files);
        });
    }

    // استرجاع الصورة الشخصية من التخزين المحلي عند تحميل الصفحة
    initializeProfileImages();
    
    // تطبيق إعدادات المستخدم المحفوظة
    applyUserSettings();

    // إضافة مستمع الحدث للعناصر التي تضاف بشكل ديناميكي
    initializeObservers();
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function highlight() {
    const dropZone = document.getElementById('dropZone');
    if (dropZone) {
        dropZone.classList.add('highlight');
    }
}

function unhighlight() {
    const dropZone = document.getElementById('dropZone');
    if (dropZone) {
        dropZone.classList.remove('highlight');
    }
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    handleFiles(files);
}

function handleFiles(files) {
    if (files.length > 0) {
        const formData = new FormData();
        formData.append('file', files[0]);

        Swal.fire({
            title: 'جاري رفع الملف...',
            text: 'يرجى الانتظار',
            allowOutsideClick: false,
            didOpen: () => {
                Swal.showLoading();
            }
        });

        fetch('/', {
            method: 'POST',
            body: formData
        })
        .then(response => response.text())
        .then(html => {
            document.documentElement.innerHTML = html;
        })
        .catch(error => {
            Swal.fire({
                icon: 'error',
                title: 'خطأ!',
                text: 'حدث خطأ أثناء رفع الملف'
            });
        });
    }
}

// توليد التقرير
function generateReport() {
    Swal.fire({
        title: 'جاري تحضير التقرير...',
        timer: 2000,
        timerProgressBar: true,
        didOpen: () => {
            Swal.showLoading();
        }
    }).then(() => {
        Swal.fire({
            title: 'تم!',
            text: 'تم تحميل التقرير بنجاح',
            icon: 'success'
        });
    });
}

// مشاركة النتيجة
function shareResult() {
    Swal.fire({
        title: 'مشاركة النتيجة',
        html: `
            <div style="display: flex; justify-content: center; gap: 20px; margin-top: 20px;">
                <button class="share-btn" onclick="shareViaEmail()">
                    <i class="fas fa-envelope"></i>
                </button>
                <button class="share-btn" onclick="shareViaWhatsApp()">
                    <i class="fab fa-whatsapp"></i>
                </button>
                <button class="share-btn" onclick="copyLink()">
                    <i class="fas fa-link"></i>
                </button>
            </div>
        `,
        showConfirmButton: false
    });
}

// التعامل مع الإشعارات وملف المستخدم في الشريط العلوي
document.addEventListener('DOMContentLoaded', function() {
    // إغلاق القوائم عند النقر خارجها
    document.addEventListener('click', function(event) {
        const notificationsMenu = document.getElementById('notificationsMenu');
        const profileMenu = document.getElementById('profileMenu');
        const notificationsButton = document.querySelector('.notifications');
        const profileButton = document.querySelector('.profile');
        
        if (notificationsMenu && !notificationsButton.contains(event.target) && !notificationsMenu.contains(event.target)) {
            notificationsMenu.classList.remove('show');
        }
        
        if (profileMenu && !profileButton.contains(event.target) && !profileMenu.contains(event.target)) {
            profileMenu.classList.remove('show');
            profileButton.classList.remove('active');
        }
    });
});

// تبديل عرض قائمة الإشعارات
function toggleNotificationsMenu() {
    const menu = document.getElementById('notificationsMenu');
    if (menu) {
        menu.classList.toggle('show');
    }
}

// تبديل عرض قائمة الملف الشخصي
function toggleProfileMenu() {
    const menu = document.getElementById('profileMenu');
    const profileButton = document.querySelector('.profile');
    if (menu) {
        menu.classList.toggle('show');
        profileButton.classList.toggle('active');
    }
}

// تنفيذ البحث
function performSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput && searchInput.value.trim() !== '') {
        // عرض رسالة أثناء البحث
        Swal.fire({
            title: 'جاري البحث...',
            text: `البحث عن "${searchInput.value}"`,
            timer: 1500,
            timerProgressBar: true,
            didOpen: () => {
                Swal.showLoading();
            }
        }).then(() => {
            // هنا يمكن إضافة كود لعرض نتائج البحث
            Swal.fire({
                title: 'نتائج البحث',
                html: `
                    <div class="search-results">
                        <p>تم العثور على 3 نتائج لـ "${searchInput.value}"</p>
                        <div class="search-result-item">
                            <h4>فحص البصر #12345</h4>
                            <p>تاريخ: 2023-05-15</p>
                        </div>
                        <div class="search-result-item">
                            <h4>فحص قرنية العين #67890</h4>
                            <p>تاريخ: 2023-04-20</p>
                        </div>
                        <div class="search-result-item">
                            <h4>تشخيص مريض #34567</h4>
                            <p>تاريخ: 2023-03-10</p>
                        </div>
                    </div>
                `,
                confirmButtonText: 'إغلاق'
            });
        });
    }
}

// تحديث أحداث النقر بعد تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    // إضافة أحداث النقر للأزرار الجديدة
    const allNotificationsLink = document.querySelector('.notifications-footer a');
    if (allNotificationsLink) {
        allNotificationsLink.addEventListener('click', function(e) {
            e.preventDefault();
            showAllNotifications();
        });
    }
    
    // تعيين وظائف لروابط قائمة الملف الشخصي
    const profileLinks = document.querySelectorAll('.profile-menu a');
    profileLinks.forEach(link => {
        if (link.textContent.includes('الملف الشخصي')) {
            link.addEventListener('click', function(e) {
                if (!link.getAttribute('href').startsWith('http')) {
                    e.preventDefault();
                    showUserProfile();
                }
            });
        } else if (link.textContent.includes('الإعدادات')) {
            link.addEventListener('click', function(e) {
                if (!link.getAttribute('href').startsWith('http')) {
                    e.preventDefault();
                    showUserSettings();
                }
            });
        }
    });
});

// عرض كل الإشعارات
function showAllNotifications() {
    Swal.fire({
        title: 'كل الإشعارات',
        html: `
            <div class="all-notifications">
                <div class="notification-group">
                    <h4>اليوم</h4>
                    <div class="notification-item unread">
                        <div class="notification-icon"><i class="fas fa-file-medical"></i></div>
                        <div class="notification-content">
                            <p>تم إكمال فحص جديد بنجاح</p>
                            <span class="notification-time">منذ 10 دقائق</span>
                        </div>
                    </div>
                    <div class="notification-item unread">
                        <div class="notification-icon"><i class="fas fa-user-md"></i></div>
                        <div class="notification-content">
                            <p>تم تعيين موعد مراجعة جديد</p>
                            <span class="notification-time">منذ 30 دقيقة</span>
                        </div>
                    </div>
                    <div class="notification-item unread">
                        <div class="notification-icon"><i class="fas fa-comment-medical"></i></div>
                        <div class="notification-content">
                            <p>رسالة جديدة من الدكتور</p>
                            <span class="notification-time">منذ ساعة</span>
                        </div>
                    </div>
                </div>
                <div class="notification-group">
                    <h4>الأمس</h4>
                    <div class="notification-item">
                        <div class="notification-icon"><i class="fas fa-calendar-check"></i></div>
                        <div class="notification-content">
                            <p>تم تأكيد موعد الفحص</p>
                            <span class="notification-time">الأمس، 14:30</span>
                        </div>
                    </div>
                    <div class="notification-item">
                        <div class="notification-icon"><i class="fas fa-file-alt"></i></div>
                        <div class="notification-content">
                            <p>تم إضافة تقرير جديد إلى ملفك</p>
                            <span class="notification-time">الأمس، 11:20</span>
                        </div>
                    </div>
                </div>
                <div class="notification-group">
                    <h4>هذا الأسبوع</h4>
                    <div class="notification-item">
                        <div class="notification-icon"><i class="fas fa-pills"></i></div>
                        <div class="notification-content">
                            <p>تذكير بموعد الدواء</p>
                            <span class="notification-time">منذ 3 أيام</span>
                        </div>
                    </div>
                    <div class="notification-item">
                        <div class="notification-icon"><i class="fas fa-heart"></i></div>
                        <div class="notification-content">
                            <p>نتائج فحص ضغط الدم جاهزة</p>
                            <span class="notification-time">منذ 5 أيام</span>
                        </div>
                    </div>
                </div>
            </div>
        `,
        width: '600px',
        confirmButtonText: 'إغلاق',
        showClass: {
            popup: 'animate__animated animate__fadeInDown'
        },
        hideClass: {
            popup: 'animate__animated animate__fadeOutUp'
        }
    });
}

// عرض الملف الشخصي
function showUserProfile() {
    // تحديد نوع الحساب للعرض المناسب
    const accountType = determineAccountType();
    
    // محتوى مخصص للمريض
    let profileRole = 'مريض';
    let profileDetails = '';
    let profileStats = '';
    
    if (accountType === 'admin') {
        // إذا كان الحساب لمسؤول النظام
        profileRole = 'طبيب - اخصائي عيون';
        profileStats = `
            <div class="profile-stats">
                <div class="stat-item">
                    <span class="stat-value">145</span>
                    <span class="stat-label">فحص تم إجراؤه</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">98%</span>
                    <span class="stat-label">دقة التشخيص</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">85</span>
                    <span class="stat-label">حالة تم علاجها</span>
                </div>
            </div>
        `;
    } else {
        // معلومات خاصة بالمريض
        profileStats = `
            <div class="profile-stats">
                <div class="stat-item">
                    <span class="stat-value">8</span>
                    <span class="stat-label">زيارات سابقة</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">3</span>
                    <span class="stat-label">فحوصات معلقة</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">12</span>
                    <span class="stat-label">تقارير طبية</span>
                </div>
            </div>
        `;
        
        profileDetails = `
            <div class="patient-details">
                <div class="detail-group">
                    <label>الحالة الصحية</label>
                    <p>تحت العلاج</p>
                </div>
                <div class="detail-group">
                    <label>آخر زيارة</label>
                    <p>15 يونيو 2023</p>
                </div>
                <div class="detail-group">
                    <label>الطبيب المعالج</label>
                    <p>د. محمد أحمد</p>
                </div>
            </div>
        `;
    }

    Swal.fire({
        title: 'الملف الشخصي',
        html: `
            <div class="user-profile-container">
                <div class="user-profile-header">
                    <img src="${document.querySelector('.profile img').src}" alt="صورة المستخدم" class="profile-avatar animate__animated animate__fadeIn">
                    <h3>${document.querySelector('.profile span').textContent}</h3>
                    <p class="user-role">${profileRole}</p>
                </div>
                <div class="user-details">
                    <div class="detail-group">
                        <label>البريد الإلكتروني</label>
                        <p>user@example.com</p>
                    </div>
                    <div class="detail-group">
                        <label>رقم الهاتف</label>
                        <p>+123456789</p>
                    </div>
                    <div class="detail-group">
                        <label>تاريخ الانضمام</label>
                        <p>15 يناير 2023</p>
                    </div>
                    <div class="detail-group">
                        <label>آخر تسجيل دخول</label>
                        <p>اليوم، 10:45 صباحاً</p>
                    </div>
                </div>
                ${profileDetails}
                ${profileStats}
                <div class="profile-actions">
                    <button class="btn-primary" onclick="editProfile()">تعديل الملف الشخصي</button>
                    <button class="btn-outline" onclick="changePassword()">تغيير كلمة المرور</button>
                </div>
            </div>
        `,
        width: '650px',
        confirmButtonText: 'إغلاق',
        showClass: {
            popup: 'animate__animated animate__fadeIn'
        }
    });
}

// عرض الإعدادات
function showUserSettings() {
    // الحصول على الإعدادات المحفوظة
    const userSettings = getUserSettings();
    
    Swal.fire({
        title: 'إعدادات الحساب',
        html: `
            <div class="settings-container">
                <div class="settings-section">
                    <h4>إعدادات الواجهة</h4>
                    <div class="setting-item">
                        <label for="darkMode">الوضع الليلي</label>
                        <label class="switch">
                            <input type="checkbox" id="darkMode" ${userSettings.darkMode ? 'checked' : ''}>
                            <span class="slider round"></span>
                        </label>
                    </div>
                    <div class="setting-item">
                        <label for="fontSize">حجم الخط</label>
                        <select id="fontSize" class="settings-select">
                            <option value="small" ${userSettings.fontSize === 'small' ? 'selected' : ''}>صغير</option>
                            <option value="medium" ${userSettings.fontSize === 'medium' ? 'selected' : ''}>متوسط</option>
                            <option value="large" ${userSettings.fontSize === 'large' ? 'selected' : ''}>كبير</option>
                        </select>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h4>إعدادات الإشعارات</h4>
                    <div class="setting-item">
                        <label for="emailNotifications">إشعارات البريد الإلكتروني</label>
                        <label class="switch">
                            <input type="checkbox" id="emailNotifications" ${userSettings.emailNotifications ? 'checked' : ''}>
                            <span class="slider round"></span>
                        </label>
                    </div>
                    <div class="setting-item">
                        <label for="browserNotifications">إشعارات المتصفح</label>
                        <label class="switch">
                            <input type="checkbox" id="browserNotifications" ${userSettings.browserNotifications ? 'checked' : ''}>
                            <span class="slider round"></span>
                        </label>
                    </div>
                </div>
                
                <div class="settings-section">
                    <h4>الخصوصية والأمان</h4>
                    <div class="setting-item">
                        <label for="twoFactor">المصادقة الثنائية</label>
                        <label class="switch">
                            <input type="checkbox" id="twoFactor" ${userSettings.twoFactor ? 'checked' : ''}>
                            <span class="slider round"></span>
                        </label>
                    </div>
                    <div class="setting-item">
                        <button class="btn-outline settings-btn" onclick="Swal.close(); setTimeout(function() { changePassword(); }, 300);">تغيير كلمة المرور</button>
                    </div>
                </div>
                
                <div class="settings-actions">
                    <button class="btn-primary" onclick="saveSettings()">حفظ التغييرات</button>
                    <button class="btn-secondary" onclick="resetSettings()">استعادة الإعدادات الافتراضية</button>
                </div>
            </div>
        `,
        width: '650px',
        showConfirmButton: false,
        showClass: {
            popup: 'animate__animated animate__fadeIn'
        }
    });
}

// معالجة تحميل الصورة الشخصية الجديدة والمعاينة
function uploadProfileImage(input) {
    if (input.files && input.files[0]) {
        // التحقق من نوع الملف
        const fileType = input.files[0].type;
        if (!fileType.startsWith('image/')) {
            Swal.fire({
                title: 'خطأ!',
                text: 'الرجاء تحميل صورة فقط (JPG، PNG، أو GIF)',
                icon: 'error'
            });
            return;
        }

        // حجم الملف (بالبايت) - 5 ميجابايت كحد أقصى
        const maxSize = 5 * 1024 * 1024;
        if (input.files[0].size > maxSize) {
            Swal.fire({
                title: 'خطأ!',
                text: 'حجم الصورة كبير جدًا. الحد الأقصى هو 5 ميجابايت',
                icon: 'error'
            });
            return;
        }

        // إظهار شاشة انتظار
        Swal.fire({
            title: 'جاري معالجة الصورة...',
            text: 'يرجى الانتظار',
            allowOutsideClick: false,
            showConfirmButton: false,
            willOpen: () => {
                Swal.showLoading();
            }
        });

        // قراءة الصورة وعرض المعاينة
        const reader = new FileReader();
        reader.onload = function(e) {
            // تخزين الصورة في الجلسة مباشرة (حتى قبل العثور على المعاينة)
            sessionStorage.setItem('newProfileImage', e.target.result);
            sessionStorage.setItem('profileImageChanged', 'true');
            
            // محاولة العثور على عنصر المعاينة
            const previewImg = document.getElementById('profileImagePreview');
            
            // إذا وجد عنصر المعاينة، قم بتحديثه
            if (previewImg) {
                console.log('تم العثور على عنصر معاينة الصورة');
                previewImg.src = e.target.result;
                
                // إضافة تأثير حركي للمعاينة
                previewImg.classList.add('animate__animated', 'animate__pulse');
                setTimeout(() => {
                    previewImg.classList.remove('animate__animated', 'animate__pulse');
                }, 1000);
            } else {
                console.warn('لم يتم العثور على عنصر معاينة الصورة، سيتم حفظ الصورة مباشرة.');
            }
            
            // حفظ الصورة دائماً بغض النظر عن وجود المعاينة
            const saveResult = saveProfileImageDirect(e.target.result);
            
            // تحديث جميع الصور في الصفحة
            updateAllProfileImages(e.target.result);
            
            // إغلاق شاشة الانتظار
            Swal.close();
            
            // عرض رسالة نجاح
            Swal.fire({
                title: 'تم!',
                text: saveResult ? 'تم تحميل وحفظ الصورة الشخصية بنجاح' : 'تم تحميل الصورة لكن قد تكون هناك مشكلة في الحفظ',
                icon: saveResult ? 'success' : 'warning',
                timer: 2000,
                showConfirmButton: false
            });
        };
        
        // التعامل مع أخطاء القراءة
        reader.onerror = function() {
            Swal.close();
            Swal.fire({
                title: 'خطأ!',
                text: 'حدث خطأ أثناء قراءة الصورة',
                icon: 'error'
            });
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// تحديث جميع صور الملف الشخصي في الصفحة
function updateAllProfileImages(imageSrc) {
    if (!imageSrc) return;
    
    // تحديد نوع الحساب
    const accountType = determineAccountType();
    
    // تحديث جميع الصور في الصفحة
    document.querySelectorAll('.profile img').forEach(img => {
        // إعادة تعيين السمات
        img.removeAttribute('data-profile-initialized');
        
        // تعيين السمات الجديدة
        img.setAttribute('data-account-type', accountType);
        img.src = imageSrc;
        img.setAttribute('data-profile-initialized', 'true');
        
        // إضافة تأثير حركي
        img.classList.add('animate__animated', 'animate__fadeIn');
        setTimeout(() => {
            img.classList.remove('animate__animated', 'animate__fadeIn');
        }, 1000);
    });
    
    console.log(`تم تحديث ${document.querySelectorAll('.profile img').length} صورة في الصفحة`);
}

// دالة للحفظ المباشر للصورة (تتجاوز الاعتماد على sessionStorage)
function saveProfileImageDirect(imageSrc) {
    if (!imageSrc) {
        console.error('لا توجد صورة للحفظ');
        return false;
    }
    
    try {
        // تحديد نوع الحساب
        const accountType = determineAccountType();
        console.log(`حفظ مباشر للصورة الشخصية لحساب نوع: ${accountType}`);
        
        // حفظ الصورة مباشرة في localStorage
        localStorage.setItem(`profileImage_${accountType}`, imageSrc);
        
        // حذف أي نسخة عامة من الصورة
        localStorage.removeItem('profileImage');
        
        console.log(`تم حفظ الصورة بنجاح في مفتاح: profileImage_${accountType}`);
        
        // التحقق من الحفظ
        const savedImage = localStorage.getItem(`profileImage_${accountType}`);
        if (savedImage) {
            console.log('تم التحقق من حفظ الصورة بنجاح');
            
            // طباعة جميع البيانات المخزنة في التخزين المحلي للتشخيص
            console.log('محتويات التخزين المحلي بعد الحفظ المباشر:');
            for (let i = 0; i < localStorage.length; i++) {
                const key = localStorage.key(i);
                if (key.startsWith('profileImage_')) {
                    console.log(`${key}: ${localStorage.getItem(key).substring(0, 20)}...`);
                }
            }
            
            return true;
        } else {
            console.error('فشل التحقق من حفظ الصورة');
            return false;
        }
    } catch (error) {
        console.error('حدث خطأ أثناء حفظ الصورة:', error);
        return false;
    }
}

// تعديل الملف الشخصي مع دعم تغيير الصورة الشخصية
function editProfile() {
    // الحصول على صورة المستخدم الحالية
    const currentUserImage = document.querySelector('.profile img') ? 
                             document.querySelector('.profile img').src : 
                             getDefaultProfileImage(determineAccountType());
    
    // الحصول على اسم المستخدم الحالي
    const currentUsername = document.querySelector('.profile span') ? 
                           document.querySelector('.profile span').textContent : 
                           'المستخدم';
    
    Swal.fire({
        title: 'تعديل الملف الشخصي',
        html: `
            <form id="editProfileForm">
                <div class="form-group">
                    <label for="editName">الاسم</label>
                    <input type="text" id="editName" class="swal2-input" value="${currentUsername}">
                </div>
                <div class="form-group">
                    <label for="editEmail">البريد الإلكتروني</label>
                    <input type="email" id="editEmail" class="swal2-input" value="user@example.com">
                </div>
                <div class="form-group">
                    <label for="editPhone">رقم الهاتف</label>
                    <input type="tel" id="editPhone" class="swal2-input" value="+123456789">
                </div>
                <div class="form-group">
                    <label>الصورة الشخصية</label>
                    <div class="profile-image-container">
                        <img id="profileImagePreview" src="${currentUserImage}" alt="صورة المستخدم" class="profile-image-preview">
                        <div class="profile-image-actions">
                            <label for="editAvatar" class="btn-upload-image">
                                <i class="fas fa-upload"></i> تحميل صورة
                            </label>
                            <input type="file" id="editAvatar" class="swal2-file" accept="image/*" style="display: none;" onchange="uploadProfileImage(this)">
                        </div>
                    </div>
                </div>
            </form>
        `,
        showCancelButton: true,
        confirmButtonText: 'حفظ التغييرات',
        cancelButtonText: 'إلغاء',
        customClass: {
            container: 'edit-profile-swal'
        },
        preConfirm: () => {
            return {
                name: document.getElementById('editName').value,
                email: document.getElementById('editEmail').value,
                phone: document.getElementById('editPhone').value,
                imageChanged: sessionStorage.getItem('profileImageChanged') === 'true'
            };
        },
        didOpen: () => {
            // تهيئة متغير لتتبع ما إذا تم تغيير الصورة
            sessionStorage.setItem('profileImageChanged', 'false');
            
            // تأكد من وجود عنصر معاينة الصورة
            const previewImg = document.getElementById('profileImagePreview');
            if (!previewImg) {
                console.error('لم يتم العثور على عنصر معاينة الصورة في نافذة التعديل');
            } else {
                console.log('تم العثور على عنصر معاينة الصورة في نافذة التعديل');
            }
        }
    }).then((result) => {
        if (result.isConfirmed) {
            // إذا تم تغيير الصورة، تأكد من حفظها
            if (result.value.imageChanged) {
                // هنا نضيف محاولة إضافية للحفظ عند النقر على زر الحفظ
                const saveSuccess = saveProfileImage();
                
                if (!saveSuccess) {
                    // محاولة ثانية باستخدام الدالة المباشرة
                    const imagePreview = document.getElementById('profileImagePreview');
                    if (imagePreview) {
                        saveProfileImageDirect(imagePreview.src);
                    }
                }
            }
            
            // تحديث بيانات المستخدم
            updateUsername(result.value.name);

            // حفظ الاسم في التخزين المحلي
            saveUserNameToStorage(result.value.name);
            
            Swal.fire({
                title: 'تم!',
                text: 'تم تحديث الملف الشخصي بنجاح',
                icon: 'success',
                confirmButtonText: 'حسناً',
                showClass: {
                    popup: 'animate__animated animate__fadeIn'
                }
            });
        }
        
        // إعادة تعيين المتغير
        sessionStorage.removeItem('profileImageChanged');
    });
}

// دالة لتحديث اسم المستخدم في جميع أجزاء الصفحة
function updateUsername(newName) {
    if (!newName) return;
    
    console.log(`تحديث اسم المستخدم إلى: ${newName}`);
    
    // تحديث اسم المستخدم في قائمة الملف الشخصي
    const profileNameElements = document.querySelectorAll('.profile span');
    profileNameElements.forEach(element => {
        element.textContent = newName;
    });
    
    // تحديث اسم المستخدم في ترويسة الإدارة
    const adminHeaderTitle = document.querySelector('.admin-header .header-info h1');
    if (adminHeaderTitle) {
        adminHeaderTitle.textContent = `مرحباً، ${newName}`;
        console.log(`تم تحديث اسم المستخدم في ترويسة الإدارة: ${adminHeaderTitle.textContent}`);
    } else {
        console.log('لم يتم العثور على عنصر ترويسة الإدارة');
    }
    
    // تحديث أي مكان آخر قد يظهر فيه اسم المستخدم
    const usernamePlaceholders = document.querySelectorAll('[data-username]');
    usernamePlaceholders.forEach(element => {
        element.textContent = newName;
    });
}

// دالة لحفظ اسم المستخدم في التخزين المحلي
function saveUserNameToStorage(username) {
    if (!username) return;
    
    const accountType = determineAccountType();
    localStorage.setItem(`username_${accountType}`, username);
    console.log(`تم حفظ اسم المستخدم "${username}" للحساب نوع: ${accountType}`);
}

// دالة لتحميل اسم المستخدم من التخزين المحلي
function loadUserNameFromStorage() {
    const accountType = determineAccountType();
    const savedUsername = localStorage.getItem(`username_${accountType}`);
    
    if (savedUsername) {
        console.log(`تم استرجاع اسم المستخدم "${savedUsername}" للحساب نوع: ${accountType}`);
        updateUsername(savedUsername);
        return true;
    }
    
    return false;
}

// الحصول على الصورة الافتراضية بناءً على نوع الحساب
function getDefaultProfileImage(accountType) {
    if (accountType === 'admin') {
        return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23FF5722' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E";
    } else {
        return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%234CAF50' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E";
    }
}

// إضافة مراقب لتحديث الصور عند إضافة عناصر جديدة للصفحة
function initializeObservers() {
    // إنشاء مراقب للتغييرات في DOM
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                // التحقق مما إذا تمت إضافة عناصر صورة جديدة
                const newImages = document.querySelectorAll('.profile img:not([data-profile-initialized])');
                if (newImages.length > 0) {
                    console.log('تم اكتشاف عناصر صورة جديدة، جاري تحديثها...');
                    updateProfileImages();
                }
            }
        });
    });
    
    // بدء مراقبة التغييرات في كامل الصفحة
    observer.observe(document.body, { childList: true, subtree: true });
    
    // تنفيذ وظيفة التحقق من الصور بشكل دوري
    setInterval(updateProfileImages, 2000);
}

// تهيئة كل صور الملف الشخصي في الصفحة
function initializeProfileImages() {
    console.log('جاري تهيئة صور الملف الشخصي...');
    
    // ضمان تحديد نوع الحساب أولاً
    const accountType = determineAccountType();
    console.log(`نوع الحساب الحالي: ${accountType}`);
    
    // ضمان تنفيذ بعد تحميل الصفحة بالكامل
    if (document.readyState === 'complete') {
        updateProfileImages();
        loadUserNameFromStorage(); // تحميل اسم المستخدم
        updateSidebar(); // تحديث الشريط الجانبي
    } else {
        window.addEventListener('load', function() {
            updateProfileImages();
            loadUserNameFromStorage(); // تحميل اسم المستخدم
            updateSidebar(); // تحديث الشريط الجانبي
        });
    }
    
    // محاولات متعددة لتحديث الصور بفواصل زمنية مختلفة
    setTimeout(function() {
        updateProfileImages();
        loadUserNameFromStorage(); // تحميل اسم المستخدم
        updateSidebar(); // تحديث الشريط الجانبي
    }, 500);
    
    setTimeout(function() {
        updateProfileImages();
        loadUserNameFromStorage(); // تحميل اسم المستخدم
        updateSidebar(); // تحديث الشريط الجانبي
    }, 1500);
    
    setTimeout(function() {
        updateProfileImages();
        loadUserNameFromStorage(); // تحميل اسم المستخدم
        updateSidebar(); // تحديث الشريط الجانبي
    }, 3000);
}

// تحديث جميع صور الملف الشخصي في الصفحة
function updateProfileImages() {
    // تحديد نوع الحساب بشكل دقيق
    const accountType = determineAccountType();
    
    console.log(`تحديث الصور الشخصية لحساب نوع: ${accountType}`);
    
    // الحصول على الصورة المخزنة الخاصة بنوع الحساب الحالي فقط
    let savedImage = localStorage.getItem(`profileImage_${accountType}`);
    
    // لا نستخدم النسخة العامة أو الاحتياطية في هذه الحالة إلا إذا كانت لنفس نوع الحساب
    // هذا يضمن عدم استخدام صورة الأدمن للمستخدم العادي والعكس
    
    // استخدام الصورة الافتراضية إذا لم يتم العثور على أي صورة
    if (!savedImage) {
        console.log(`لم يتم العثور على صورة مخزنة لحساب: ${accountType}، سيتم استخدام الصورة الافتراضية`);
        // يمكن هنا إضافة صورة افتراضية مختلفة لكل نوع حساب
        if (accountType === 'admin') {
            // صورة افتراضية للمسؤول - يمكن استبدالها بصورة فعلية
            savedImage = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%23FF5722' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E";
        } else {
            // صورة افتراضية للمستخدم العادي - يمكن استبدالها بصورة فعلية
            savedImage = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath fill='%234CAF50' d='M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z'/%3E%3C/svg%3E";
        }
    }
    
    // تحديث فقط صور المستخدم التي تتوافق مع نوع الحساب الحالي
    const profileImages = document.querySelectorAll('.profile img:not([data-profile-initialized])');
    
    if (profileImages.length > 0) {
        console.log(`تحديث ${profileImages.length} صورة للحساب نوع: ${accountType}`);
        
        profileImages.forEach(img => {
            // تعيين نوع الحساب كسمة للصورة لتمييزها
            img.setAttribute('data-account-type', accountType);
            
            // تعيين الصورة المحفوظة
            img.src = savedImage;
            
            // وضع علامة على الصورة لتجنب تحديثها مرة أخرى
            img.setAttribute('data-profile-initialized', 'true');
            
            // تسجيل نجاح أو فشل تحميل الصورة
            img.onload = function() {
                console.log(`تم تحميل الصورة الشخصية لحساب: ${accountType} بنجاح`);
                // إضافة تأثير حركي خفيف
                img.classList.add('animate__animated', 'animate__fadeIn');
                setTimeout(() => {
                    img.classList.remove('animate__animated', 'animate__fadeIn');
                }, 1000);
            };
            
            img.onerror = function() {
                console.error(`حدثت مشكلة في تحميل الصورة الشخصية لحساب: ${accountType}`);
                // إزالة العلامة للسماح بمحاولة أخرى
                img.removeAttribute('data-profile-initialized');
            };
        });
        
        console.log(`تم تحديث صور المستخدم بنجاح لحساب نوع: ${accountType}`);
    }
}

// حفظ وتحديث الصورة الشخصية في واجهة المستخدم وفي التخزين المحلي
function saveProfileImage() {
    console.log('بدء تنفيذ وظيفة حفظ الصورة الشخصية...');
    const newImageSrc = sessionStorage.getItem('newProfileImage');
    if (!newImageSrc) {
        console.error('لم يتم العثور على صورة جديدة للحفظ في sessionStorage');
        return false;
    }
    
    try {
        // تحديد نوع الحساب الحالي بدقة
        const accountType = determineAccountType();
        console.log(`حفظ صورة جديدة لحساب نوع: ${accountType}`);
        
        // حفظ الصورة فقط تحت مفتاح خاص بنوع الحساب الحالي
        localStorage.setItem(`profileImage_${accountType}`, newImageSrc);
        
        // حذف أي نسخة عامة من الصورة لتجنب التداخل
        localStorage.removeItem('profileImage');
        
        console.log(`تم حفظ الصورة الشخصية بنجاح لحساب: ${accountType}`);
        
        // تحديث جميع الصور المرتبطة بنوع الحساب الحالي في الصفحة
        document.querySelectorAll('.profile img').forEach(img => {
            // إعادة تعيين السمات لضمان تحديث الصورة في المرة القادمة إذا كانت تنتمي لنوع حساب مختلف
            img.removeAttribute('data-profile-initialized');
            
            // تعيين نوع الحساب وتحديث الصورة
            img.setAttribute('data-account-type', accountType);
            img.src = newImageSrc;
            
            // وضع علامة على الصورة بعد تحديثها
            img.setAttribute('data-profile-initialized', 'true');
            
            // إضافة تأثير حركي
            img.classList.add('animate__animated', 'animate__fadeIn');
            setTimeout(() => {
                img.classList.remove('animate__animated', 'animate__fadeIn');
            }, 1000);
        });
        
        // طباعة جميع البيانات المخزنة في التخزين المحلي للتشخيص
        console.log('محتويات التخزين المحلي بعد الحفظ:');
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            if (key.startsWith('profileImage_')) {
                console.log(`${key}: ${localStorage.getItem(key).substring(0, 20)}...`);
            }
        }
        
        // إخلاء التخزين المؤقت للجلسة
        sessionStorage.removeItem('newProfileImage');
        sessionStorage.removeItem('profileImageChanged');
        
        return true; // إشارة إلى نجاح العملية
    } catch (error) {
        console.error('حدث خطأ أثناء حفظ الصورة الشخصية:', error);
        return false;
    }
}

// تحديد نوع الحساب بدقة (مدير أو مستخدم)
function determineAccountType() {
    // 1. التحقق من URL الحالي - وهي الطريقة الأكثر موثوقية
    if (window.location.pathname.includes('admin')) {
        console.log('تم تحديد نوع الحساب: admin (استناداً إلى URL)');
        return 'admin';
    }
    
    // 2. التحقق من العناصر الخاصة بلوحة التحكم في الصفحة
    const adminDashboardLinks = document.querySelectorAll('a[href*="admin_dashboard"], a[href*="admin/dashboard"]');
    const adminManageUsersLinks = document.querySelectorAll('a[href*="manage_users"], a[href*="users/manage"]');
    const adminPanel = document.querySelector('.admin-panel, #adminPanel, [data-role="admin"]');
    
    if (adminDashboardLinks.length > 0 || adminManageUsersLinks.length > 0 || adminPanel) {
        console.log('تم تحديد نوع الحساب: admin (استناداً إلى روابط لوحة التحكم)');
        return 'admin';
    }
    
    // 3. التحقق من نص الروابط في القائمة الجانبية
    const adminKeywords = ['لوحة التحكم', 'إدارة المستخدمين', 'لوحة الادارة', 'مدير النظام', 'الإدارة', 'المشرف'];
    const sidebarLinks = document.querySelectorAll('.nav-links a, .sidebar a');
    
    for (let link of sidebarLinks) {
        const linkText = link.textContent.trim();
        for (let keyword of adminKeywords) {
            if (linkText.includes(keyword)) {
                console.log(`تم تحديد نوع الحساب: admin (استناداً إلى الكلمة المفتاحية: ${keyword})`);
                return 'admin';
            }
        }
    }
    
    // 4. التحقق من وجود عناصر خاصة بالإدارة بناءً على الأيقونات
    const adminIcons = document.querySelectorAll('i.fa-user-shield, i.fa-users-cog, i.fa-user-cog');
    if (adminIcons.length > 0) {
        console.log('تم تحديد نوع الحساب: admin (استناداً إلى أيقونات الإدارة)');
        return 'admin';
    }
    
    console.log('تم تحديد نوع الحساب: user (الإعداد الافتراضي)');
    return 'user'; // في حالة عدم التأكد، الافتراض بأن الحساب هو مستخدم عادي
}

// تحميل الصورة الشخصية من التخزين المحلي (دالة احتياطية للتوافق الخلفي)
function loadProfileImageFromStorage() {
    updateProfileImages();
}

// تغيير كلمة المرور
function changePassword() {
    Swal.fire({
        title: 'تغيير كلمة المرور',
        html: `
            <form id="changePasswordForm">
                <div class="form-group">
                    <label for="currentPassword">كلمة المرور الحالية</label>
                    <input type="password" id="currentPassword" class="swal2-input" placeholder="كلمة المرور الحالية">
                </div>
                <div class="form-group">
                    <label for="newPassword">كلمة المرور الجديدة</label>
                    <input type="password" id="newPassword" class="swal2-input" placeholder="كلمة المرور الجديدة">
                </div>
                <div class="form-group">
                    <label for="confirmPassword">تأكيد كلمة المرور</label>
                    <input type="password" id="confirmPassword" class="swal2-input" placeholder="تأكيد كلمة المرور">
                </div>
            </form>
        `,
        confirmButtonText: 'تغيير كلمة المرور',
        showCancelButton: true,
        cancelButtonText: 'إلغاء',
        preConfirm: () => {
            const newPassword = document.getElementById('newPassword').value;
            const confirmPassword = document.getElementById('confirmPassword').value;
            
            if (newPassword !== confirmPassword) {
                Swal.showValidationMessage('كلمتا المرور غير متطابقتين');
                return false;
            }
            
            return true;
        }
    }).then((result) => {
        if (result.isConfirmed) {
            Swal.fire({
                title: 'تم!',
                text: 'تم تغيير كلمة المرور بنجاح',
                icon: 'success',
                confirmButtonText: 'حسناً'
            });
        }
    });
}

// حفظ إعدادات المستخدم
function saveSettings() {
    const settings = {
        darkMode: document.getElementById('darkMode').checked,
        fontSize: document.getElementById('fontSize').value,
        emailNotifications: document.getElementById('emailNotifications').checked,
        browserNotifications: document.getElementById('browserNotifications').checked,
        twoFactor: document.getElementById('twoFactor').checked
    };
    
    // تحديد نوع الحساب
    const accountType = determineAccountType();
    
    // حفظ الإعدادات في التخزين المحلي باستخدام مفتاح خاص بنوع الحساب
    localStorage.setItem(`userSettings_${accountType}`, JSON.stringify(settings));
    
    // تطبيق الإعدادات على الصفحة
    applyThemeSettings(settings);
    
    console.log(`تم حفظ إعدادات حساب: ${accountType}`);
    
    Swal.fire({
        title: 'جارِ الحفظ...',
        text: 'يتم حفظ الإعدادات الجديدة',
        timer: 1500,
        timerProgressBar: true,
        didOpen: () => {
            Swal.showLoading();
        }
    }).then(() => {
        Swal.fire({
            title: 'تم!',
            text: 'تم حفظ الإعدادات بنجاح',
            icon: 'success',
            confirmButtonText: 'حسناً',
            showClass: {
                popup: 'animate__animated animate__fadeIn'
            }
        });
    });
}

// استعادة الإعدادات الافتراضية
function resetSettings() {
    Swal.fire({
        title: 'هل أنت متأكد؟',
        text: 'سيتم استعادة جميع الإعدادات إلى الوضع الافتراضي',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'نعم، استعادة',
        cancelButtonText: 'إلغاء'
    }).then((result) => {
        if (result.isConfirmed) {
            // إعادة تعيين الإعدادات إلى القيم الافتراضية
            const defaultSettings = {
                darkMode: false,
                fontSize: 'medium',
                emailNotifications: true,
                browserNotifications: true,
                twoFactor: false
            };
            
            // تحديد نوع الحساب
            const accountType = determineAccountType();
            
            // حفظ الإعدادات الافتراضية
            localStorage.setItem(`userSettings_${accountType}`, JSON.stringify(defaultSettings));
            
            // تطبيق الإعدادات الافتراضية
            applyThemeSettings(defaultSettings);
            
            // إعادة تحميل نافذة الإعدادات لتعكس التغييرات
            setTimeout(() => showUserSettings(), 300);
            
            Swal.fire({
                title: 'تم!',
                text: 'تمت استعادة الإعدادات الافتراضية',
                icon: 'success',
                confirmButtonText: 'حسناً'
            });
        }
    });
}

// الحصول على إعدادات المستخدم المحفوظة
function getUserSettings() {
    // الإعدادات الافتراضية
    const defaultSettings = {
        darkMode: false,
        fontSize: 'medium',
        emailNotifications: true,
        browserNotifications: true,
        twoFactor: false
    };
    
    // تحديد نوع الحساب لاسترجاع الإعدادات المناسبة
    const accountType = determineAccountType();
    
    // محاولة استرداد الإعدادات المحفوظة
    const savedSettings = localStorage.getItem(`userSettings_${accountType}`);
    
    if (savedSettings) {
        try {
            return JSON.parse(savedSettings);
        } catch (error) {
            console.error('خطأ في تحليل إعدادات المستخدم:', error);
            return defaultSettings;
        }
    }
    
    return defaultSettings;
}

// تطبيق إعدادات المستخدم على الصفحة
function applyUserSettings() {
    const settings = getUserSettings();
    applyThemeSettings(settings);
}

// تطبيق إعدادات السمة (الوضع الليلي وحجم الخط)
function applyThemeSettings(settings) {
    // تطبيق الوضع الليلي
    if (settings.darkMode) {
        document.body.classList.add('dark-mode');
    } else {
        document.body.classList.remove('dark-mode');
    }
    
    // تطبيق حجم الخط
    document.body.classList.remove('font-small', 'font-medium', 'font-large');
    document.body.classList.add(`font-${settings.fontSize}`);
}

// إضافة دالة لتحديث السايد بار وإضافة رابط الرسائل
function updateSidebar() {
    // تحديد نوع الحساب
    const accountType = determineAccountType();
    console.log(`تحديث السايد بار لحساب نوع: ${accountType}`);
    
    // البحث عن السايد بار
    const sidebar = document.querySelector('.sidebar-menu, .nav-links, .sidebar');
    
    if (!sidebar) {
        console.error('لم يتم العثور على القائمة الجانبية');
        return;
    }
    
    // التحقق ما إذا كان رابط الرسائل موجوداً بالفعل
    const existingMessagesLink = document.querySelector('.sidebar-menu a[href="/messages"], .nav-links a[href="/messages"], .sidebar a[href="/messages"]');
    
    if (existingMessagesLink) {
        console.log('رابط الرسائل موجود بالفعل في القائمة الجانبية');
        return;
    }
    
    // إنشاء رابط الرسائل
    const messagesLink = document.createElement('a');
    messagesLink.href = '/messages';
    
    // تخصيص الأيقونة والنص بناءً على نوع الحساب
    if (accountType === 'admin') {
        // رابط للطبيب/المدير
        messagesLink.innerHTML = `
            <i class="fas fa-comment-dots"></i>
            <span>الرسائل الطبية</span>
        `;
    } else {
        // رابط للمريض
        messagesLink.innerHTML = `
            <i class="fas fa-comment-dots"></i>
            <span>التواصل مع الطبيب</span>
        `;
    }
    
    // إنشاء عنصر li إذا كانت القائمة تستخدم ul/li
    const listItem = document.createElement('li');
    listItem.appendChild(messagesLink);
    
    // محاكاة نمط الروابط الحالية - نحتاج أن نفعل هذا قبل إضافة الرابط إلى DOM
    const existingLinks = sidebar.querySelectorAll('a');
    if (existingLinks.length > 0) {
        // نسخ الكلاسات من رابط موجود
        const sampleLink = existingLinks[0];
        const linkClasses = sampleLink.getAttribute('class');
        if (linkClasses) {
            messagesLink.setAttribute('class', linkClasses);
        }
    }
    
    // العثور على رابط تسجيل الخروج
    const logoutLink = findLogoutLink(sidebar);
    
    if (logoutLink) {
        // إضافة الرابط قبل رابط تسجيل الخروج
        if (sidebar.tagName === 'UL') {
            // إذا كان logoutLink في li
            const logoutLi = logoutLink.closest('li');
            if (logoutLi && logoutLi.parentNode) {
                logoutLi.parentNode.insertBefore(listItem, logoutLi);
                console.log('تمت إضافة رابط الرسائل قبل تسجيل الخروج في قائمة UL');
            } else {
                sidebar.appendChild(listItem);
                console.log('تمت إضافة رابط الرسائل إلى نهاية قائمة UL (لم يتم العثور على تسجيل الخروج)');
            }
        } else {
            if (logoutLink.parentNode) {
                logoutLink.parentNode.insertBefore(messagesLink, logoutLink);
                console.log('تمت إضافة رابط الرسائل قبل تسجيل الخروج مباشرة');
            } else {
                sidebar.appendChild(messagesLink);
                console.log('تمت إضافة رابط الرسائل إلى نهاية السايد بار (لم يتم العثور على تسجيل الخروج)');
            }
        }
    } else {
        // إذا لم يتم العثور على رابط تسجيل الخروج، أضف الرابط إلى نهاية السايد بار
        if (sidebar.tagName === 'UL') {
            sidebar.appendChild(listItem);
            console.log('تمت إضافة رابط الرسائل إلى نهاية قائمة UL');
        } else if (sidebar.classList.contains('nav-links') || sidebar.classList.contains('sidebar-menu') || sidebar.classList.contains('sidebar')) {
            sidebar.appendChild(messagesLink);
            console.log('تمت إضافة رابط الرسائل إلى نهاية السايد بار');
        }
    }
    
    // إضافة event listener للرابط
    messagesLink.addEventListener('click', function(e) {
        if (!this.getAttribute('href').startsWith('http')) {
            e.preventDefault();
            window.location.href = '/messages';
        }
    });
    
    console.log(`تمت إضافة رابط الرسائل بنجاح للحساب نوع: ${accountType}`);
}

// العثور على رابط تسجيل الخروج في السايد بار
function findLogoutLink(sidebar) {
    // البحث باستخدام النص العربي
    const logoutLinks = Array.from(sidebar.querySelectorAll('a')).filter(link => {
        const linkText = link.textContent.trim().toLowerCase();
        return linkText.includes('تسجيل الخروج') || 
               linkText.includes('خروج') || 
               linkText.includes('logout') ||
               link.querySelector('i.fa-sign-out-alt') ||
               link.querySelector('i.fa-sign-out') ||
               link.querySelector('i.fa-power-off');
    });
    
    if (logoutLinks.length > 0) {
        return logoutLinks[0];
    }
    
    // البحث عن آخر رابط في السايد بار (غالبًا ما يكون تسجيل الخروج)
    const allLinks = sidebar.querySelectorAll('a');
    if (allLinks.length > 0) {
        return allLinks[allLinks.length - 1];
    }
    
    return null;
} 