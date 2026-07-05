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

    graph_data = {"nodes": nodes, "edges": edges}

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
    
    <!-- We initialize the clean Alpine component here -->
    <body class="h-full flex flex-col" 
          x-data="mindmapComponent()"
          @open-node-view.window="openNode($event.detail.id)">
        
        <header class="border-b border-neutral-800 bg-neutral-900/50 px-6 py-4 flex items-center justify-between">
            <span class="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">CODEBASE MIND-MAP</span>
        </header>

        <div class="flex flex-1 overflow-hidden">
            <aside class="w-80 border-r border-neutral-800 bg-neutral-900/20 overflow-y-auto p-4">
                {% for file_name, functions in structure.items() %}
                <div class="mb-4 bg-neutral-900/60 p-2 rounded-lg">
                    <div class="text-emerald-400 text-xs font-mono mb-1 truncate">📄 {{ file_name }}</div>
                    {% for func in functions %}
                    <button @click="openNode('{{ func.id }}')"
                            class="w-full text-left px-2 py-1 text-xs font-mono text-neutral-400 hover:text-emerald-400">⚡ {{ func.name }}</button>
                    {% endfor %}
                </div>
                {% endfor %}
            </aside>

            <main class="flex-1 bg-neutral-950 relative">
                <div id="architecture-network" class="w-full h-full"></div>
                
                <template x-if="selectedCode">
                    <div class="absolute inset-0 z-20 flex bg-neutral-950 divide-x divide-neutral-800">
                        <section class="flex-1 overflow-auto p-4"><pre class="text-xs text-neutral-300" x-text="selectedCode"></pre></section>
                        <section id="summary-container" class="w-[450px] overflow-auto p-6 prose prose-invert prose-emerald text-xs" x-html="selectedSummary"></section>
                        <button @click="selectedCode = ''" class="absolute top-4 right-4 bg-neutral-800 px-3 py-1 rounded text-xs">Close</button>
                    </div>
                </template>
            </main>
        </div>

        <script>
            mermaid.initialize({ startOnLoad: false, theme: 'dark' });

            window.appGraphData = {{ graph_json | safe }};

            // 🟢 Extracting the logic into a clean Alpine Component script block
            document.addEventListener('alpine:init', () => {
                Alpine.data('mindmapComponent', () => ({
                    selectedCode: '', 
                    selectedSummary: '', 
                    selectedFile: '',
                    
                    openNode(nodeId) {
                        const node = window.appGraphData.nodes.find(n => n.id === nodeId);
                        if (node && node.code) {
                            this.selectedFile = node.file_name;
                            this.selectedCode = node.code;
                            
                            let rawSummary = node.summary;
                            if (!rawSummary || rawSummary.trim() === '' || rawSummary === 'null') {
                                rawSummary = '### ⚠️ No AI Summary Available\\n\\nThe AI analysis pipeline did not return a summary for this file. This usually happens if the AI API rate limit was reached during the Celery worker process, or if the file was skipped.';
                            }
                            
                            try {
                                this.selectedSummary = marked.parse(String(rawSummary));
                            } catch (error) {
                                const safeRawText = String(rawSummary).replace(/</g, '&lt;').replace(/>/g, '&gt;');
                                this.selectedSummary = `<p class="text-red-400">Error rendering markdown.</p><pre class="text-xs text-neutral-500 mt-4 whitespace-pre-wrap">${safeRawText}</pre>`;
                                console.error("Markdown parse error: ", error);
                            }
                            
                            this.$nextTick(() => {
                                const container = document.getElementById('summary-container');
                                if (container) {
                                    const mermaidBlocks = container.querySelectorAll('code.language-mermaid');
                                    mermaidBlocks.forEach((el) => {
                                        const pre = el.parentElement;
                                        if (pre && pre.tagName === 'PRE') {
                                            const div = document.createElement('div');
                                            div.className = 'mermaid';
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
                    }
                }));
            });

            document.addEventListener('DOMContentLoaded', () => {
                const data = { 
                    nodes: new vis.DataSet(window.appGraphData.nodes), 
                    edges: new vis.DataSet(window.appGraphData.edges) 
                };
                
                const network = new vis.Network(document.getElementById('architecture-network'), data, { 
                    physics: { solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -250, springLength: 200, avoidOverlap: 1 } } 
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
    return render_template_string(html_template, structure=repo_structure, graph_json=json.dumps(graph_data))

if __name__ == '__main__':
    app.run(debug=True, port=5001)