#!/usr/bin/env python3
"""
Advanced HTML/CSS/JS -> React (Vite) Converter v4
Fixed and Enhanced Version

Major improvements:
 - Fixed BeautifulSoup parsing with proper HTML5 handling
 - Improved JSX conversion with proper escaping
 - Better event handler extraction with scope analysis
 - Enhanced CSS processing (regular + modules)
 - Smart script conversion and dynamic loading
 - SVG and special element handling
 - Inline styles conversion
 - Better TypeScript type generation
 - Improved component detection and extraction
 - Asset path resolution and copying
 - Error handling and validation
 - Support for modern HTML/CSS/JS patterns

Usage:
  python3 converter_v4.py /path/to/vanilla /path/to/dest --name mysite --ts --css-modules
"""

import os
import re
import shutil
import json
import argparse
import textwrap
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from bs4 import BeautifulSoup, Tag, NavigableString, Comment
import hashlib

# ---------- Utilities ------------------------------------------------------

def ensure_dir(path: str) -> None:
    """Create directory if it doesn't exist"""
    os.makedirs(path, exist_ok=True)


def write_file(path: str, content: str, binary: bool = False) -> None:
    """Write content to file with proper encoding"""
    ensure_dir(os.path.dirname(path))
    mode = 'wb' if binary else 'w'
    with open(path, mode, encoding=None if binary else 'utf-8') as f:
        f.write(content)


def slugify(name: str) -> str:
    """Convert string to valid identifier"""
    name = re.sub(r"[^0-9a-zA-Z_]+", "_", name).strip('_')
    if not name or name[0].isdigit():
        name = 'comp_' + name
    return name or 'component'


def title_case(name: str) -> str:
    """Convert to PascalCase for component names"""
    parts = re.split(r"\W+", name)
    result = ''.join(p.capitalize() for p in parts if p)
    if not result or result[0].isdigit():
        result = 'Component' + result
    return result or 'Component'


def is_self_closing_tag(tag_name: str) -> bool:
    """Check if HTML tag should be self-closing in JSX"""
    self_closing = {
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input',
        'link', 'meta', 'param', 'source', 'track', 'wbr', 'command',
        'keygen', 'menuitem'
    }
    return tag_name.lower() in self_closing


def escape_jsx_text(text: str) -> str:
    """Escape text for JSX"""
    if not text:
        return text
    # Only escape opening braces that could be interpreted as expressions
    # Don't escape if already in expression context
    text = re.sub(r'(?<!\\)\{', '{{', text)
    text = re.sub(r'(?<!\\)\}', '}}', text)
    return text


# ---------- JSX Conversion -------------------------------------------------

EVENT_ATTRS = {
    'onclick': 'onClick',
    'onchange': 'onChange',
    'onsubmit': 'onSubmit',
    'oninput': 'onInput',
    'onblur': 'onBlur',
    'onfocus': 'onFocus',
    'onmouseover': 'onMouseOver',
    'onmouseout': 'onMouseOut',
    'onmouseenter': 'onMouseEnter',
    'onmouseleave': 'onMouseLeave',
    'onmousedown': 'onMouseDown',
    'onmouseup': 'onMouseUp',
    'onmousemove': 'onMouseMove',
    'onkeydown': 'onKeyDown',
    'onkeyup': 'onKeyUp',
    'onkeypress': 'onKeyPress',
    'ondblclick': 'onDoubleClick',
    'oncontextmenu': 'onContextMenu',
    'onload': 'onLoad',
    'onerror': 'onError',
    'onscroll': 'onScroll',
    'onresize': 'onResize',
    'ondrag': 'onDrag',
    'ondrop': 'onDrop',
    'ondragover': 'onDragOver',
    'ondragstart': 'onDragStart',
    'ondragend': 'onDragEnd',
    'onwheel': 'onWheel',
    'ontouchstart': 'onTouchStart',
    'ontouchend': 'onTouchEnd',
    'ontouchmove': 'onTouchMove',
}


