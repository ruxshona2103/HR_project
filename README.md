# 🚀 HR Management System

A scalable and production-ready HR (Human Resources) management platform designed to automate recruitment workflows, manage company structures, and streamline candidate evaluation.

---

## 📖 Project Overview

This project is a full-featured HR system where:

- Companies can create and manage job vacancies
- Candidates can register, build profiles, and apply for jobs
- Recruiters can review applications and manage hiring pipelines
- AI Interview Simulation System (Simulates HR interview scenarios and evaluates candidates)

The system is built with scalability and clean architecture in mind, following RESTful API standards.

---

## 🧠 Business Logic

### 👤 Candidate Flow
1. User registers via phone number (OTP verification)
2. Completes profile (skills, experience, CV)
3. Browses job listings
4. Applies to jobs
5. Tracks application status
6. AI Interview Simulation

### 🏢 Company Flow
1. Company registers and creates profile
2. Posts job vacancies
3. Reviews candidates
4. Accepts / Rejects applications

---

## 🏗 System Architecture

The project follows a modular architecture:

- **Users App** → authentication, roles (candidate / recruiter)
- **Companies App** → company profiles & management
- **Jobs App** → job postings & applications
- **Common Services** → utilities, permissions, validations

---

## 🔐 Authentication & Security

- Phone-based authentication (OTP)
- Token-based authorization (JWT / DRF Tokens)
- Role-based access control (RBAC)
- Secure password handling & validation

---

## 🤖 AI HR Mocking System

An intelligent simulation system that mimics real HR interview scenarios.

### Features:
- 🎤 Simulated interview questions
- 🧠 AI-based response evaluation
- 📊 Candidate scoring system
- 💬 Feedback generation for improvement

### Goal:
To help candidates practice interviews and improve their communication and technical skills before applying to real jobs.

---

## 🛠 Tech Stack

### Backend
- Python 🐍
- Django
- Django REST Framework

### Frontend
- (React / Vue / HTML — update this)

### Database
- PostgreSQL

### Tools
- Git & GitHub
- Docker (optional)
- Postman (API testing)

---

## 📊 API Design Principles

- RESTful structure
- Clear endpoint naming
- Separation of concerns
- Validation & error handling

Example:

- GET /api/jobs/
- POST /api/jobs/
- GET /api/jobs/{id}/
- POST /api/apply/

---

## ⚙️ Installation

```bash
git clone https://github.com/your-username/hr-project.git
cd hr-project

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```
---

## 📂 Project Structure

```
hr-project/
│
├── apps/
│   ├── choose_roles/
│   ├── landing_page/
│   ├── profile/
│   ├── user_profile/
│   ├── users1/
│   ├── vacancies/
│
├── config/
├── manage.py
└── requirements.txt
```

---

## 🔄 Workflow Diagram (Concept)
```
Candidate → Apply → Job → Company → Decision
        ↘ status tracking ↙
```

---

## 🧪 Testing

```
python manage.py test
```

---

## 🚀 Future Improvements

- 🤖 AI-based candidate-job matching
- 🔔 Real-time notifications (WebSockets)
- 📱 Mobile application
- 📊 Advanced analytics dashboard
- 🌍 Multi-language support
- 🤖 AI Interview Simulation with real-time feedback

---

## ⚡ Performance & Scalability

- Optimized database queries
- Pagination for large datasets
- Ready for microservices transition
- Caching (Redis — future plan)

---

## 🤝 Contributing

Contributions are welcome! Feel free to fork and submit a pull request.

---

## 📜 License

MIT License

