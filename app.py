import sqlite3
import re
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
    for row in rows:
        file_name = row['file_name']
        if file_name not in repo_structure:
            repo_structure[file_name] = []
        
        code = row['function_code']
        
        # Regex to find 'def function_name(' and extract just the name
        match = re.search(r'def\s+([a-zA-Z0-9_]+)\s*\(', code)
        real_name = match.group(1) if match else f"Block {row['id']}"
        
        repo_structure[file_name].append({
            'id': row['id'],
            'name': real_name, # Storing the real extracted name
            'code': code,
            'summary': row['ai_summary']
        })

    # High-contrast, minimalist premium dark-mode dashboard template
    html_template = """
    <!DOCTYPE html>
    <html lang="en" class="h-full bg-neutral-950 text-neutral-200">
    <head>
        <meta charset="UTF-8">
        <title>🧠 Architecture Mind Map</title>
        <script src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js" defer></script>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="h-full flex flex-col font-sans antialiased" x-data="{ 
        selectedCode: '', 
        selectedSummary: '', 
        selectedFile: '',
        selectFunction(file, code, summary) {
            this.selectedFile = file;
            this.selectedCode = code;
            this.selectedSummary = summary;
        }
    }">
        
        <!-- Header -->
        <header class="border-b border-neutral-800 bg-neutral-900/50 px-6 py-4 flex items-center justify-between backdrop-blur-md sticky top-0 z-10">
            <div class="flex items-center space-x-3">
                <span class="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">CODEBASE MIND-MAP</span>
                <span class="px-2 py-0.5 text-xs font-semibold bg-neutral-800 border border-neutral-700 rounded-full text-neutral-400">v1.0</span>
            </div>
            <div class="text-xs text-neutral-500 font-mono">Local Workspace Pipeline</div>
        </header>

        <!-- Main Workspace -->
        <div class="flex flex-1 overflow-hidden">
            
            <!-- Left Sidebar: Code Directory -->
            <aside class="w-80 border-r border-neutral-800 bg-neutral-900/20 overflow-y-auto p-4 space-y-4">
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
                            <!-- Safely bind data to HTML attributes using Jinja escape (|e) -->
                            <button 
                                data-file="{{ file_name }}"
                                data-code="{{ func.code | e }}"
                                data-summary="{{ func.summary | e }}"
                                @click="selectFunction($el.dataset.file, $el.dataset.code, $el.dataset.summary)"
                                class="w-full text-left px-2 py-1.5 text-xs rounded font-mono text-neutral-400 hover:bg-neutral-800 hover:text-neutral-100 transition-all flex items-center space-x-1.5"
                                :class="selectedCode === $el.dataset.code ? 'bg-neutral-800 text-emerald-400 font-semibold border-l-2 border-emerald-500 pl-1.5' : ''"
                            >
                                <span>⚡</span>
                                <!-- We inject the dynamically extracted real function name here -->
                                <span class="truncate">{{ func.name }}()</span>
                            </button>
                            {% endfor %}
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </aside>

            <!-- Right Workspace Pane -->
            <main class="flex-1 flex flex-col md:flex-row overflow-hidden bg-neutral-950">
                
                <!-- If nothing is selected -->
                <div x-show="!selectedCode" class="flex-1 flex flex-col items-center justify-center text-center p-12 space-y-3">
                    <div class="text-4xl text-neutral-700 animate-pulse">🧠</div>
                    <p class="text-sm text-neutral-500">Select a function block from the directory tree to inspect its layout and AI analysis mapping.</p>
                </div>

                <!-- Splitted Detailed Panels -->
                <template x-if="selectedCode">
                    <div class="flex-1 flex flex-col md:flex-row w-full h-full overflow-hidden divide-y md:divide-y-0 md:divide-x divide-neutral-800">
                        
                        <!-- Left Panel: Raw Extracted Code -->
                        <section class="flex-1 flex flex-col h-1/2 md:h-full overflow-hidden">
                            <div class="px-4 py-2 border-b border-neutral-800 bg-neutral-900/40 flex items-center justify-between">
                                <span class="text-xs font-semibold uppercase tracking-wider text-neutral-400">Source Code</span>
                                <span class="text-xs font-mono text-emerald-500 bg-emerald-500/10 px-2 py-1 rounded" x-text="selectedFile"></span>
                            </div>
                            <div class="flex-1 p-4 overflow-auto font-mono text-xs leading-relaxed bg-neutral-950 text-neutral-300 selection:bg-emerald-500/20">
                                <pre class="whitespace-pre-wrap"><code x-text="selectedCode"></code></pre>
                            </div>
                        </section>

                        <!-- Right Panel: Architecture Mapping Details -->
                        <section class="w-full md:w-[450px] flex flex-col h-1/2 md:h-full overflow-hidden bg-neutral-900/10">
                            <div class="px-4 py-2 border-b border-neutral-800 bg-neutral-900/40">
                                <span class="text-xs font-semibold uppercase tracking-wider text-neutral-400">Architectural Analysis</span>
                            </div>
                            <div class="flex-1 p-6 space-y-6 overflow-y-auto">
                                <div class="bg-gradient-to-br from-neutral-900 to-neutral-950 border border-neutral-800 p-5 rounded-xl shadow-xl space-y-3 relative overflow-hidden">
                                    <!-- Decorative accent -->
                                    <div class="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl -mr-10 -mt-10 pointer-events-none"></div>
                                    
                                    <div class="flex items-center space-x-2">
                                        <span class="flex h-2 w-2 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_8px_rgba(52,211,153,0.8)]"></span>
                                        <h3 class="text-sm font-bold tracking-wide text-neutral-100">AI Component Blueprint</h3>
                                    </div>
                                    <p class="text-sm text-neutral-300 leading-relaxed font-normal relative z-10" x-text="selectedSummary"></p>
                                </div>
                                
                                <div class="border border-dashed border-neutral-800 p-4 rounded-xl space-y-2 bg-neutral-900/30">
                                    <h4 class="text-xs font-semibold text-neutral-500 uppercase tracking-wider">Pipeline Meta</h4>
                                    <div class="text-[11px] font-mono space-y-1 text-neutral-400">
                                        <div class="flex justify-between"><span>Engine Protocol:</span> <span class="text-neutral-300">Hybrid Cloud/Local Routing</span></div>
                                        <div class="flex justify-between"><span>Data Store:</span> <span class="text-neutral-300">SQLite Context</span></div>
                                        <div class="flex justify-between"><span>Frontend:</span> <span class="text-neutral-300">Alpine.js + Tailwind</span></div>
                                    </div>
                                </div>
                            </div>
                        </section>
                        
                    </div>
                </template>

            </main>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template, structure=repo_structure)

if __name__ == '__main__':
    app.run(debug=True, port=5000)