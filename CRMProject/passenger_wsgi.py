import sys, os

# 1️⃣ Path to your Django project folder
project_home = '/home/mediama2/crm_project'  # <-- adjust to your actual path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 2️⃣ Set Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'CRMProject.settings'  # <-- replace with your project.settings

# 3️⃣ Activate virtual environment
venv_path = '/home/mediama2/crm_project/venv/bin/activate_this.py'  # <-- adjust if your venv path is different
with open(venv_path) as f:
    exec(f.read(), {'__file__': venv_path})

# 4️⃣ Get WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
