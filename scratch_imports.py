import os
import re

base = r"C:\Users\ardcr\Desktop\EcoFleetExpress\core\views"

def add_imports(filename, new_imports):
    path = os.path.join(base, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # insert after the last import or from statement
    lines = content.split('\n')
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i
            
    lines.insert(last_import_idx + 1, new_imports)
    
    with open(path, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))

add_imports('attendance.py', 'from core.models import ToolRun\nfrom django.contrib import messages\nfrom django.conf import settings')
add_imports('btpl.py', 'from core.models import ToolRun\nfrom django.contrib import messages\nfrom django.conf import settings')
add_imports('ftl.py', 'from core.models import ToolRun\nfrom django.contrib import messages\nfrom django.conf import settings')
add_imports('cof.py', 'from core.models import ToolRun\nfrom django.contrib import messages\nfrom django.conf import settings')
add_imports('portal_views.py', 'from django.contrib import messages')
add_imports('common.py', 'from core.models import ToolRunFile\nfrom django.core.files.base import ContentFile')
add_imports('morning.py', 'import datetime\nfrom core.models import ToolRunFile\nfrom django.core.files.base import ContentFile')
add_imports('prev_month.py', 'import datetime\nfrom core.models import ToolRunFile\nfrom django.core.files.base import ContentFile')
add_imports('pendency.py', 'from django.http import Http404')

print("Imports added.")