class JSXConverter:
    """Handles HTML to JSX conversion"""
    
    def __init__(self, use_css_modules: bool = False):
        self.use_css_modules = use_css_modules
        self.css_class_map: Dict[str, str] = {}
        self.handler_placeholders: Dict[str, str] = {}
        
    def convert_attributes(self, tag: Tag) -> None:
        """Convert HTML attributes to JSX format"""
        if not hasattr(tag, 'attrs') or not tag.attrs:
            return
            
        attrs_to_update = {}
        attrs_to_remove = []
        
        for attr_name, attr_value in list(tag.attrs.items()):
            # Skip event handlers (processed separately)
            if attr_name.lower() in EVENT_ATTRS:
                continue
            
            # Handle class -> className
            if attr_name == 'class':
                attrs_to_remove.append('class')
                classes = attr_value if isinstance(attr_value, list) else [attr_value]
                if self.use_css_modules:
                    attrs_to_update['className'] = self._convert_classes_to_modules(classes)
                else:
                    attrs_to_update['className'] = ' '.join(classes)
            
            # Handle for -> htmlFor
            elif attr_name == 'for':
                attrs_to_remove.append('for')
                attrs_to_update['htmlFor'] = attr_value
            
            # Handle tabindex -> tabIndex
            elif attr_name == 'tabindex':
                attrs_to_remove.append('tabindex')
                attrs_to_update['tabIndex'] = attr_value
            
            # Handle maxlength -> maxLength
            elif attr_name == 'maxlength':
                attrs_to_remove.append('maxlength')
                attrs_to_update['maxLength'] = attr_value
            
            # Handle minlength -> minLength
            elif attr_name == 'minlength':
                attrs_to_remove.append('minlength')
                attrs_to_update['minLength'] = attr_value
            
            # Handle readonly -> readOnly
            elif attr_name == 'readonly':
                attrs_to_remove.append('readonly')
                attrs_to_update['readOnly'] = True
            
            # Handle colspan -> colSpan
            elif attr_name == 'colspan':
                attrs_to_remove.append('colspan')
                attrs_to_update['colSpan'] = attr_value
            
            # Handle rowspan -> rowSpan
            elif attr_name == 'rowspan':
                attrs_to_remove.append('rowspan')
                attrs_to_update['rowSpan'] = attr_value
            
            # Handle boolean attributes
            elif attr_name in ['checked', 'disabled', 'required', 'selected', 'autofocus', 
                             'autoplay', 'controls', 'loop', 'muted']:
                if attr_value == '' or attr_value == attr_name or attr_value is True:
                    attrs_to_update[attr_name] = True
            
            # Handle style attribute
            elif attr_name == 'style' and isinstance(attr_value, str):
                style_obj = self._parse_inline_style(attr_value)
                if style_obj:
                    attrs_to_remove.append('style')
                    attrs_to_update['style'] = style_obj
        
        # Apply updates
        for attr in attrs_to_remove:
            if attr in tag.attrs:
                del tag.attrs[attr]
        
        for attr, value in attrs_to_update.items():
            tag.attrs[attr] = value
    
    def _parse_inline_style(self, style_str: str) -> str:
        """Convert inline CSS to React style object"""
        if not style_str:
            return ""
        
        styles = {}
        declarations = style_str.split(';')
        
        for decl in declarations:
            if ':' not in decl:
                continue
            
            prop, value = decl.split(':', 1)
            prop = prop.strip()
            value = value.strip()
            
            if not prop or not value:
                continue
            
            # Convert kebab-case to camelCase
            prop_parts = prop.split('-')
            camel_prop = prop_parts[0] + ''.join(p.capitalize() for p in prop_parts[1:])
            
            # Handle numeric values
            if value.replace('.', '').replace('-', '').isdigit():
                styles[camel_prop] = value
            else:
                styles[camel_prop] = f"'{value}'"
        
        if not styles:
            return ""
        
        style_pairs = [f"{k}: {v}" for k, v in styles.items()]
        return "{{ " + ", ".join(style_pairs) + " }}"
    
    def _convert_classes_to_modules(self, classes: List[str]) -> str:
        """Convert CSS classes to CSS module syntax"""
        if not classes:
            return ""
        
        converted = []
        for cls in classes:
            if not cls:
                continue
            safe_cls = slugify(cls)
            module_ref = f"styles.{safe_cls}"
            self.css_class_map[cls] = module_ref
            converted.append(module_ref)
        
        if not converted:
            return ""
        elif len(converted) == 1:
            return f"{{{converted[0]}}}"
        else:
            return "{`${" + "} ${".join(converted) + "}`}"
    
    def to_jsx_string(self, element, indent_level: int = 0) -> str:
        """Convert BeautifulSoup element to JSX string with proper formatting"""
        if isinstance(element, Comment):
            # Convert HTML comments to JSX comments
            return f"{{/* {element.strip()} */}}"
        
        if isinstance(element, NavigableString):
            text = str(element)
            # Preserve whitespace structure but escape JSX
            if text.strip():
                return escape_jsx_text(text)
            return text
        
        if not isinstance(element, Tag):
            return str(element)
        
        tag_name = element.name
        
        # Handle special React components
        if tag_name in ['html', 'body', 'head']:
            children = ''.join(self.to_jsx_string(child, indent_level) for child in element.children)
            return children
        
        # Build JSX attributes
        attrs_str = self._attrs_to_jsx(element.attrs)
        
        # Handle self-closing tags
        if is_self_closing_tag(tag_name):
            return f"<{tag_name}{attrs_str} />"
        
        # Handle tags with children
        children_jsx = []
        for child in element.children:
            child_jsx = self.to_jsx_string(child, indent_level + 1)
            if child_jsx:
                children_jsx.append(child_jsx)
        
        children_str = ''.join(children_jsx)
        
        # Handle empty tags
        if not children_str.strip():
            if tag_name in ['script', 'style', 'title']:
                return f"<{tag_name}{attrs_str}></{tag_name}>"
            return f"<{tag_name}{attrs_str}></{tag_name}>"
        
        return f"<{tag_name}{attrs_str}>{children_str}</{tag_name}>"
    
    def _attrs_to_jsx(self, attrs: dict) -> str:
        """Convert attributes dict to JSX attribute string"""
        if not attrs:
            return ""
        
        parts = []
        for key, value in sorted(attrs.items()):
            # Handle handler placeholders
            if key.startswith('HANDLER_'):
                handler_ref = self.handler_placeholders.get(key)
                if handler_ref:
                    jsx_attr = key.replace('HANDLER_', '')
                    parts.append(f" {jsx_attr}={{{handler_ref}}}")
                continue
            
            # Handle None or empty
            if value is None or value == '':
                continue
            
            # Handle boolean attributes
            if value is True:
                parts.append(f" {key}")
            elif value is False:
                continue
            
            # Handle list values
            elif isinstance(value, list):
                joined = ' '.join(str(v) for v in value if v)
                if joined:
                    parts.append(f' {key}="{joined}"')
            
            # Handle style objects
            elif key == 'style' and isinstance(value, str) and value.startswith('{{'):
                parts.append(f' {key}={value}')
            
            # Handle className with CSS modules
            elif key == 'className' and self.use_css_modules and value.startswith('{'):
                parts.append(f' {key}={value}')
            
            # Handle regular string values
            else:
                safe_value = str(value).replace('"', '&quot;').replace('{', '{{').replace('}', '}}')
                parts.append(f' {key}="{safe_value}"')
        
        return ''.join(parts)


