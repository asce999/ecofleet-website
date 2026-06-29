import os

base = r"C:\Users\ardcr\Desktop\EcoFleetExpress\core\views"

def add_imports(filename, new_imports):
    path = os.path.join(base, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split('\n')
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i
    lines.insert(last_import_idx + 1, new_imports)
    with open(path, "w", encoding="utf-8") as f:
        f.write('\n'.join(lines))

add_imports('common.py', 'import os\nfrom django.shortcuts import redirect')

def remove_unused(filename, strings_to_remove):
    path = os.path.join(base, filename)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    lines = content.split('\n')
    new_lines = []
    for line in lines:
        keep = True
        for s in strings_to_remove:
            if s in line:
                keep = False
                break
        if keep:
            new_lines.append(line)
    with open(path, "w", encoding="utf-8") as f:
        f.write('\n'.join(new_lines))

# For ftl.py we can just use replace:
with open(os.path.join(base, 'ftl.py'), 'r', encoding='utf-8') as f:
    ftl = f.read()
ftl = ftl.replace("from django.shortcuts import render, redirect, get_object_or_404", "from django.shortcuts import render, redirect")
ftl = ftl.replace("from django.http import FileResponse, Http404, JsonResponse", "from django.http import FileResponse, Http404")
ftl = ftl.replace("import json\n", "")
with open(os.path.join(base, 'ftl.py'), 'w', encoding='utf-8') as f:
    f.write(ftl)

# pendency.py
with open(os.path.join(base, 'pendency.py'), 'r', encoding='utf-8') as f:
    p = f.read()
p = p.replace("from django.http import FileResponse, Http404\n", "from django.http import Http404\n")
p = p.replace("import datetime\n", "")
with open(os.path.join(base, 'pendency.py'), 'w', encoding='utf-8') as f:
    f.write(p)

# portal_views.py
with open(os.path.join(base, 'portal_views.py'), 'r', encoding='utf-8') as f:
    pv = f.read()
pv = pv.replace("from django.db.models import Sum, Q", "from django.db.models import Sum")
pv = pv.replace("from core.models import ToolRun, ToolRunFile", "from core.models import ToolRun")
with open(os.path.join(base, 'portal_views.py'), 'w', encoding='utf-8') as f:
    f.write(pv)
    
print("Cleaned up remaining issues.")
