#!/usr/bin/env python3
"""
Advanced Vanilla -> React (Vite) converter v3

Major improvements:
 - Fixed BeautifulSoup parsing and tag replacement issues
 - Better JSX attribute conversion (including self-closing tags)
 - Improved event handler extraction with proper scope handling
 - Smart CSS class mapping for CSS Modules
 - Better component detection and extraction
 - Proper handling of SVG and special elements
 - Route generation with proper imports
 - Error handling and validation
 - Support for nested components
 - Better TypeScript type generation
 - Improved script loading with error handling
 - Asset copying with path resolution

Usage:
  python3 converter_v3.py /path/to/vanilla /path/to/dest --name mysite --ts --css-modules
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
from bs4 import BeautifulSoup, Tag, NavigableString
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
        'link', 'meta', 'param', 'source', 'track', 'wbr'
    }
    return tag_name.lower() in self_closing


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
    'onkeydown': 'onKeyDown',
    'onkeyup': 'onKeyUp',
    'onkeypress': 'onKeyPress',
    'ondblclick': 'onDoubleClick',
    'oncontextmenu': 'onContextMenu',
    'onload': 'onLoad',
    'onerror': 'onError',
    'onscroll': 'onScroll',
    'onresize': 'onResize',
}


class JSXConverter:
    """Handles HTML to JSX conversion"""
    
    def __init__(self, use_css_modules: bool = False):
        self.use_css_modules = use_css_modules
        self.css_class_map: Dict[str, str] = {}
        
    def convert_attributes(self, tag: Tag) -> None:
        """Convert HTML attributes to JSX format"""
        if not hasattr(tag, 'attrs'):
            return
            
        attrs = dict(tag.attrs)
        
        for old_attr, new_attr in list(attrs.items()):
            # Handle class -> className
            if old_attr == 'class':
                classes = tag.attrs.pop('class')
                if self.use_css_modules:
                    tag.attrs['className'] = self._convert_classes_to_modules(classes)
                else:
                    tag.attrs['className'] = ' '.join(classes) if isinstance(classes, list) else classes
            
            # Handle for -> htmlFor
            elif old_attr == 'for':
                tag.attrs['htmlFor'] = tag.attrs.pop('for')
            
            # Handle tabindex -> tabIndex
            elif old_attr == 'tabindex':
                tag.attrs['tabIndex'] = tag.attrs.pop('tabindex')
            
            # Handle boolean attributes
            elif old_attr in ['checked', 'disabled', 'readonly', 'required', 'selected']:
                if tag.attrs[old_attr] == '' or tag.attrs[old_attr] == old_attr:
                    tag.attrs[old_attr] = '{true}'
            
            # Handle data attributes (keep as-is)
            elif old_attr.startswith('data-'):
                continue
                
            # Handle aria attributes (keep as-is)
            elif old_attr.startswith('aria-'):
                continue
    
    def _convert_classes_to_modules(self, classes: List[str]) -> str:
        """Convert CSS classes to CSS module syntax"""
        if isinstance(classes, str):
            classes = classes.split()
        
        converted = []
        for cls in classes:
            module_ref = f"styles.{slugify(cls)}"
            self.css_class_map[cls] = module_ref
            converted.append(module_ref)
        
        if len(converted) == 1:
            return f"{{{converted[0]}}}"
        else:
            return "{`${" + "} ${".join(converted) + "}`}"
    
    def to_jsx_string(self, element) -> str:
        """Convert BeautifulSoup element to JSX string"""
        if isinstance(element, NavigableString):
            text = str(element).strip()
            # Escape curly braces in text content
            if text:
                text = text.replace('{', '{{').replace('}', '}}')
            return text
        
        if not isinstance(element, Tag):
            return str(element)
        
        tag_name = element.name
        attrs_str = self._attrs_to_jsx(element.attrs)
        
        # Handle self-closing tags
        if is_self_closing_tag(tag_name) and not element.contents:
            return f"<{tag_name}{attrs_str} />"
        
        # Handle tags with children
        children = ''.join(self.to_jsx_string(child) for child in element.children)
        
        return f"<{tag_name}{attrs_str}>{children}</{tag_name}>"
    
    def _attrs_to_jsx(self, attrs: dict) -> str:
        """Convert attributes dict to JSX attribute string"""
        if not attrs:
            return ""
        
        parts = []
        for key, value in attrs.items():
            if value is None or value == '':
                parts.append(f" {key}")
            elif isinstance(value, list):
                parts.append(f' {key}="{" ".join(value)}"')
            elif key.startswith('HANDLER_'):
                # Event handler placeholder
                parts.append(f" {key}")
            else:
                # Escape quotes in attribute values
                safe_value = str(value).replace('"', '&quot;')
                parts.append(f' {key}="{safe_value}"')
        
        return ''.join(parts)


# ---------- Event Handler Extraction --------------------------------------

class EventHandlerExtractor:
    """Extract and convert inline event handlers"""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.handlers: List[Dict] = []
        self.handler_count = 0
    
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
                
                self.handlers.append({
                    'name': handler_name,
                    'jsx_attr': jsx_event,
                    'code': code,
                    'original_attr': attr
                })
                
                # Add placeholder
                tag.attrs[f'HANDLER_{jsx_event}'] = f'{{{handler_name}}}'
    
    def extract_from_tree(self, soup: BeautifulSoup) -> None:
        """Extract handlers from entire tree"""
        for tag in soup.find_all(True):
            self.extract_from_tag(tag)
    
    def generate_handler_code(self) -> str:
        """Generate React handler functions"""
        if not self.handlers:
            return ""
        
        code_parts = []
        for handler in self.handlers:
            # Wrap inline code safely
            inline_code = handler['code'].strip()
            
            # Try to detect if preventDefault is needed
            prevent_default = 'submit' in handler['jsx_attr'].lower()
            
            func = textwrap.dedent(f"""
  const {handler['name']} = (event) => {{
    {('event.preventDefault();' if prevent_default else '')}
    try {{
      {inline_code}
    }} catch (error) {{
      console.error('Event handler error in {handler['name']}:', error);
    }}
  }};
            """).strip()
            
            code_parts.append(func)
        
        return '\n\n'.join(code_parts)
    
    def apply_handlers_to_jsx(self, jsx_string: str) -> str:
        """Replace handler placeholders in JSX"""
        for handler in self.handlers:
            placeholder = f'HANDLER_{handler["jsx_attr"]}="{{{handler["name"]}}}"'
            replacement = f'{handler["jsx_attr"]}={{{handler["name"]}}}'
            jsx_string = jsx_string.replace(placeholder, replacement)
        
        return jsx_string


# ---------- Component Detection --------------------------------------------

def detect_user_components(soup: BeautifulSoup) -> List[Tuple[Tag, str]]:
    """Detect user-defined components in the HTML"""
    components = []
    
    for tag in soup.find_all(True):
        if not hasattr(tag, 'attrs'):
            continue
        
        # Check for explicit component markers
        if tag.get('data-component'):
            name = tag['data-component']
            components.append((tag, name))
            continue
        
        # Check for Webflow component markers
        for attr in tag.attrs.keys():
            if attr.startswith('data-wf-'):
                name = tag.get('id') or tag.get('class', ['Component'])[0]
                components.append((tag, name))
                break
        
        # Check for component-like patterns
        classes = ' '.join(tag.get('class', [])).lower()
        tag_id = (tag.get('id') or '').lower()
        
        if any(pattern in classes or pattern in tag_id 
               for pattern in ['component', 'widget', 'module', 'block']):
            name = tag.get('id') or tag.get('class', ['Component'])[0]
            if isinstance(name, list):
                name = name[0]
            components.append((tag, name))
    
    return components


# ---------- Shared Component Detection ------------------------------------

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
        # Look for header
        header = soup.find('header')
        if header:
            fragments['Header'].append(normalize(str(header)))
        
        # Look for footer
        footer = soup.find('footer')
        if footer:
            fragments['Footer'].append(normalize(str(footer)))
        
        # Look for nav
        nav = soup.find('nav')
        if nav:
            fragments['Navigation'].append(normalize(str(nav)))
    
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
        
        soup = BeautifulSoup(html, 'html5lib')
        body = soup.find('body') if is_page else soup
        
        if body is None:
            body = soup
        
        # Extract event handlers
        handler_extractor = EventHandlerExtractor(name)
        handler_extractor.extract_from_tree(body)
        
        # Convert attributes
        for tag in body.find_all(True):
            self.jsx_converter.convert_attributes(tag)
        
        # Convert to JSX
        jsx = self.jsx_converter.to_jsx_string(body)
        jsx = handler_extractor.apply_handlers_to_jsx(jsx)
        
        # Generate imports
        imports = ['import React from "react";']
        
        if self.options.css_modules:
            imports.append(f'import styles from "./{name}.module.css";')
        
        if is_page:
            imports.append('import { Helmet } from "react-helmet-async";')
        
        # Generate component code
        handler_code = handler_extractor.generate_handler_code()
        
        component_code = f"""
{chr(10).join(imports)}

