# Task Management System

## Overview
**Task Management System** is a web application designed to help teams manage projects and tasks efficiently. It allows users to create, assign, and track tasks within various projects, facilitating collaboration and improving productivity.

## Features
- **User Authentication**: Sign up, log in, and manage user profiles.
- **Role Management**: Differentiate between Project Managers and Team Members.
- **Project Management**: Create and manage projects with team assignments.
- **Task Management**: Create, assign, and track tasks with due dates and priorities.
- **Time Tracking**: Log time spent on tasks for better productivity analysis.
- **File Attachments**: Upload and manage files related to tasks.
- **Comments**: Collaborate with team members through comments on tasks.
- **Dashboard**: Overview of assigned tasks and managed projects.

## Technology Stack
- **Backend**: Django (Python)
- **Frontend**: HTML, CSS, JavaScript (with frameworks like Bootstrap)
- **Database**: PostgreSQL

## Installation

### Prerequisites
- Python 3.8 or higher
- Django 5.1.5
- PostgreSQL
- pip (Python package installer) 



**Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3*Install dependencies**:
     pip install -r requirements.txt
  

**Set up the database**:
   - Create a PostgreSQL database and user.
   - Update the `DATABASES` setting in `task_management/settings.py` with your database credentials.
   I have provided backup file for the database in the project folder.

**Set up email**:
   - Install `django.core.mail` and `django.core.mail.backends.smtp.EmailBackend` in your `settings.py` file.
   - Create an email account for sending emails from your application.
   - Update the `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER

**Run migrations**:
   ```bash
   python manage.py migrate
   ```

**Create a superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

**Run the development server**:
   ```bash
   python manage.py runserver
   ```

**Access the application**:
   Open your web browser and go to `http://127.0.0.1:8000/`.

## Usage
- **Sign Up**: Create a new account to start using the application.
- **Log In**: Access your dashboard to view assigned tasks and managed projects.
- **Create Projects**: Project Managers can create and manage projects.
- **Create Tasks**: Assign tasks to team members and track their progress.
- **Log Time**: Track the time spent on tasks for better management.

