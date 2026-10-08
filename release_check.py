"""Check a complete release without loading credentials or starting workers."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re

from jinja2 import Environment, FileSystemLoader, TemplateError, meta


def check_release(root=None, strict=False):
    root = Path(root or Path(__file__).parent)
    problems, warnings = [], []
    required = {'flask':'Flask', 'requests':'requests', 'waitress':'waitress', 'PIL':'Pillow', 'tzdata':'tzdata'}
    for module, package in required.items():
        if importlib.util.find_spec(module) is None:
            problems.append('Missing dependency: '+package+'. Install requirements.txt.')
    modules = list(root.glob('*.py'))
    for source in modules:
        try:
            tree = ast.parse(source.read_text(encoding='utf-8'), filename=source.name)
            compile(tree, source.name, 'exec')
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and not node.level:
                    name = node.module.split('.')[0]
                    if importlib.util.find_spec(name) is None and not (root/(name+'.py')).is_file():
                        problems.append(source.name+' imports missing module '+name)
        except (SyntaxError, UnicodeError) as exc:
            problems.append(source.name+': '+type(exc).__name__)
    environment = Environment(loader=FileSystemLoader(root/'templates'))
    for name in environment.list_templates():
        try:
            text = (root/'templates'/name).read_text(encoding='utf-8')
            tree = environment.parse(text)
            for reference in meta.find_referenced_templates(tree):
                if reference and not (root/'templates'/reference).is_file():
                    problems.append(name+' requires missing template '+reference)
            for asset in re.findall(r"filename\s*=\s*['\"]([^'\"]+)['\"]", text):
                if not (root/'static'/asset).is_file():
                    problems.append(name+' requires missing static/'+asset)
        except (UnicodeError, ValueError, TemplateError) as exc:
            problems.append(name+': '+type(exc).__name__)
    manifest = root/'BUILD_MANIFEST.json'
    if manifest.is_file():
        spec = json.loads(manifest.read_text(encoding='utf-8'))
        for name, expected in spec.get('files', {}).items():
            path = root/name
            if not path.is_file():
                problems.append('Missing release file: '+name)
            elif hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                (problems if strict else warnings).append('File differs from packaged release: '+name)
    if not (root/'templates/index.html').is_file() or not (root/'templates/admin.html').is_file():
        problems.append('The templates folder is incomplete.')
    return dict(ok=not problems, problems=sorted(set(problems)), warnings=sorted(set(warnings)),
                python_modules=len(modules), templates=len(environment.list_templates()))