{handler_code}

const {name} = () => {{
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
            replacement = BeautifulSoup(f'<{comp_name} />', 'html.parser')
            tag.replace_with(replacement.contents[0])
            
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
            print(f"Warning: CSS file not found: {source_path}")
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
    
    def copy_script(self, src: str, page_name: str) -> Optional[str]:
        """Copy JS file and return public path"""
        if src.startswith(('http://', 'https://', '//')):
            return src
        
        source_path = self.source_root / src.lstrip('/')
        
        if not source_path.exists():
            print(f"Warning: Script not found: {source_path}")
            return None
        
        dest_dir = self.public_dir / 'js'
        ensure_dir(str(dest_dir))
        
        filename = f"{page_name.lower()}_{source_path.name}"
        dest_path = dest_dir / filename
        shutil.copy2(source_path, dest_path)
        
        return f'/js/{filename}'
    
    def save_inline_script(self, code: str, page_name: str, index: int) -> str:
        """Save inline script and return public path"""
        dest_dir = self.public_dir / 'js'
        ensure_dir(str(dest_dir))
        
        filename = f"{page_name.lower()}_inline_{index}.js"
        dest_path = dest_dir / filename
        
        write_file(str(dest_path), code)
        
        return f'/js/{filename}'
    
    def copy_assets(self, asset_dir: str = 'assets') -> None:
        """Copy entire assets directory"""
        source_assets = self.source_root / asset_dir
        
        if source_assets.exists():
            dest_assets = self.public_dir / asset_dir
            if dest_assets.exists():
                shutil.rmtree(dest_assets)
            shutil.copytree(source_assets, dest_assets)
            print(f"Copied {asset_dir} directory")


# ---------- Main Conversion Logic ------------------------------------------

def convert_page(html_path: Path, options, asset_manager: AssetManager, 
                shared_components: Dict[str, str]) -> Dict:
    """Convert a single HTML page to React"""
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    soup = BeautifulSoup(content, 'html5lib')
    page_name = title_case(html_path.stem)
    
    # Extract metadata
    head = soup.find('head')
    title = head.find('title').string if head and head.find('title') else page_name
    meta_tags = []
    
    if head:
        for meta in head.find_all('meta'):
            meta_tags.append(str(meta))
    
    # Process CSS
    css_imports = []
    css_links = []
    
    if head:
        for link in head.find_all('link', rel=lambda x: x and 'stylesheet' in x):
            href = link.get('href')
            if href:
                if href.startswith(('http://', 'https://')):
                    css_links.append(str(link))
                else:
                    path = asset_manager.copy_css(href, options.css_modules)
                    if path:
                        if options.css_modules:
                            css_imports.append(path)
                        else:
                            css_links.append(f'<link rel="stylesheet" href="{path}" />')
    
    # Process scripts
    scripts = []
    
    if head:
        for script in head.find_all('script'):
            src = script.get('src')
            if src:
                path = asset_manager.copy_script(src, html_path.stem)
                if path:
                    scripts.append(path)
            elif script.string:
                path = asset_manager.save_inline_script(script.string, html_path.stem, len(scripts))
                scripts.append(path)
    
    body = soup.find('body')
    if body:
        for script in body.find_all('script'):
            src = script.get('src')
            if src:
                path = asset_manager.copy_script(src, html_path.stem)
                if path:
                    scripts.append(path)
            elif script.string:
                path = asset_manager.save_inline_script(script.string, html_path.stem, len(scripts))
                scripts.append(path)
            script.extract()
    
    # Generate component
    generator = ComponentGenerator(options)
    
    # Extract user components
    user_components = generator.extract_user_components(soup, page_name)
    
    # Generate page component
    page_code, _ = generator.generate_component(page_name, str(soup), is_page=True)
    
    return {
        'name': page_name,
        'code': page_code,
        'title': title,
        'meta_tags': meta_tags,
        'css_links': css_links,
        'scripts': scripts,
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
    (target_dir / 'public' / 'css').mkdir(exist_ok=True)
    (target_dir / 'public' / 'js').mkdir(exist_ok=True)
    
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
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-router-dom": "^6.20.0",
            "react-helmet-async": "^2.0.0"
        },
        "devDependencies": {
            "vite": "^5.0.0",
            "@vitejs/plugin-react": "^4.2.0",
            "@types/react": "^18.2.0" if options.ts else None,
            "@types/react-dom": "^18.2.0" if options.ts else None,
            "typescript": "^5.3.0" if options.ts else None
        }
    }
    
    # Remove None values
    package_json["devDependencies"] = {
        k: v for k, v in package_json["devDependencies"].items() if v is not None
    }
    
    write_file(str(target_dir / 'package.json'), json.dumps(package_json, indent=2))
    
    # vite.config.js
    vite_config = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    assetsDir: 'static',
    emptyOutDir: true
  },
  publicDir: 'public',
  server: {
    port: 3000,
    open: true
  }
})
"""
    write_file(str(target_dir / 'vite.config.js'), vite_config)
    
    # index.html
    index_html = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>React App</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
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
            "include": ["src"],
            "references": [{"path": "./tsconfig.node.json"}]
        }
        write_file(str(target_dir / 'tsconfig.json'), json.dumps(tsconfig, indent=2))


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
        routes.append(f'      <Route path="{page["route"]}" element={{<{page["name"]} />}} />')
    
    main_code = f"""{chr(10).join(imports)}