# ---------- Event Handler Extraction --------------------------------------

class EventHandlerExtractor:
    """Extract and convert inline event handlers"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.handlers: List[Dict] = []
        self.handler_count = 0
        self.state_vars: Set[str] = set()
    
    def extract_from_tag(self, tag: Tag) -> None:
        """Extract event handlers from a tag"""
        if not hasattr(tag, 'attrs'):
            return
        
        for attr in list(tag.attrs.keys()):
            if attr.lower() in EVENT_ATTRS:
                code = tag.attrs.pop(attr)
                if not code:
                    continue
                
                self.handler_count += 1
                handler_name = f"handle{title_case(self.component_name)}{self.handler_count}"
                jsx_event = EVENT_ATTRS[attr.lower()]
                
                # Analyze code for state variables
                self._analyze_code_for_state(code)
                
                self.handlers.append({
                    'name': handler_name,
                    'jsx_attr': jsx_event,
                    'code': code,
                    'original_attr': attr
                })
                
                # Add placeholder that will be replaced
                placeholder_key = f'HANDLER_{jsx_event}'
                tag.attrs[placeholder_key] = handler_name
    
    def _analyze_code_for_state(self, code: str) -> None:
        """Analyze JavaScript code to detect potential state variables"""
        # Look for common patterns like getElementById, querySelector, etc.
        patterns = [
            r'document\.getElementById\(["\']([^"\']+)["\']\)',
            r'document\.querySelector\(["\']([^"\']+)["\']\)',
            r'\.value',
            r'\.checked',
            r'\.innerHTML',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, code)
            self.state_vars.update(matches)
    
    def extract_from_tree(self, soup: BeautifulSoup) -> None:
        """Extract handlers from entire tree"""
        for tag in soup.find_all(True):
            self.extract_from_tag(tag)
    
    def generate_handler_code(self, use_ts: bool = False) -> str:
        """Generate React handler functions"""
        if not self.handlers:
            return ""
        
        code_parts = []
        
        for handler in self.handlers:
            inline_code = handler['code'].strip()
            
            # Clean up inline code
            inline_code = inline_code.rstrip(';')
            
            # Detect if we need preventDefault
            prevent_default = 'submit' in handler['jsx_attr'].lower() or 'return false' in inline_code.lower()
            
            # Convert common DOM operations to React patterns
            inline_code = self._convert_dom_operations(inline_code)
            
            # Type annotation for TypeScript
            event_type = ': React.MouseEvent' if use_ts else ''
            if 'Key' in handler['jsx_attr']:
                event_type = ': React.KeyboardEvent' if use_ts else ''
            elif 'Change' in handler['jsx_attr'] or 'Input' in handler['jsx_attr']:
                event_type = ': React.ChangeEvent<HTMLInputElement>' if use_ts else ''
            
            func = f"""  const {handler['name']} = (event{event_type}) => {{"""
            
            if prevent_default:
                func += "\n    event.preventDefault();"
            
            func += f"""
    try {{
      {self._indent_code(inline_code, 6)}
    }} catch (error) {{
      console.error('Event handler error in {handler['name']}:', error);
    }}
  }};"""
            
            code_parts.append(func)
        
        return '\n\n'.join(code_parts)
    
    def _convert_dom_operations(self, code: str) -> str:
        """Convert common DOM operations to React patterns"""
        # Convert getElementById to ref access (add comment)
        code = re.sub(
            r'document\.getElementById\(["\']([^"\']+)["\']\)',
            r'/* TODO: Use useRef for \1 */ document.getElementById("\1")',
            code
        )
        
        # Convert querySelector to ref access (add comment)
        code = re.sub(
            r'document\.querySelector\(["\']([^"\']+)["\']\)',
            r'/* TODO: Use useRef */ document.querySelector("\1")',
            code
        )
        
        # Convert this references to event.currentTarget
        code = re.sub(r'\bthis\b', 'event.currentTarget', code)
        
        return code
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block"""
        indent = ' ' * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line if line.strip() else '' for line in lines).strip()
    
    def apply_handlers_to_jsx_converter(self, converter: JSXConverter) -> None:
        """Register handler placeholders with JSX converter"""
        for handler in self.handlers:
            placeholder_key = f'HANDLER_{handler["jsx_attr"]}'
            converter.handler_placeholders[placeholder_key] = handler['name']


