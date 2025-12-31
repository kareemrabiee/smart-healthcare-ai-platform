// إضافة الرسوم البيانية
function initCharts() {
    const diagnosisCtx = document.getElementById('diagnosisChart');
    const activityCtx = document.getElementById('activityChart');

    // تدمير الرسوم البيانية القديمة إذا وجدت
    if (window.diagnosisChart instanceof Chart) {
        window.diagnosisChart.destroy();
    }
    if (window.activityChart instanceof Chart) {
        window.activityChart.destroy();
    }

    if (diagnosisCtx) {
        window.diagnosisChart = new Chart(diagnosisCtx, {
            type: 'doughnut',
            data: {
                labels: ['طبيعي', 'مشتبه به', 'قرنية مخروطية'],
                datasets: [{
                    data: [65, 25, 10],
                    backgroundColor: [
                        'rgba(14, 165, 233, 0.8)',
                        'rgba(2, 132, 199, 0.8)',
                        'rgba(3, 105, 161, 0.8)'
                    ],
                    borderColor: [
                        'rgba(14, 165, 233, 1)',
                        'rgba(2, 132, 199, 1)',
                        'rgba(3, 105, 161, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                family: 'Tajawal'
                            }
                        }
                    }
                }
            }
        });
    }

    if (activityCtx) {
        window.activityChart = new Chart(activityCtx, {
            type: 'line',
            data: {
                labels: ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو'],
                datasets: [{
                    label: 'عدد الفحوصات',
                    data: [12, 19, 15, 25, 22, 30],
                    borderColor: 'rgba(37, 99, 235, 1)',
                    backgroundColor: 'rgba(37, 99, 235, 0.1)',
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            font: {
                                family: 'Tajawal'
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(0, 0, 0, 0.05)'
                        },
                        ticks: {
                            font: {
                                family: 'Tajawal'
                            }
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            font: {
                                family: 'Tajawal'
                            }
                        }
                    }
                }
            }
        });
    }
}

// نظام الإشعارات المباشرة
function initNotifications() {
    const notificationBtn = document.querySelector('.notifications-btn');
    const notificationsDropdown = document.querySelector('.notifications-dropdown');
    
    if (notificationBtn && notificationsDropdown) {
        notificationBtn.addEventListener('click', () => {
            notificationsDropdown.classList.toggle('show');
        });
        
        document.addEventListener('click', (e) => {
            if (!notificationBtn.contains(e.target) && !notificationsDropdown.contains(e.target)) {
                notificationsDropdown.classList.remove('show');
            }
        });
    }
}

// تحسين تجربة المستخدم في المراسلات
function enhanceMessaging() {
    const messageInput = document.querySelector('.message-input');
    const messagePreview = document.querySelector('.message-preview');
    
    if (messageInput && messagePreview) {
        messageInput.addEventListener('input', () => {
            messagePreview.innerHTML = marked(messageInput.value);
        });
    }
}

// تحسين عرض الصور
function enhanceImageViews() {
    const diagnosisImages = document.querySelectorAll('.diagnosis-image');
    
    diagnosisImages.forEach(img => {
        img.addEventListener('click', () => {
            Swal.fire({
                imageUrl: img.src,
                imageAlt: 'صورة التشخيص',
                width: '80%',
                showConfirmButton: false
            });
        });
    });
}

// تفعيل القائمة الجانبية للموبايل
function initMobileMenu() {
    const menuBtn = document.querySelector('.menu-btn');
    const sidebar = document.querySelector('.sidebar');
    
    if (menuBtn && sidebar) {
        menuBtn.addEventListener('click', () => {
            sidebar.classList.toggle('show');
        });
    }
}

// تهيئة جميع المميزات عند تحميل الصفحة
document.addEventListener('DOMContentLoaded', () => {
    // تأكد من وجود العناصر قبل تنفيذ الدوال
    if (document.querySelector('.admin-dashboard')) {
        setTimeout(initCharts, 100); // تأخير قليل لضمان تحميل العناصر
    }
    
    const notificationBtn = document.querySelector('.notifications-btn');
    const notificationsDropdown = document.querySelector('.notifications-dropdown');
    if (notificationBtn && notificationsDropdown) {
        initNotifications();
    }

    const messageInput = document.querySelector('.message-input');
    if (messageInput) {
        enhanceMessaging();
    }

    const diagnosisImages = document.querySelectorAll('.diagnosis-image');
    if (diagnosisImages.length) {
        enhanceImageViews();
    }

    const menuBtn = document.querySelector('.menu-btn');
    const sidebar = document.querySelector('.sidebar');
    if (menuBtn && sidebar) {
        initMobileMenu();
    }
}); 