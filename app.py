import sqlite3
import re
import json
from flask import Flask, render_template_string

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('architecture_map.db')
    conn.row_factory = sqlite3.Row  
    return conn

def clean_ai_summary(raw_text):
    """
    Strips accidental JSON formatting and literal escaped characters
    that were saved directly into the SQLite database.
    """
    if not raw_text:
        return ""
    try:
        parsed = json.loads(raw_text)
        if isinstance(parsed, list):
            return "\n".join(parsed)
        elif isinstance(parsed, str):
            return parsed
    except Exception:
        pass
        
    cleaned = str(raw_text).replace('\\n', '\n').replace('\\"', '"').replace('\\t', '\t')
    if cleaned.startswith('["') and cleaned.endswith('"]'):
        cleaned = cleaned[2:-2]
    return cleaned

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_name, file_type, function_name, function_code, ai_summary FROM functions ORDER BY file_name")
    rows = cursor.fetchall()
    conn.close()

    colors = {
        'python': {'bg': '#064e3b', 'border': '#34d399'}, 
        'vue': {'bg': '#4c1d95', 'border': '#8b5cf6'},    
        'sql': {'bg': '#1e3a8a', 'border': '#3b82f6'},    
        'config': {'bg': '#450a0a', 'border': '#ef4444'}  
    }

    repo_structure = {}
    nodes = []
    edges = []
    processed_files = set()
    
    for row in rows:
        file_name = row['file_name']
        file_type = row['file_type'] or 'python'
        code = row['function_code']
        func_id = f"func_{row['id']}"
        real_name = row['function_name'] or "Unnamed"
        
        clean_summary = clean_ai_summary(row['ai_summary'])
        
        if file_name not in repo_structure:
            repo_structure[file_name] = []
            
        repo_structure[file_name].append({
            'id': func_id,
            'name': real_name
        })
        
        if file_name not in processed_files:
            nodes.append({"id": file_name, "label": f"📄 {file_name}", "shape": "box", "color": {"background": "#0f172a", "border": "#475569"}, "font": {"color": "#94a3b8"}})
            processed_files.add(file_name)
            
        c = colors.get(file_type, {'bg': '#374151', 'border': '#6b7280'})
        
        nodes.append({
            "id": func_id, "label": f"⚡ {real_name}", "shape": "box",
            "color": {"background": c['bg'], "border": c['border']}, "font": {"color": "#f8fafc", "size": 12},
            "file_name": file_name, "code": code, "summary": clean_summary
        })
        edges.append({"from": file_name, "to": func_id})

    repo_tree = {'_files': []}
    for fname, functions in repo_structure.items():
        parts = fname.split('/')
        curr = repo_tree
        for part in parts[:-1]:
            if part not in curr:
                curr[part] = {'_files': []}
            curr = curr[part]
        curr['_files'].append({'name': parts[-1], 'functions': functions})

    graph_data = {"nodes": nodes, "edges": edges}

    # Standard System Architecture Template written in Markdown + Mermaid
    system_architecture_md = """
### 🏗️ Platform System Architecture
This global diagram illustrates how data flows between the frontend client, the backend server, and the asynchronous task queues.

```mermaid
graph TD
    Client[💻 Vue.js Client] -->|REST API Requests| API[⚡ Flask Backend]
    
    subgraph Backend Ecosystem
        API -->|Read / Write| DB[(🗄️ MySQL Database)]
        API -->|Enqueue Tasks| Broker((💨 Redis Broker))
        Broker -->|Consume Tasks| Worker[⚙️ Celery Worker]
        Worker -->|Update Status| DB
    end

"""

    html_template = """
<!DOCTYPE html>
<html lang="en" class="h-full bg-neutral-950 text-neutral-200">
<head>
    <meta charset="UTF-8">
    <title>🧠 Architecture Mind Map</title>
    <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
    <script src="https://cdn.tailwindcss.com?plugins=typography"></script>
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>

<body class="h-full flex flex-col" 
      x-data="mindmapComponent()"
      @open-node-view.window="openNode($event.detail.id)">
    
    <header class="border-b border-neutral-800 bg-neutral-900/50 px-6 py-4 flex items-center justify-between">
        <span class="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">CODEBASE MIND-MAP</span>
        
        <button @click="openSystemArchitecture()" 
                class="bg-neutral-800 hover:bg-neutral-700 text-emerald-400 px-4 py-2 rounded-md text-sm font-bold border border-emerald-500/30 transition-colors flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 7v10c0 2 1.5 3 3.5 3S11 19 11 17V7c0-2-1.5-3-3.5-3S4 5 4 7zm10 0v10c0 2 1.5 3 3.5 3s3.5-1 3.5-3V7c0-2-1.5-3-3.5-3S14 5 14 7z"></path></svg>
            View System Architecture
        </button>
    </header>

    <div class="flex flex-1 overflow-hidden">
        <aside class="w-80 border-r border-neutral-800 bg-neutral-900/20 overflow-y-auto p-4">
            {% macro render_tree(node, depth=0) %}
                {% for folder, content in node.items() %}
                    {% if folder != '_files' %}
                        <div class="mb-2" x-data="{ open: true }">
                            <button @click="open = !open" class="flex items-center text-xs font-mono text-emerald-300 hover:text-emerald-400 mb-1" style="padding-left: {{ depth * 12 }}px">
                                <svg x-show="!open" class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg>
                                <svg x-show="open" class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>
                                📁 {{ folder }}
                            </button>
                            <div x-show="open">
                                {{ render_tree(content, depth + 1) }}
                            </div>
                        </div>
                    {% endif %}
                {% endfor %}
                {% if node.get('_files') %}
                    {% for file in node['_files'] %}
                    <div class="mb-2 bg-neutral-900/60 p-2 rounded-lg border border-neutral-800" style="margin-left: {{ depth * 12 }}px">
                        <div class="text-emerald-400 text-xs font-mono mb-1 truncate" title="{{ file.name }}">📄 {{ file.name }}</div>
                        {% for func in file.functions %}
                        <button @click="openNode('{{ func.id }}')"
                                class="w-full text-left px-2 py-1 text-xs font-mono text-neutral-400 hover:text-emerald-400 truncate">⚡ {{ func.name }}</button>
                        {% endfor %}
                    </div>
                    {% endfor %}
                {% endif %}
            {% endmacro %}
            {{ render_tree(tree) }}
        </aside>

        <main class="flex-1 bg-neutral-950 relative">
            <div id="architecture-network" class="w-full h-full"></div>
            
            <template x-if="showPanel">
                <div class="absolute inset-0 z-20 flex bg-neutral-950 divide-x divide-neutral-800">
                    <template x-if="selectedCode">
                        <section class="flex-1 overflow-auto p-4"><pre class="text-xs text-neutral-300" x-text="selectedCode"></pre></section>
                    </template>
                    
                    <section :class="selectedCode ? 'w-[450px]' : 'flex-1 max-w-5xl mx-auto'" 
                             class="overflow-auto p-6 prose prose-invert prose-emerald" 
                             id="summary-container" x-html="selectedSummary"></section>
                    
                    <button @click="showPanel = false" class="absolute top-4 right-4 bg-neutral-800 px-3 py-1 rounded text-xs">Close</button>
                </div>
            </template>
        </main>
    </div>

    <script>
        mermaid.initialize({ startOnLoad: false, theme: 'dark' });

        window.appGraphData = {{ graph_json | safe }};
        window.appSysArch = {{ sys_arch_json | safe }}; 

        document.addEventListener('alpine:init', () => {
            Alpine.data('mindmapComponent', () => ({
                showPanel: false, 
                selectedCode: '', 
                selectedSummary: '', 
                selectedFile: '',
                
                openSystemArchitecture() {
                    this.selectedCode = ''; 
                    this.selectedSummary = marked.parse(window.appSysArch);
                    this.showPanel = true;
                    this.renderMermaid();
                },

                openNode(nodeId) {
                    const node = window.appGraphData.nodes.find(n => n.id === nodeId);
                    if (node && node.code) {
                        this.selectedFile = node.file_name;
                        this.selectedCode = node.code;
                        
                        let rawSummary = node.summary;
                        if (!rawSummary || rawSummary.trim() === '' || rawSummary === 'null') {
                            rawSummary = '### ⚠️ No AI Summary Available\\n\\nThe AI analysis pipeline did not return a summary for this file.';
                        }
                        
                        try {
                            this.selectedSummary = marked.parse(String(rawSummary));
                        } catch (error) {
                            const safeRawText = String(rawSummary).replace(/</g, '&lt;').replace(/>/g, '&gt;');
                            this.selectedSummary = `<p class="text-red-400">Error rendering markdown.</p><pre class="text-xs text-neutral-500 mt-4 whitespace-pre-wrap">${safeRawText}</pre>`;
                        }
                        
                        this.showPanel = true;
                        this.renderMermaid();
                    }
                },

                renderMermaid() {
                    this.$nextTick(() => {
                        const container = document.getElementById('summary-container');
                        if (container) {
                            const mermaidBlocks = container.querySelectorAll('code.language-mermaid');
                            mermaidBlocks.forEach((el) => {
                                const pre = el.parentElement;
                                if (pre && pre.tagName === 'PRE') {
                                    const div = document.createElement('div');
                                    div.className = 'mermaid flex justify-center mt-6'; 
                                    div.textContent = el.textContent;
                                    pre.replaceWith(div);
                                }
                            });
                        }

                        if (window.mermaid) {
                            mermaid.run({ querySelector: '.mermaid' }).catch(e => console.error("Mermaid error:", e));
                        }
                    });
                }
            }));
        });

        document.addEventListener('DOMContentLoaded', () => {
                const data = { 
                    nodes: new vis.DataSet(window.appGraphData.nodes), 
                    edges: new vis.DataSet(window.appGraphData.edges) 
                };
                
                // 🟢 SENIOR UI/UX FIX: The Archipelago Layout
                const network = new vis.Network(document.getElementById('architecture-network'), data, { 
                    layout: {
                        improvedLayout: true
                    },
                    physics: {
                        enabled: true,
                        solver: 'repulsion', // Spreads nodes out to fill empty space
                        repulsion: {
                            nodeDistance: 180,      // Pushes different files away from each other
                            centralGravity: 0.05,   // Gently pulls everything toward the center so nothing floats away
                            springLength: 60,       // Pulls functions tightly to their parent file (creates neat clusters)
                            springConstant: 0.05
                        },
                        stabilization: {
                            enabled: true,
                            iterations: 500,        // Pre-calculates the physics silently BEFORE showing the user
                            fit: true               // Automatically frames the entire map perfectly on load
                        }
                    },
                    edges: {
                        smooth: {
                            type: 'curvedCW',       // Gentle, modern curves
                            roundness: 0.2
                        },
                        color: { color: '#475569', opacity: 0.7, highlight: '#34d399' },
                        arrows: { to: { enabled: true, scaleFactor: 0.5 } } 
                    },
                    interaction: {
                        hover: true,
                        tooltipDelay: 200,
                        zoomView: true
                    }
                });
                
                network.on("click", (p) => {
                    if (p.nodes.length) {
                        window.dispatchEvent(new CustomEvent('open-node-view', { detail: { id: p.nodes[0] } }));
                    }
                });
            });
    </script>
</body>
</html>
"""
    return render_template_string(html_template, structure=repo_structure, tree=repo_tree, graph_json=json.dumps(graph_data), sys_arch_json=json.dumps(system_architecture_md))

if __name__ == '__main__':
    app.run(debug=True, port=5000)