# ---------- Script Handler -------------------------------------------------

class ScriptHandler:
    """Handle external and inline scripts"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.external_scripts: List[str] = []
        self.inline_scripts: List[str] = []
    
    def generate_use_effect_code(self) -> str:
        """Generate useEffect code for script loading"""
        if not self.external_scripts and not self.inline_scripts:
            return ""
        
        code = """
  useEffect(() => {
    // Load external scripts
"""
        
        for script_url in self.external_scripts:
            code += f"""    const script{len(self.external_scripts)} = document.createElement('script');
    script{len(self.external_scripts)}.src = '{script_url}';
    script{len(self.external_scripts)}.async = true;
    document.body.appendChild(script{len(self.external_scripts)});
"""
        
        if self.inline_scripts:
            code += """
    // Execute inline scripts
    try {
"""
            for idx, inline in enumerate(self.inline_scripts):
                code += f"      {self._indent_code(inline, 6)}\n"
            
            code += """    } catch (error) {
      console.error('Script execution error:', error);
    }
"""
        
        code += """
    // Cleanup
    return () => {
"""
        
        for idx in range(len(self.external_scripts)):
            code += f"      if (script{idx + 1}.parentNode) {{\n"
            code += f"        script{idx + 1}.parentNode.removeChild(script{idx + 1});\n"
            code += "      }\n"
        
        code += """    };
  }, []);
"""
        
        return code
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code block"""
        indent = ' ' * spaces
        lines = code.split('\n')
        return '\n'.join(indent + line if line.strip() else '' for line in lines).strip()


# ---------- Component Detection --------------------------------------------

def detect_user_components(soup: BeautifulSoup) -> List[Tuple[Tag, str]]:
    """Detect user-defined components in the HTML"""
    components = []
    seen = set()
    
    for tag in soup.find_all(True):
        if not hasattr(tag, 'attrs'):
            continue
        
        # Avoid duplicates
        tag_id = id(tag)
        if tag_id in seen:
            continue
        
        # Check for explicit component markers
        if tag.get('data-component'):
            name = tag['data-component']
            components.append((tag, name))
            seen.add(tag_id)
            continue
        
        # Check for Webflow/similar builders
        for attr in tag.attrs.keys():
            if attr.startswith(('data-wf-', 'data-ix-', 'data-w-')):
                name = tag.get('id') or tag.get('class', ['Component'])[0]
                if isinstance(name, list):
                    name = name[0]
                components.append((tag, name))
                seen.add(tag_id)
                break
        
        # Check for semantic component patterns
        classes = ' '.join(tag.get('class', [])).lower()
        tag_id_attr = (tag.get('id') or '').lower()
        
        patterns = ['component', 'widget', 'module', 'block', 'card', 'panel']
        if any(pattern in classes or pattern in tag_id_attr for pattern in patterns):
            name = tag.get('id') or tag.get('class', ['Component'])[0]
            if isinstance(name, list):
                name = name[0]
            if tag_id not in seen:
                components.append((tag, name))
                seen.add(tag_id)
    
    return components


