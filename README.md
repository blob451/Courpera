# Courpera

Courpera is a server‑rendered e‑learning web application built with Django. It provides user accounts (students and teachers), course authoring and enrolment, materials upload, course feedback, status updates, notifications, search, and real‑time messaging.

Key Features
- User accounts and roles (students/teachers)
- Courses and enrolments with role‑based access
- Materials upload with server‑side validation
- Course feedback (rating and comments) and status updates
- Notifications (recent popover and full list)
- Search for people and courses
- Real‑time messaging via WebSockets (course rooms and direct messages)
- REST API with OpenAPI documentation

Technology Stack
- Python and Django (server‑rendered templates and forms)
- Django REST Framework (versioned REST API)
- drf‑spectacular (OpenAPI/Swagger/Redoc)
- Django Channels + Redis (WebSockets)
- SQLite by default; WhiteNoise for static files
- Optional enhancements: HTMX for progressive enhancement, DiceBear avatars, Google reCAPTCHA v3 on registration, and iCalendar (ICS) export for events

Design & Accessibility
- Accessible, semantic HTML with a lightweight design system (CSS tokens and base styles)
