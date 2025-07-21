
# Product Analysis Tool

This is a Django-based web tool that allows uploading CSV files and generates product tier and two-word descriptions using AI. The tool tracks progress and stores configuration data for a superuser.

---

## Features

- Upload CSV files containing company data
- Generate product tiers and descriptions using OpenAI
- Track processing progress for each user
- Store and retrieve superuser-specific configuration

---

## Prerequisites

- Python 3.8+
- pip (Python package installer)
- virtualenv (optional but recommended)

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/devwahed/dealflow_automator
````

### 2. Create and activate virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install requirements

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

Follow the prompts to create a superuser account. This is required for saving and retrieving configuration data.

### 6. Start the development server

```bash
python manage.py runserver
```

Visit [http://localhost:8000](http://localhost:8000) to access the application.

---

## Notes

* The tool uses OpenAI APIs to generate content. Make sure you have your API key configured properly in your environment or settings.
* A progress tracking JSON file is created per user in a dedicated progress directory.

---