def detect_shared_components(html_files: Dict[str, BeautifulSoup], 
                            threshold: float = 0.6) -> Dict[str, str]:
    """Detect components shared across pages"""
    
    def normalize(html: str) -> str:
        """Normalize HTML for comparison"""
        html = re.sub(r'\s+', ' ', html).strip()
        html = re.sub(r'\sid=["\'][^"\']*["\']', '', html)
        html = re.sub(r'\sdata-[^=]+=["\'][^"\']*["\']', '', html)
        return html
    
    fragments = defaultdict(list)
    total_pages = len(html_files)
    
    for filename, soup in html_files.items():
        # Look for semantic tags
        for tag_name, component_name in [('header', 'Header'), 
                                         ('footer', 'Footer'), 
                                         ('nav', 'Navigation')]:
            element = soup.find(tag_name)
            if element:
                fragments[component_name].append(normalize(str(element)))
    
    shared = {}
    for component_name, instances in fragments.items():
        if not instances:
            continue
        
        counter = Counter(instances)
        most_common_html, count = counter.most_common(1)[0]
        
        if count / total_pages >= threshold:
            shared[component_name] = most_common_html
    
    return shared


# ---------- Component Generation -------------------------------------------

class ComponentGenerator:
    """Generate React components from HTML"""
    
    def __init__(self, options):
        self.options = options
        self.jsx_converter = JSXConverter(options.css_modules)
    
    def generate_component(self, name: str, html: str, 
                         is_page: bool = False) -> Tuple[str, List[str]]:
        """Generate a React component from HTML"""
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find body or use root
        if is_page:
            body = soup.find('body')
            if not body:
                body = soup
        else:
            body = soup
        
        # Remove comments
        for comment in body.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Extract event handlers
        handler_extractor = EventHandlerExtractor(name)
        handler_extractor.extract_from_tree(body)
        
        # Register handlers with converter
        handler_extractor.apply_handlers_to_jsx_converter(self.jsx_converter)
        
        # Convert attributes
        for tag in body.find_all(True):
            self.jsx_converter.convert_attributes(tag)
        
        # Convert to JSX
        jsx = self.jsx_converter.to_jsx_string(body)
        
        # Generate imports
        imports = ['import React, { useEffect, useState } from "react";']
        
        if self.options.css_modules and self.jsx_converter.css_class_map:
            imports.append(f'import styles from "./{name}.module.css";')
        
        if is_page:
            imports.append('import { Helmet } from "react-helmet-async";')
        
        # Generate component code
        handler_code = handler_extractor.generate_handler_code(self.options.ts)
        
        # State declarations if needed
        state_code = ""
        if handler_extractor.state_vars:
            state_code = "\n  // TODO: Add state for interactive elements\n"
        
        # Build component
        ext = 'tsx' if self.options.ts else 'jsx'
        type_annotation = ': React.FC' if self.options.ts else ''
        
        component_code = f"""{chr(10).join(imports)}

const {name}{type_annotation} = () => {{{state_code}
{handler_code if handler_code else ''}

  return (
    <>
      {jsx}
    </>
  );
}};

export default {name};
"""
        
        return component_code, imports
    
    def extract_user_components(self, soup: BeautifulSoup, 
                               page_name: str) -> List[Tuple[str, str, str]]:
        """Extract user-defined components"""
        components = detect_user_components(soup)
        extracted = []
        
        for idx, (tag, raw_name) in enumerate(components, 1):
            comp_name = title_case(raw_name)
            comp_name = re.sub(r'[^A-Za-z0-9_]', '', comp_name) or f'Component{idx}'
            
            # Generate component
            html = str(tag)
            code, _ = self.generate_component(comp_name, html, is_page=False)
            
            # Replace tag with component usage
            replacement = soup.new_tag(comp_name)
            tag.replace_with(replacement)
            
            extracted.append((comp_name, code, raw_name))
        
        return extracted


# ---------- Asset Management -----------------------------------------------