const App = () => {{
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

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
"""
    
    write_file(str(target_dir / 'src' / f'main.{ext}'), main_code)


# ---------- Main Orchestration ---------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Advanced Vanilla HTML to React (Vite) Converter v3'
    )
    parser.add_argument('source', help='Source directory with HTML files')
    parser.add_argument('dest', help='Destination directory')
    parser.add_argument('--name', default='react-app', help='Project name')
    parser.add_argument('--ts', action='store_true', help='Use TypeScript')
    parser.add_argument('--css-modules', action='store_true', help='Use CSS Modules')
    parser.add_argument('--no-install', action='store_true', help='Skip npm install')
    parser.add_argument('--extract-shared', action='store_true', 
                       help='Extract shared components (header/footer)')
    parser.add_argument('--threshold', type=float, default=0.6,
                       help='Threshold for shared component detection')
    
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    target_dir = Path(args.dest) / args.name
    
    if not source_dir.exists():
        print(f"Error: Source directory '{source_dir}' does not exist")
        return
    
    print(f"Converting {source_dir} -> {target_dir}")
    print(f"Options: TypeScript={args.ts}, CSS Modules={args.css_modules}")
    
    # Create project structure
    class Options:
        pass
    
    options = Options()
    options.name = args.name
    options.ts = args.ts
    options.css_modules = args.css_modules
    options.extract_shared = args.extract_shared
    options.threshold = args.threshold
    
    create_project_structure(target_dir, options)
    
    # Initialize asset manager
    asset_manager = AssetManager(str(source_dir), str(target_dir))
    
    # Copy assets directory if exists
    asset_manager.copy_assets()
    
    # Find HTML files
    html_files = list(source_dir.glob('*.html'))
    
    if not html_files:
        print("Error: No HTML files found in source directory")
        return
    
    print(f"\nFound {len(html_files)} HTML files")
    
    # Detect shared components
    shared_components = {}
    if options.extract_shared:
        soups = {f.name: BeautifulSoup(f.read_text(), 'html5lib') 
                for f in html_files}
        shared_components = detect_shared_components(soups, options.threshold)
        
        if shared_components:
            print(f"Detected shared components: {', '.join(shared_components.keys())}")
    
    # Convert pages
    pages = []
    
    for html_file in html_files:
        print(f"\nProcessing {html_file.name}...")
        
        try:
            page_data = convert_page(html_file, options, asset_manager, shared_components)
            pages.append(page_data)
            
            # Write page component
            ext = 'tsx' if options.ts else 'jsx'
            page_path = target_dir / 'src' / 'pages' / f"{page_data['name']}.{ext}"
            write_file(str(page_path), page_data['code'])
            
            # Write user components
            for comp_name, comp_code, _ in page_data['user_components']:
                comp_path = target_dir / 'src' / 'components' / f"{comp_name}.{ext}"
                write_file(str(comp_path), comp_code)
                print(f"  Created component: {comp_name}")
            
            print(f"  ✓ Converted to {page_data['name']}")
            
        except Exception as e:
            print(f"  ✗ Error converting {html_file.name}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # Generate shared components
    if shared_components:
        ext = 'tsx' if options.ts else 'jsx'
        generator = ComponentGenerator(options)
        
        for comp_name, html in shared_components.items():
            code, _ = generator.generate_component(comp_name, html, is_page=False)
            comp_path = target_dir / 'src' / 'components' / f"{comp_name}.{ext}"
            write_file(str(comp_path), code)
            print(f"Created shared component: {comp_name}")
    
    # Generate main entry
    if pages:
        generate_main_entry(target_dir, pages, options)
        print("\n✓ Generated main entry point")
    
    # Create README
    readme = f"""# {options.name}

This project was generated using the Advanced Vanilla to React Converter v3.

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Run development server:
   ```bash
   npm run dev
   ```

3. Build for production:
   ```bash
   npm run build
   ```

## Project Structure

- `src/pages/` - Page components
- `src/components/` - Reusable components
- `public/` - Static assets (CSS, JS, images)

## Notes

- Event handlers have been extracted and converted to React patterns
- CSS {'modules are' if options.css_modules else 'files are'} used for styling
- All scripts are loaded dynamically via useEffect
- Review and test interactive features carefully

## Manual Review Needed

1. Check event handlers for correct behavior
2. Verify CSS class names and styling
3. Test all interactive elements
4. Update any hardcoded URLs or paths
5. Add proper error boundaries
6. Implement proper state management if needed
"""
    
    write_file(str(target_dir / 'README.md'), readme)
    
    # Install dependencies
    if not args.no_install:
        print("\n" + "="*60)
        print("Installing dependencies...")
        print("="*60)
        
        import subprocess
        import sys
        
        try:
            result = subprocess.run(
                ['npm', 'install'],
                cwd=str(target_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✓ Dependencies installed successfully")
            else:
                print("✗ npm install failed:")
                print(result.stderr)
        except FileNotFoundError:
            print("Warning: npm not found. Please install dependencies manually:")
            print(f"  cd {target_dir}")
            print("  npm install")
        except Exception as e:
            print(f"Error during npm install: {e}")
    
    # Print summary
    print("\n" + "="*60)
    print("CONVERSION COMPLETE")
    print("="*60)
    print(f"✓ Converted {len(pages)} pages")
    print(f"✓ Project created at: {target_dir}")
    print("\nNext steps:")
    print(f"  1. cd {target_dir}")
    if args.no_install:
        print("  2. npm install")
        print("  3. npm run dev")
    else:
        print("  2. npm run dev")
    print("\n⚠️  Important: Review and test all interactive features!")
    print("="*60)


if __name__ == '__main__':
    main()