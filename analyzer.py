# analyzer.py
import os
import re
import tree_sitter_python as tspython
from tree_sitter import Language, Parser
from database import db, ProjectNode

# --- 1. Global Configuration ---
IGNORE_DIRS = {'venv', '.venv', 'node_modules', '.git', '__pycache__', 'dist', 'build', 'target', '.idea', '.vscode', '.next', 'config'}
IMPORTANT_CONFIGS = {'dockerfile', 'docker-compose.yml', 'requirements.txt', '.env.example', 'package.json', 'next.config.js'}

# Completely ignore media, locks, and compiled files
IGNORE_EXTS = {
    '.lock', '.svg', '.png', '.jpg', '.jpeg', '.ico', '.pyc', '.log', '.map'
}

# Ignore generic docs/configs UNLESS they are in IMPORTANT_CONFIGS
CONFIG_EXTS = {
    '.json', '.md', '.txt', '.yml', '.yaml'
}

# Initialize Python Tree-Sitter
PY_LANGUAGE = Language(tspython.language())
PARSER = Parser()
PARSER.language = PY_LANGUAGE
PY_QUERY = PY_LANGUAGE.query("(function_definition) @func (class_definition) @class")

# --- 2. Routing Engine ---
def _get_file_type(ext):
    """Maps file extensions to high-level language categories."""
    mapping = {
        '.py': 'python',
        '.vue': 'vue',
        '.js': 'javascript', '.ts': 'typescript',
        '.jsx': 'react', '.tsx': 'react',  
        '.java': 'java',
        '.cpp': 'cpp', '.hpp': 'cpp', '.c': 'cpp', '.h': 'cpp',
        '.html': 'html',
        '.sql': 'sql'
    }
    return mapping.get(ext, 'config')

# --- 3. Framework & Language Parsing Strategies ---
def _parse_python_frameworks(rel_path, content):
    results = []
    try:
        tree = PARSER.parse(content.encode('utf-8'))
        
        # Updated capture loop to avoid unpacking errors
        for capture in PY_QUERY.captures(tree.root_node):
            node = capture[0]  # The actual syntax node
            
            name_node = node.child_by_field_name('name')
            name = content[name_node.start_byte:name_node.end_byte] if name_node else "Anonymous"
            code_block = content[node.start_byte:node.end_byte]
            
            node_type = "Class" if node.type == "class_definition" else "Function"
            display_name = f"{node_type}: {name}"
            file_type_tag = "python" 
            
            # Framework Detection Logic
            if "@app.route" in code_block or "@bp.route" in code_block or ".route(" in code_block:
                display_name = f"Flask Route: {name}"
                file_type_tag = "flask"
            elif "models.Model" in code_block or "db.Model" in code_block:
                display_name = f"DB Model: {name}"
                file_type_tag = "django" if "models.Model" in code_block else "flask"
            elif "serializers.ModelSerializer" in code_block:
                display_name = f"Django Serializer: {name}"
                file_type_tag = "django"
            elif "render(request" in code_block or "HttpResponse" in code_block:
                display_name = f"Django View: {name}"
                file_type_tag = "django"

            results.append({
                "file_name": rel_path,
                "file_type": file_type_tag,
                "function_name": display_name,
                "function_code": code_block
            })
            
    except Exception as e:
        results.append({
            "file_name": rel_path, 
            "file_type": "python", 
            "function_name": "Error Parsing", 
            "function_code": str(e)
        })
    return results
def _extract_brace_block(content, start_index):
    open_braces = 0
    in_string = False
    string_char = ''
    escape = False
    
    for i in range(start_index, len(content)):
        char = content[i]
        
        if escape:
            escape = False
            continue
            
        if char == '\\':
            escape = True
            continue
            
        if in_string:
            if char == string_char:
                in_string = False
            continue
            
        if char in ("'", '"', '`'):
            in_string = True
            string_char = char
            continue
            
        if char == '{':
            open_braces += 1
        elif char == '}':
            open_braces -= 1
            if open_braces == 0:
                return content[start_index:i+1]
                
    return content[start_index:]