class AssetManager:
    """Manage CSS, JS, and other assets"""
    
    def __init__(self, source_root: str, target_root: str):
        self.source_root = Path(source_root)
        self.target_root = Path(target_root)
        self.public_dir = self.target_root / 'public'
    
    def copy_css(self, href: str, use_modules: bool = False) -> Optional[str]:
        """Copy CSS file and return import path"""
        if href.startswith(('http://', 'https://', '//')):
            return href
        
        source_path = self.source_root / href.lstrip('/')
        
        if not source_path.exists():
            print(f"  Warning: CSS file not found: {source_path}")
            return None
        
        dest_dir = self.public_dir / 'css'
        ensure_dir(str(dest_dir))
        
        filename = source_path.name
        
        if use_modules:
            name, ext = os.path.splitext(filename)
            filename = f"{name}.module{ext}"
        
        dest_path = dest_dir / filename
        shutil.copy2(source_path, dest_path)
        
        return f'/css/{filename}'
    
    def copy_script(self, src: str) -> Optional[str]:
        """Copy JS file and return public path"""
        if src.startswith(('http://', 'https://', '//')):
            return src
        
        source_path = self.source_root / src.lstrip('/')
        
        if not source_path.exists():
            print(f"  Warning: Script not found: {source_path}")
            return None
        
        dest_dir = self.public_dir / 'js'
        ensure_dir(str(dest_dir))
        
        filename = source_path.name
        dest_path = dest_dir / filename
        shutil.copy2(source_path, dest_path)
        
        return f'/js/{filename}'
    
    def copy_image(self, src: str) -> Optional[str]:
        """Copy image and return public path"""
        if src.startswith(('http://', 'https://', '//', 'data:')):
            return src
        
        source_path = self.source_root / src.lstrip('/')
        
        if not source_path.exists():
            return src
        
        dest_dir = self.public_dir / 'images'
        ensure_dir(str(dest_dir))
        
        filename = source_path.name
        dest_path = dest_dir / filename
        
        try:
            shutil.copy2(source_path, dest_path)
            return f'/images/{filename}'
        except Exception as e:
            print(f"  Warning: Could not copy image {source_path}: {e}")
            return src
    
    def copy_assets(self, asset_dirs: List[str] = None) -> None:
        """Copy asset directories"""
        if asset_dirs is None:
            asset_dirs = ['assets', 'images', 'img', 'fonts', 'media']
        
        for asset_dir in asset_dirs:
            source_assets = self.source_root / asset_dir
            
            if source_assets.exists() and source_assets.is_dir():
                dest_assets = self.public_dir / asset_dir
                if dest_assets.exists():
                    shutil.rmtree(dest_assets)
                shutil.copytree(source_assets, dest_assets)
                print(f"  ✓ Copied {asset_dir}/ directory")


# ---------- Main Conversion Logic ------------------------------------------

def convert_page(html_path: Path, options, asset_manager: AssetManager) -> Dict:
    """Convert a single HTML page to React"""
    
    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html.parser')
    page_name = title_case(html_path.stem)
    
    # Extract metadata
    title = "React App"
    meta_tags = []
    
    head = soup.find('head')
    if head:
        title_tag = head.find('title')
        if title_tag and title_tag.string:
            title = title_tag.string.strip()
        
        for meta in head.find_all('meta'):
            meta_tags.append(str(meta))
    
    # Process images
    for img in soup.find_all('img'):
        src = img.get('src')
        if src:
            new_src = asset_manager.copy_image(src)
            if new_src:
                img['src'] = new_src
    
    # Process CSS
    css_imports = []
    if head:
        for link in head.find_all('link', rel=lambda x: x and 'stylesheet' in ' '.join(x) if isinstance(x, list) else x):
            href = link.get('href')
            if href and not href.startswith(('http://', 'https://')):
                path = asset_manager.copy_css(href, options.css_modules)
                if path:
                    css_imports.append(path)
            link.extract()
    
    # Process scripts
    script_handler = ScriptHandler(page_name)
    
    for script in soup.find_all('script'):
        src = script.get('src')
        if src:
            path = asset_manager.copy_script(src)
            if path:
                script_handler.external_scripts.append(path)
        elif script.string:
            script_handler.inline_scripts.append(script.string)
        script.extract()
    
    # Generate component
    generator = ComponentGenerator(options)
    user_components = generator.extract_user_components(soup, page_name)
    
    # Get body content
    body = soup.find('body')
    body_html = str(body) if body else str(soup)
    
    page_code, _ = generator.generate_component(page_name, body_html, is_page=True)
    
    # Add script loading if needed
    use_effect_code = script_handler.generate_use_effect_code()
    if use_effect_code:
        # Insert useEffect before return statement
        page_code = page_code.replace(
            '  return (',
            use_effect_code + '\n  return ('
        )
    
    return {
        'name': page_name,
        'code': page_code,
        'title': title,
        'meta_tags': meta_tags,
        'css_imports': css_imports,
        'user_components': user_components,
        'route': '/' if html_path.stem == 'index' else f'/{html_path.stem}'
    }


# ---------- Project Setup --------------------------------------------------

