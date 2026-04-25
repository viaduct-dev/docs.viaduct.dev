#!/usr/bin/env python3
"""
Append a dynamically generated nav to docs/mkdocs.yml.

Reads the upstream nav via git (before overlays replaced mkdocs.yml),
extracts the Documentation section children, fixes paths flattened by
the build, appends the KDocs section, and writes nav YAML to the end
of the already-applied overlay mkdocs.yml.

Also promotes the Getting Started index page to the site root (index.md)
so that docs.viaduct.dev/ serves the Getting Started landing page directly.
"""
import os
import shutil
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

# Promote the Getting Started index page to the site root so that
# docs.viaduct.dev/ serves the Getting Started landing page directly.
# The Getting Started nav entry will link to / (index.md) rather than
# /getting_started/.

def gs_index_path(section_value):
    """Return the index page path for a nav section value (str or list)."""
    if isinstance(section_value, str):
        return section_value
    if isinstance(section_value, list):
        for item in section_value:
            if isinstance(item, str):
                return item
            if isinstance(item, dict):
                v = next(iter(item.values()))
                if isinstance(v, str):
                    return v
    return None

def remap_first(items, old_path, new_path):
    """Replace first occurrence of old_path with new_path in nav tree.

    Returns (new_items, found).
    """
    out = []
    found = False
    for item in items:
        if found:
            out.append(item)
            continue
        if isinstance(item, str):
            if item == old_path:
                out.append(new_path)
                found = True
            else:
                out.append(item)
        elif isinstance(item, dict):
            new_dict = {}
            for k, v in item.items():
                if found:
                    new_dict[k] = v
                elif isinstance(v, str):
                    if v == old_path:
                        new_dict[k] = new_path
                        found = True
                    else:
                        new_dict[k] = v
                elif isinstance(v, list):
                    new_v, sub_found = remap_first(v, old_path, new_path)
                    new_dict[k] = new_v
                    if sub_found:
                        found = True
                else:
                    new_dict[k] = v
            out.append(new_dict)
        else:
            out.append(item)
    return out, found

gs_path = None
for item in nav:
    if isinstance(item, dict) and 'Getting Started' in item:
        gs_path = gs_index_path(item['Getting Started'])
        break

if gs_path and gs_path != 'index.md':
    src = f'docs/docs/{gs_path}'
    dst = 'docs/docs/index.md'
    if os.path.exists(src):
        shutil.copy2(src, dst)
        nav, remapped = remap_first(nav, gs_path, 'index.md')
        if remapped:
            print(f"patch-mkdocs.py: promoted {gs_path} -> index.md")
        else:
            print(f"patch-mkdocs.py: WARNING — could not remap {gs_path} in nav", file=sys.stderr)
    else:
        print(f"patch-mkdocs.py: WARNING — {src} not found, root index unchanged", file=sys.stderr)

nav_yaml = yaml.dump({'nav': nav}, default_flow_style=False, allow_unicode=True)

with open('docs/mkdocs.yml', 'a') as f:
    f.write('\n')
    f.write(nav_yaml)

print(f"patch-mkdocs.py: nav generated ({len(nav)} top-level sections)")