def _parse_react_next(rel_path, content):
    results = []
    next_funcs = ['getServerSideProps', 'getStaticProps', 'getStaticPaths', 'generateMetadata']
    for func in next_funcs:
        for match in re.finditer(r'((?:export\s+)?(?:async\s+)?function\s+' + func + r'\s*\([^)]*\)\s*\{)', content):
            sig = match.group(1)
            block = _extract_brace_block(content, match.end(1) - 1)
            results.append({"file_name": rel_path, "file_type": "react", "function_name": f"Next API: {func}", "function_code": sig[:-1] + block})

    for match in re.finditer(r'((?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Z][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "react", "function_name": f"Component: {match.group(2)}", "function_code": sig[:-1] + block})

    for match in re.finditer(r'((?:export\s+)?(?:const|let|var)\s+([A-Z][a-zA-Z0-9_]*)\s*=\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>\s*\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "react", "function_name": f"Component (Arrow): {match.group(2)}", "function_code": sig[:-1] + block})

    for match in re.finditer(r'(function\s+(use[A-Z][a-zA-Z0-9_]*)\s*\([^)]*\)\s*\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "react", "function_name": f"Hook: {match.group(2)}", "function_code": sig[:-1] + block})

    return results

def _parse_node_express(rel_path, content):
    results = []
    for match in re.finditer(r'((?:app|router)\.(get|post|put|delete|patch|use)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*(?:async\s+)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>\s*\{)', content):
        method = match.group(2).upper()
        route = match.group(3)
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "node", "function_name": f"Express {method}: {route}", "function_code": sig[:-1] + block + ")"})

    for match in re.finditer(r'((?:app|router)\.(get|post|put|delete|patch|use)\s*\(\s*[\'"`]([^\'"`]+)[\'"`]\s*,\s*(?:async\s+)?function\s*(?:[a-zA-Z0-9_]+)?\s*\([^)]*\)\s*\{)', content):
        method = match.group(2).upper()
        route = match.group(3)
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "node", "function_name": f"Express {method}: {route}", "function_code": sig[:-1] + block + ")"})

    return results

def _parse_vue(rel_path, content):
    results = []
    script = re.search(r'<script.*?(?:setup)?>(.*?)</script>', content, re.DOTALL)
    if script:
        results.append({"file_name": rel_path, "file_type": "vue", "function_name": "Vue Script Logic", "function_code": script.group(1).strip()})
        
    for match in re.finditer(r'((?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{)', content):
        hook_name = match.group(2)
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "vue", "function_name": f"API Hook: {hook_name}", "function_code": sig[:-1] + block})
        
    for match in re.finditer(r'(const\s+([a-zA-Z0-9_]+)\s*=\s*computed\s*\(\(\)\s*=>\s*\{)', content):
        comp_name = match.group(2)
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "vue", "function_name": f"Computed: {comp_name}", "function_code": sig[:-1] + block + ")"})
        
    return results

