import sqlite3
import re
import json
from flask import Flask, render_template_string

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('architecture_map.db')
    conn.row_factory = sqlite3.Row  
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, file_name, function_code, ai_summary FROM functions ORDER BY file_name")
    rows = cursor.fetchall()
    conn.close()

    repo_structure = {}
    nodes = []
    edges = []
    processed_files = set()
    
    for row in rows:
        file_name = row['file_name']
        code = row['function_code']
        func_id = f"func_{row['id']}"
        
        # Extract real function name
        match = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', code)
        real_name = match.group(1) if match else f"Block {row['id']}"
        
        if file_name not in repo_structure:
            repo_structure[file_name] = []
            
        repo_structure[file_name].append({
            'id': row['id'],
            'name': real_name,
            'code': code,
            'summary': row['ai_summary']
        })
        
        # 1. Add File Node (Level 0)
        if file_name not in processed_files:
            nodes.append({
                "id": file_name, 
                "label": f"📄 {file_name}", 
                "shape": "box", 
                "level": 0,
                "color": {"background": "#064e3b", "border": "#34d399", "hover": {"background": "#047857"}},
                "font": {"color": "#a7f3d0", "face": "monospace"}
            })
            processed_files.add(file_name)
            
        # 2. Add Function Node (Level 1) - Store code and summary for the click event
        nodes.append({
            "id": func_id, 
            "label": f"⚡ {real_name}()", 
            "shape": "box", 
            "level": 1,
            "color": {"background": "#1e293b", "border": "#475569", "hover": {"background": "#334155", "border": "#10b981"}},
            "font": {"color": "#cbd5e1", "size": 12, "face": "monospace"},
            "file_name": file_name,
            "code": code,
            "summary": row['ai_summary']
        })
        
        # 3. Connect File to Function
        edges.append({
            "from": file_name, 
            "to": func_id, 
            "color": {"color": "#334155", "hover": "#10b981"},
            "smooth": {"type": "cubicBezier", "forceDirection": "horizontal", "roundness": 0.4}
        })

    graph_data = {
        "nodes": nodes,
        "edges": edges
    }

    html_template = """
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-neutral-950 text-neutral-200">
    <head>
        <meta charset="UTF-8">
        <title>🧠 Architecture Mind Map</title>
        <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
        <script src="https://cdn.tailwindcss.com"></script>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    </head>
    <!-- The @open-node-view event bridges the Vis.js click to Alpine.js -->
    <body class="h-full flex flex-col font-sans antialiased" 
          x-data="{ 
              selectedCode: '', 
              selectedSummary: '', 
              selectedFile: '',
              selectFunction(file, code, summary) {
                  this.selectedFile = file;
                  this.selectedCode = code;
                  this.selectedSummary = summary;
              }
          }"
          @open-node-view.window="selectFunction($event.detail.file, $event.detail.code, $event.detail.summary)">
        
        <header class="border-b border-neutral-800 bg-neutral-900/50 px-6 py-4 flex items-center justify-between backdrop-blur-md sticky top-0 z-10">
            <div class="flex items-center space-x-3">
                <span class="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">CODEBASE MIND-MAP</span>
                <span class="px-2 py-0.5 text-xs font-semibold bg-neutral-800 border border-neutral-700 rounded-full text-neutral-400">v1.0</span>
            </div>
            <div class="text-xs text-neutral-500 font-mono">Local Workspace Pipeline</div>
        </header>

        <div class="flex flex-1 overflow-hidden">
            
            <aside class="w-80 border-r border-neutral-800 bg-neutral-900/20 overflow-y-auto p-4 space-y-4 z-10 relative shadow-2xl">
                <h2 class="text-xs font-semibold tracking-wider text-neutral-500 uppercase px-2">Repository Files</h2>
                <div class="space-y-2">
                    {% for file_name, functions in structure.items() %}
                    <div class="bg-neutral-900/60 border border-neutral-800/60 rounded-lg p-2 space-y-1">
                        <div class="flex items-center space-x-2 px-2 py-1 text-sm font-medium text-emerald-400 font-mono truncate">
                            <span>📄</span>
                            <span>{{ file_name }}</span>
                        </div>
                        <div class="space-y-1 pl-4 border-l border-neutral-800 ms-2">
                            {% for func in functions %}
                            <button 
                                data-file="{{ file_name }}"
                                data-code="{{ func.code | e }}"
                                data-summary="{{ func.summary | e }}"
                                @click="selectFunction($el.dataset.file, $el.dataset.code, $el.dataset.summary)"
                                class="w-full text-left px-2 py-1.5 text-xs rounded font-mono text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100 transition-all flex items-center space-x-1.5"
                                :class="selectedCode === $el.dataset.code ? 'bg-neutral-800 text-emerald-400 font-semibold border-l-2 border-emerald-500 pl-1.5' : ''"
                            >
                                <span>⚡</span>
                                <span class="truncate">{{ func.name }}()</span>
                            </button>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </aside>

            <main class="flex-1 flex flex-col md:flex-row overflow-hidden bg-neutral-950 relative">
                
                <!-- Structured Hierarchical Graph -->
                <div x-show="!selectedCode" class="absolute inset-0 w-full h-full flex flex-col">
                    <div class="absolute top-4 left-6 z-10">
                        <h3 class="text-emerald-400 font-mono text-sm">Structural Architecture Map</h3>
                        <p class="text-neutral-500 text-xs mt-1">Click any function block to inspect its layout and AI analysis.</p>
                    </div>
                    <div id="architecture-network" class="w-full h-full cursor-pointer"></div>
                </div>

                <!-- Detailed Panels -->
                <template x-if="selectedCode">
                    <div class="flex-1 flex flex-col md:flex-row w-full h-full overflow-hidden divide-y md:divide-y-0 md:divide-x divide-neutral-800 bg-neutral-950 z-20">
                        
                        <section class="flex-1 flex flex-col h-1/2 md:h-full overflow-hidden relative">
                            <button @click="selectedCode = ''" class="absolute top-2 right-4 text-neutral-500 hover:text-emerald-400 text-xs font-mono bg-neutral-900 px-2 py-1 rounded border border-neutral-800 transition-colors">
                                ← Back to Map
                            </button>
                            
                            <div class="px-4 py-2 border-b border-neutral-800 bg-neutral-900/40 flex items-center justify-between">
                                <span class="text-xs font-semibold uppercase tracking-wider text-neutral-400">Source Code</span>
                                <span class="text-xs font-mono text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded mr-24" x-text="selectedFile"></span>
                            </div>
                            <div class="flex-1 p-4 overflow-auto font-mono text-xs leading-relaxed bg-neutral-950 text-neutral-300 selection:bg-emerald-500/20">
                                <pre class="whitespace-pre-wrap"><code x-text="selectedCode"></code></pre>
                            </div>
                        </section>

                        <section class="w-full md:w-[450px] flex flex-col h-1/2 md:h-full overflow-hidden bg-neutral-900/10">
                            <div class="px-4 py-2 border-b border-neutral-800 bg-neutral-900/40">
                                <span class="text-xs font-semibold uppercase tracking-wider text-neutral-400">Architectural Analysis</span>
                            </div>
                            <div class="flex-1 p-6 space-y-6 overflow-y-auto">
                                <div class="bg-gradient-to-br from-neutral-900 to-neutral-950 border border-neutral-800 p-5 rounded-xl shadow-xl space-y-3 relative overflow-hidden">
                                    <div class="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
                                    <div class="flex items-center space-x-2">
                                        <span class="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
                                        <h3 class="text-sm font-bold tracking-wide text-neutral-100">AI Component Blueprint</h3>
                                    </div>
                                    <p class="text-sm text-neutral-300 leading-relaxed font-normal relative z-10" x-text="selectedSummary"></p>
                                </div>
                            </div>
                        </section>
                        
                    </div>
                </template>

            </main>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function() {
                const graphData = {{ graph_json | safe }};
                const container = document.getElementById('architecture-network');
                
                const data = {
                    nodes: new vis.DataSet(graphData.nodes),
                    edges: new vis.DataSet(graphData.edges)
                };
                
                // Structured tree configuration
                const options = {
                    layout: {
                        hierarchical: false 
                    },
                    physics: {
                        enabled: true,
                        solver: 'forceAtlas2Based',
                        forceAtlas2Based: {
                            gravitationalConstant: -250, // Pushes all clusters firmly apart
                            centralGravity: 0.005,       // Very weak center gravity so the map expands wide
                            springLength: 200,           // Lengthens the leash for massive files like dashboard.py
                            springConstant: 0.04,
                            avoidOverlap: 1              // STRICTLY prevents function boxes from touching
                        },
                        stabilization: {
                            enabled: true,
                            iterations: 300,             // Pre-calculates the layout before rendering
                            fit: true
                        }
                    },
                    interaction: {
                        dragNodes: true,
                        hover: true,
                        zoomView: true
                    }
                };
                const network = new vis.Network(container, data, options);

                // Add the Click Event Listener
                network.on("click", function (params) {
                    if (params.nodes.length > 0) {
                        const nodeId = params.nodes[0];
                        const node = data.nodes.get(nodeId);
                        
                        // If it's a function node with attached code, fire the UI event
                        if (node.code && node.summary) {
                            window.dispatchEvent(new CustomEvent('open-node-view', {
                                detail: {
                                    file: node.file_name,
                                    code: node.code,
                                    summary: node.summary
                                }
                            }));
                        }
                    }
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, structure=repo_structure, graph_json=json.dumps(graph_data))

if __name__ == '__main__':
    app.run(debug=True, port=5000)