# Smart Healthcare AI-Enhanced Patient Care Platform

An AI-powered healthcare web application designed to assist in the early detection of **Keratoconus** using deep learning, while also providing smart patient management and secure doctor-patient interaction.

This project was developed as a **Graduation Project** at the Faculty of Computers & Artificial Intelligence.

---

## Project Overview

The Smart Healthcare AI Platform aims to improve healthcare efficiency by combining:
- Artificial Intelligence for medical image analysis
- Secure web-based patient management
- Doctor-assisted diagnosis and reporting

The system focuses on analyzing corneal topography images to support doctors in detecting keratoconus with high accuracy.

---

## Key Features

-  AI-based Keratoconus detection from corneal images  
-  User authentication (Patients / Doctors / Admin)  
-  Medical data visualization and diagnosis reports  
-  Secure messaging between patients and doctors  
-  Role-Based Access Control (RBAC)  
-  Downloadable diagnostic reports  

---

## AI Model Details

- Architecture: **MobileNetV2 (Transfer Learning)**
- Framework: TensorFlow / Keras
- Input Size: 96×96 RGB images
- Accuracy: **93.2%**
- Sensitivity: **95.2%**
- Specificity: **91.2%**

The model analyzes corneal images and extracts medical features to assist in clinical decision-making.

---

## Tech Stack

### Backend
- Python
- Flask
- Flask-Login
- SQLAlchemy

### AI & Machine Learning
- TensorFlow
- Keras
- NumPy

### Frontend
- HTML5
- CSS3
- JavaScript
- Bootstrap

### Database
- SQLite

---

## How to Run the Project Locally

```bash
# Clone the repository
git clone https://github.com/kareemrabiee/smart-healthcare-ai-platform.git

# Navigate to the project folder
cd smart-healthcare-ai-platform

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