def _parse_javascript_typescript(rel_path, content, lang_type):
    results = []
    for match in re.finditer(r'(class\s+([a-zA-Z0-9_]+)(?:\s+extends\s+[a-zA-Z0-9_]+)?\s*\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": lang_type, "function_name": f"Class: {match.group(2)}", "function_code": sig[:-1] + block})
    for match in re.finditer(r'((?:export\s+)?(?:async\s+)?function\s+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": lang_type, "function_name": f"Function: {match.group(2)}", "function_code": sig[:-1] + block})
    return results

def _parse_java(rel_path, content):
    results = []
    for match in re.finditer(r'((?:public|private|protected)?\s*(?:static|final|abstract)?\s*class\s+([a-zA-Z0-9_]+).*?\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "java", "function_name": f"Class: {match.group(2)}", "function_code": sig[:-1] + block})
        
    for match in re.finditer(r'((?:public|private|protected)\s+(?:static\s+)?(?:[\w<>[\]]+\s+)+([a-zA-Z0-9_]+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "java", "function_name": f"Method: {match.group(2)}", "function_code": sig[:-1] + block})
    return results

def _parse_cpp(rel_path, content):
    results = []
    for match in re.finditer(r'((?:class|struct)\s+([a-zA-Z0-9_]+)(?:\s*:\s*(?:public|private|protected)\s+[a-zA-Z0-9_]+)?\s*\{)', content):
        sig = match.group(1)
        block = _extract_brace_block(content, match.end(1) - 1)
        results.append({"file_name": rel_path, "file_type": "cpp", "function_name": f"Struct/Class: {match.group(2)}", "function_code": sig[:-1] + block + ";"})
        
    for match in re.finditer(r'((?:[\w:]+\s+)+([a-zA-Z0-9_:]+)\s*\([^)]*\)\s*(?:const)?\s*\{)', content):
        name = match.group(2)
        if name not in ('if', 'for', 'while', 'switch', 'catch', 'return'):
            sig = match.group(1)
            block = _extract_brace_block(content, match.end(1) - 1)
            results.append({"file_name": rel_path, "file_type": "cpp", "function_name": f"Function: {name}", "function_code": sig[:-1] + block})
    return results

def _parse_html(rel_path, content):
    results = []
    if nav := re.search(r'(<nav.*?</nav>)', content, re.DOTALL | re.IGNORECASE):
        results.append({"file_name": rel_path, "file_type": "html", "function_name": "Section: Navbar", "function_code": nav.group(1)})
    for i, table in enumerate(re.findall(r'(<table.*?</table>)', content, re.DOTALL | re.IGNORECASE)):
        results.append({"file_name": rel_path, "file_type": "html", "function_name": f"Section: Table_{i+1}", "function_code": table})
    for modal in re.findall(r'(<div[^>]*class=["\'][^"\']*modal[^"\']*["\'][^>]*>.*?</div>)', content, re.DOTALL | re.IGNORECASE):
        title = re.search(r'<h[1-6]>(.*?)</h[1-6]>', modal, re.IGNORECASE)
        results.append({"file_name": rel_path, "file_type": "html", "function_name": f"Modal: {title.group(1)}" if title else "Modal: UI Component", "function_code": modal})
    if not results:
        results.append({"file_name": rel_path, "file_type": "html", "function_name": "Full Template", "function_code": content})
    return results

def _parse_sql(rel_path, content):
    results = []
    for match in re.finditer(r'(CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([a-zA-Z0-9_]+).*?;)', content, re.DOTALL | re.IGNORECASE):
        results.append({"file_name": rel_path, "file_type": "sql", "function_name": f"Table: {match.group(2)}", "function_code": match.group(1)})
    if not results:
        results.append({"file_name": rel_path, "file_type": "sql", "function_name": "SQL Script", "function_code": content})
    return results

# --- 4. Main Extraction Loop ---
def extract_all_functions(directory_path):
    extracted_data = []
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in IGNORE_EXTS:
                continue
            if ext in CONFIG_EXTS and file.lower() not in IMPORTANT_CONFIGS:
                continue
            
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, directory_path)
            file_type = _get_file_type(ext)

            if file.lower() in IMPORTANT_CONFIGS or 'config' in file.lower() or file_type == 'config':
                try:
                    with open(path, 'r', errors='ignore') as f:
                        extracted_data.append({"file_name": rel_path, "file_type": "config", "function_name": f"Config: {file}", "function_code": f.read()})
                except Exception:
                    pass
                continue

            try:
                with open(path, 'r', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue

            if file_type == 'python':
                extracted_data.extend(_parse_python_frameworks(rel_path, content))
            elif file_type == 'vue':
                extracted_data.extend(_parse_vue(rel_path, content))
            elif file_type == 'react':
                extracted_data.extend(_parse_react_next(rel_path, content))
            elif file_type in ['javascript', 'typescript']:
                if 'express' in content.lower() or 'app.get(' in content or 'router.post(' in content:
                    extracted_data.extend(_parse_node_express(rel_path, content))
                elif 'import React' in content or 'useState' in content or 'useEffect' in content:
                    extracted_data.extend(_parse_react_next(rel_path, content))
                else:
                    extracted_data.extend(_parse_javascript_typescript(rel_path, content, file_type))
            elif file_type == 'java':
                extracted_data.extend(_parse_java(rel_path, content))
            elif file_type == 'cpp':
                extracted_data.extend(_parse_cpp(rel_path, content))
            elif file_type == 'html':
                extracted_data.extend(_parse_html(rel_path, content))
            elif file_type == 'sql':
                extracted_data.extend(_parse_sql(rel_path, content))

    return extracted_data

# --- 5. Edge Calculation & Database Integration ---
def _calculate_edges(extracted_data):
    all_names = {}
    for item in extracted_data:
        raw_name = item['function_name'].split(': ')[-1] if ': ' in item['function_name'] else item['function_name']
        all_names[raw_name] = item['function_name'] 
        
        item['inbound_calls'] = set()
        item['outbound_calls'] = set()

    for current_node in extracted_data:
        code = current_node['function_code']
        current_display_name = current_node['function_name']
        
        for raw_target_name, target_display_name in all_names.items():
            if current_display_name == target_display_name:
                continue
                
            pattern = rf"\b{re.escape(raw_target_name)}\b(?=\s*\()" 
            
            if re.search(pattern, code):
                current_node['outbound_calls'].add(target_display_name)
                for target_node in extracted_data:
                    if target_node['function_name'] == target_display_name:
                        target_node['inbound_calls'].add(current_display_name)
                        break

    for item in extracted_data:
        item['inbound_calls'] = list(item['inbound_calls'])
        item['outbound_calls'] = list(item['outbound_calls'])
        
    return extracted_data

def process_repository_to_db(repository_id, directory_path):
    """
    Main entry point: Call this from Celery after downloading the GitHub repo.
    """
    raw_nodes = extract_all_functions(directory_path)
    linked_nodes = _calculate_edges(raw_nodes)
    
    for node_data in linked_nodes:
        node_type = 'global'
        if 'Class:' in node_data['function_name'] or 'Struct' in node_data['function_name']:
            node_type = 'class'
        elif 'Config:' not in node_data['function_name'] and 'Full Template' not in node_data['function_name']:
            node_type = 'function'

        metadata = {
            "inbound_calls": node_data['inbound_calls'],
            "outbound_calls": node_data['outbound_calls'],
            "file_name": node_data['file_name'],
            "file_type": node_data['file_type']
        }

        new_node = ProjectNode(
            repository_id=repository_id,
            node_name=node_data['function_name'],
            node_type=node_type,
            code_content=node_data['function_code'].replace('\x00', ''),
            structural_metadata=metadata
        )
        db.session.add(new_node)
        
    db.session.commit()
    print(f"✅ Successfully mapped {len(linked_nodes)} nodes for Repository ID: {repository_id}")