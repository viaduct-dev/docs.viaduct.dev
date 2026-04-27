#!/usr/bin/env python3
"""
Append a dynamically generated nav to docs/mkdocs.yml.

Reads the upstream nav via git (before overlays replaced mkdocs.yml),
extracts the Documentation section children, fixes paths flattened by
the build, appends the KDocs section, and writes nav YAML to the end
of the already-applied overlay mkdocs.yml.
"""
import subprocess
import sys
import yaml

# Custom loader: silently handles !ENV and !!python/name: tags
class PermissiveLoader(yaml.SafeLoader):
    pass

def _unknown(loader, tag_suffix, node):
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node, deep=True)
    return loader.construct_mapping(node, deep=True)

PermissiveLoader.add_multi_constructor('', _unknown)

# Read upstream nav from git (pre-overlay version of mkdocs.yml)
raw = subprocess.check_output(['git', 'show', 'HEAD:docs/mkdocs.yml']).decode()
upstream = yaml.load(raw, Loader=PermissiveLoader)

# Extract Documentation section children we want at the top level
KEEP = {'Getting Started', 'Developers', 'Service Engineers', 'Contributors'}
doc_nav = []
for item in upstream.get('nav', []):
    if isinstance(item, dict) and 'Documentation' in item:
        for sub in item['Documentation']:
            if isinstance(sub, dict) and next(iter(sub)) in KEEP:
                doc_nav.append(sub)

if not doc_nav:
    print("patch-mkdocs.py: ERROR — no Documentation section found in upstream nav", file=sys.stderr)
    sys.exit(1)

# Fix paths to match the flatten step:
#   docs/developers/  -> developers/
#   docs/service_engineers/ -> service_engineers/
#   docs/contributors/ -> contributors/
FIXES = {
    'docs/developers/': 'developers/',
    'docs/service_engineers/': 'service_engineers/',
    'docs/contributors/': 'contributors/',
}

def fix_path(s):
    for old, new in FIXES.items():
        s = s.replace(old, new)
    return s

def fix_nav(items):
    out = []
    for item in items:
        if isinstance(item, str):
            out.append(fix_path(item))
        elif isinstance(item, dict):
            out.append({
                k: fix_nav(v) if isinstance(v, list) else fix_path(v) if isinstance(v, str) else v
                for k, v in item.items()
            })
    return out

nav = fix_nav(doc_nav) + [{'KDocs': [
    'kdocs/index.md',
    {'Tenant API': 'https://docs.viaduct.dev/apis/tenant-api/'},
    {'Service API': 'https://docs.viaduct.dev/apis/service/'},
]}]

nav_yaml = yaml.dump({'nav': nav}, default_flow_style=False, allow_unicode=True)

with open('docs/mkdocs.yml', 'a') as f:
    f.write('\n')
    f.write(nav_yaml)

print(f"patch-mkdocs.py: nav generated ({len(nav)} top-level sections)")