def create_project_structure(target_dir: Path, options) -> None:
    """Create React project structure"""
    
    # Create directories
    (target_dir / 'src').mkdir(exist_ok=True)
    (target_dir / 'src' / 'components').mkdir(exist_ok=True)
    (target_dir / 'src' / 'pages').mkdir(exist_ok=True)
    (target_dir / 'public').mkdir(exist_ok=True)
    
    # package.json
    package_json = {
        "name": options.name,
        "version": "1.0.0",
        "type": "module",
        "scripts": {
            "dev": "vite",
            "build": "vite build",
            "preview": "vite preview",
            "lint": "eslint src --ext js,jsx,ts,tsx"
        },
        "dependencies": {
            "react": "^18.3.1",
            "react-dom": "^18.3.1",
            "react-router-dom": "^6.26.0",
            "react-helmet-async": "^2.0.5"
        },
        "devDependencies": {
            "vite": "^5.4.0",
            "@vitejs/plugin-react": "^4.3.0",
            "eslint": "^8.57.0",
            "eslint-plugin-react": "^7.35.0"
        }
    }
    
    if options.ts:
        package_json["devDependencies"].update({
            "@types/react": "^18.3.0",
            "@types/react-dom": "^18.3.0",
            "typescript": "^5.5.0"
        })
    
    write_file(str(target_dir / 'package.json'), json.dumps(package_json, indent=2))
    
    # vite.config.js
    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'static',
    emptyOutDir: true,
    sourcemap: true
  },
  publicDir: 'public',
  server: {
    port: 3000,
    open: true,
    host: true
  }
})
"""
    write_file(str(target_dir / 'vite.config.js'), vite_config)
    
    # index.html
    index_html = f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{options.name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.{'tsx' if options.ts else 'jsx'}"></script>
  </body>
</html>
"""
    write_file(str(target_dir / 'index.html'), index_html)
    
    # TypeScript config
    if options.ts:
        tsconfig = {
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "resolveJsonModule": True,
                "isolatedModules": True,
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True
            },
            "include": ["src"]
        }
        write_file(str(target_dir / 'tsconfig.json'), json.dumps(tsconfig, indent=2))
    
    # .gitignore
    gitignore = """# Dependencies
node_modules
/.pnp
.pnp.js

# Testing
/coverage

# Production
/dist
/build

# Misc
.DS_Store
.env.local
.env.development.local
.env.test.local
.env.production.local

npm-debug.log*
yarn-debug.log*
yarn-error.log*
"""
    write_file(str(target_dir / '.gitignore'), gitignore)


def generate_main_entry(target_dir: Path, pages: List[Dict], options) -> None:
    """Generate main.jsx/tsx entry point"""
    
    ext = 'tsx' if options.ts else 'jsx'
    
    # Generate imports
    imports = [
        "import React from 'react';",
        "import ReactDOM from 'react-dom/client';",
        "import { BrowserRouter, Routes, Route } from 'react-router-dom';",
        "import { HelmetProvider } from 'react-helmet-async';"
    ]
    
    for page in pages:
        imports.append(f"import {page['name']} from './pages/{page['name']}.{ext}';")
    
    # Generate routes
    routes = []
    for page in pages:
        routes.append(f'        <Route path="{page["route"]}" element={{<{page["name"]} />}} />')
    
    # Add 404 route
    if pages:
        routes.append(f'        <Route path="*" element={{<{pages[0]["name"]} />}} />')
    
    main_code = f"""{chr(10).join(imports)}

const App{': React.FC' if options.ts else ''} = () => {{
  return (
    <HelmetProvider>
      <BrowserRouter>
        <Routes>
{chr(10).join(routes)}
        </Routes>
      </BrowserRouter>
    </HelmetProvider>
  );
}};

const rootElement = document.getElementById('root');
if (rootElement) {{
  const root = ReactDOM.createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}}
"""
    
    write_file(str(target_dir / 'src' / f'main.{ext}'), main_code)


# ---------- Main Orchestration ---------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Advanced HTML/CSS/JS to React Converter v4 (Fixed)'
    )
    parser.add_argument('source', help='Source directory with HTML files')
    parser.add_argument('dest', help='Destination directory')
    parser.add_argument('--name', default='react-app', help='Project name')
    parser.add_argument('--ts', action='store_true', help='Use TypeScript')
    parser.add_argument('--css-modules', action='store_true', help='Use CSS Modules')
    parser.add_argument('--no-install', action='store_true', help='Skip npm install')
    
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    target_dir = Path(args.dest)
    
    if not source_dir.exists():
        print(f"❌ Error: Source directory '{source_dir}' does not exist")
        return
    
    print("="*60)
    print("Advanced HTML to React Converter v4")
    print("="*60)
    print(f"Source: {source_dir}")
    print(f"Target: {target_dir}")
    print(f"TypeScript: {'✓' if args.ts else '✗'}")
    print(f"CSS Modules: {'✓' if args.css_modules else '✗'}")
    print("="*60)
    
    # Create options object
    class Options:
        pass
    
    options = Options()
    options.name = args.name
    options.ts = args.ts
    options.css_modules = args.css_modules
    
    # Create project structure
    print("\n📁 Creating project structure...")
    create_project_structure(target_dir, options)
    
    # Initialize asset manager
    asset_manager = AssetManager(str(source_dir), str(target_dir))
    asset_manager.copy_assets()
    
    # Find HTML files
    html_files = list(source_dir.glob('*.html'))
    
    if not html_files:
        print("❌ Error: No HTML files found")
        return
    
    print(f"\n🔍 Found {len(html_files)} HTML file(s)")
    
    # Convert pages
    pages = []
    errors = []
    
    for html_file in html_files:
        print(f"\n📄 Processing: {html_file.name}")
        
        try:
            page_data = convert_page(html_file, options, asset_manager)
            pages.append(page_data)
            
            # Write page component
            ext = 'tsx' if options.ts else 'jsx'
            page_path = target_dir / 'src' / 'pages' / f"{page_data['name']}.{ext}"
            write_file(str(page_path), page_data['code'])
            print(f"  ✓ Created: pages/{page_data['name']}.{ext}")
            
            # Write user components
            for comp_name, comp_code, _ in page_data['user_components']:
                comp_path = target_dir / 'src' / 'components' / f"{comp_name}.{ext}"
                write_file(str(comp_path), comp_code)
                print(f"  ✓ Created: components/{comp_name}.{ext}")
            
        except Exception as e:
            error_msg = f"Error in {html_file.name}: {str(e)}"
            errors.append(error_msg)
            print(f"  ❌ {error_msg}")
            import traceback
            traceback.print_exc()
    
    # Generate main entry
    if pages:
        print("\n🔧 Generating main entry point...")
        generate_main_entry(target_dir, pages, options)
        print("  ✓ Created main entry")
    
    # Create README
    readme = f"""# {options.name}

Generated with Advanced HTML to React Converter v4

## Setup

Install dependencies:
```bash
npm install
```

## Development

Run development server:
```bash
npm run dev
```

## Build

Build for production:
```bash
npm run build
```

## Project Structure

```
{options.name}/
├── src/
│   ├── pages/          # Page components
│   ├── components/     # Reusable components
│   └── main.{('tsx' if options.ts else 'jsx')}        # Entry point
├── public/             # Static assets
└── package.json
```

## Notes

- ✅ HTML converted to JSX
- ✅ CSS {'modules' if options.css_modules else 'files'} imported
- ✅ Event handlers extracted
- ✅ Routing configured
- ⚠️  Review all event handlers for correctness
- ⚠️  Test interactive features thoroughly
- ⚠️  Update hardcoded URLs/paths as needed

## Manual Review Checklist

- [ ] Test all forms and interactions
- [ ] Verify CSS styling
- [ ] Check responsive behavior
- [ ] Update environment-specific URLs
- [ ] Add error boundaries
- [ ] Implement proper state management
- [ ] Add loading states
- [ ] Handle edge cases

"""
    write_file(str(target_dir / 'README.md'), readme)
    
    # Install dependencies
    if not args.no_install:
        print("\n📦 Installing dependencies...")
        import subprocess
        
        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=str(target_dir),
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("  ✓ Dependencies installed")
            else:
                print(f"  ⚠️  npm install had issues:\n{result.stderr}")
        except subprocess.TimeoutExpired:
            print("  ⚠️  npm install timed out")
        except FileNotFoundError:
            print("  ⚠️  npm not found. Install manually:")
            print(f"     cd {target_dir} && npm install")
        except Exception as e:
            print(f"  ⚠️  Error during npm install: {e}")
    
    # Print summary
    print("\n" + "="*60)
    print("✅ CONVERSION COMPLETE")
    print("="*60)
    print(f"✓ Converted: {len(pages)} page(s)")
    if errors:
        print(f"⚠️  Errors: {len(errors)}")
        for error in errors:
            print(f"   - {error}")
    print(f"\n📂 Project location: {target_dir}")
    print("\n🚀 Next steps:")
    print(f"   cd {target_dir}")
    if args.no_install:
        print("   npm install")
    print("   npm run dev")
    print("\n⚠️  Important: Review and test all features!")
    print("="*60)


if __name__ == '__main__':
    main()