# 🧠 Codebase Architecture Mind-Map

An AI-powered, end-to-end repository indexing pipeline. It clones any public GitHub repository, extracts function definitions using [tree-sitter](https://github.com/tree-sitter/tree-sitter), generates architectural summaries utilizing Google Gemini or a local Ollama model, and visualizes them on a sleek, high-contrast dark-mode dashboard.

---

## 🛠️ System Architecture

```mermaid
graph TD
    A[trigger.py] -->|Celery Task Request| B[Upstash Redis]
    B -->|Dequeues Job| C[worker.py]
    C -->|Git Clone| D[Local Temp Dir]
    C -->|Extracts Functions| E[slicer.py / Tree-Sitter]
    E -->|Raw Functions| F[analyzer.py]
    F -->|Route 1: Cloud| G[Gemini 2.5 Flash API]
    F -->|Route 2: Fallback Local| H[Ollama / mistral]
    G -->|Summary| I[database.py]
    H -->|Summary| I[database.py]
    I -->|Writes SQLite| J[architecture_map.db]
    K[app.py / Flask Dashboard] -->|Reads| J
    L[read_db.py / CLI view] -->|Reads| J
```

---

## 📋 Prerequisites

Before setting up, make sure your system has the following installed:

1. **Python 3.8+**
2. **Git** (Added to your system's PATH)
3. **Redis Server** (Or an active Cloud connection string, e.g., Upstash Redis)
4. **Ollama** (Required if running AI models locally; optional if only using Gemini API)

---

## 🚀 Environment Setup & Installation

Follow the guide specific to your operating system to set up your environment:

###  macOS / 🐧 Linux

1. **Open your Terminal** and navigate to the project directory:
   ```bash
   cd /Users/nishchaysaluja/Desktop/Projectify/Mind-Map
   ```

2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   ```

3. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

4. **Upgrade pip and install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Xcode CLI Tools / Build Tools**:
   * macOS: Ensure compiler utilities are available:
     ```bash
     xcode-select --install
     ```
   * Linux (Debian/Ubuntu):
     ```bash
     sudo apt update && sudo apt install build-essential git -y
     ```

---

### 🪟 Windows (CMD / PowerShell)

1. **Open Command Prompt or PowerShell** and navigate to the project directory:
   ```cmd
   cd C:\Users\nishchaysaluja\Desktop\Projectify\Mind-Map
   ```

2. **Create a virtual environment**:
   ```cmd
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   * Command Prompt:
     ```cmd
     venv\Scripts\activate.bat
     ```
   * PowerShell:
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```

4. **Upgrade pip and install dependencies**:
   ```cmd
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

5. **Build Tools & Git on Windows**:
   * Make sure Git is installed and checkable via `git --version`.
   * If `tree-sitter` compilation fails, install the [C++ Build Tools for Visual Studio](https://visualstudio.microsoft.com/visual-cpp-build-tools/).

---

## 🦙 Ollama Installation & Setup

Ollama is used to run large language models locally. By default, [analyzer.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/analyzer.py) routes code summary queries to a local Ollama service using the `mistral` model as a rate-limit fallback or primary model if `GEMINI_API_KEY` is not set.

### 1. Install Ollama
* **macOS**:
  * Download the ZIP archive from [ollama.com/download/mac](https://ollama.com/download/mac), extract it, and move the Ollama application to your Applications folder.
  * Alternatively, install via Homebrew:
    ```bash
    brew install ollama
    ```
* **Windows**:
  * Download the installer from [ollama.com/download/windows](https://ollama.com/download/windows) and run the executable (`OllamaSetup.exe`).
* **Linux**:
  * Run the official installation script:
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```

### 2. Start the Ollama Service
* On **macOS** and **Windows**, launch the **Ollama** application from your Applications folder or Start Menu. It will run in the background (visible as an icon in your menu bar or system tray).
* On **Linux**, the installer registers Ollama as a `systemd` service. Verify it is running or start it using:
  ```bash
  sudo systemctl daemon-reload
  sudo systemctl enable ollama
  sudo systemctl start ollama
  ```
  *(Or run `ollama serve` manually in a separate shell terminal).*

### 3. Download the Mistral Model
To download and run the required model, open a terminal or command prompt and run:
```bash
ollama run mistral
```
This downloads the ~4.1GB `mistral` model parameters to your machine. Once the download finishes, you can test it by writing a test prompt directly in the shell, or type `/exit` to close the interactive session.

### 4. Verify API Availability
Verify that Ollama is serving on port `11434`:
* **macOS / Linux**:
  ```bash
  curl http://localhost:11434
  ```
* **Windows (PowerShell)**:
  ```powershell
  Invoke-RestMethod -Uri http://localhost:11434
  ```
*Expected Output:* `Ollama is running`

---

## ⚙️ Configuration (`.env`)

Create or update the [.env](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/.env) file in the root directory:

```env
# Upstash or Local Redis URI
UPSTASH_REDIS_URL=rediss://default:YOUR_REDIS_PASSWORD@your-redis-endpoint.io:6379

# Google Gemini API Key (Highly Recommended)
GEMINI_API_KEY=YOUR_GEMINI_API_KEY

# The target repository URL to parse
GITHUB_URL=https://github.com/username/repository
```

---

## 🏃 Run the Application End-to-End

### Step 1: Run the Celery Worker
The worker handles background execution, cloning, parsing, and requesting AI summaries.

* **macOS / Linux**:
  ```bash
  celery -A worker.app worker --loglevel=info
  ```

* **Windows**:
  Celery does not natively support the default prefork pooling system on Windows. Run it with the `--pool=solo` option:
  ```cmd
  celery -A worker.app worker --loglevel=info --pool=solo
  ```

---

### Step 2: Trigger the Mapping Task
In a separate terminal (with the virtual environment activated), trigger the processing task:
```bash
python trigger.py
```
This task will:
1. Fetch the repository URL configured in [.env](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/.env).
2. Clone it to a secure temporary directory.
3. Walk the codebase, parse Python files, and extract functions via [slicer.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/slicer.py).
4. Run Gemini API (Cloud) or Ollama (Local fallback) to generate architecture Blueprints via [analyzer.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/analyzer.py).
5. Write all analysis directly into [database.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/database.py) (saving in `architecture_map.db`).

---

### Step 3: View the Results

You can view the extracted architecture maps through either the web dashboard or command-line:

#### Option A: Web Dashboard (Recommended)
Start the web dashboard application:
```bash
python app.py
```
* Open your browser and navigate to **`http://127.0.0.1:5000/`**.
* Enjoy the modern, responsive dark-mode layout featuring Alpine.js directory selection, code highlighting, and interactive blueprint blueprints.

#### Option B: Terminal CLI Viewer
To quickly print out the structured data inside the SQLite database, run:
```bash
python read_db.py
```

---

## 📁 Repository Structure & Component Descriptions

* [app.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/app.py): **Flask Dashboard Web Application.**
  Defines the web-server endpoint (`/`) that reads the SQLite database, parses the records, structures files and functions hierarchically, and renders the high-contrast dashboard with Alpine.js UI bindings and Tailwind CSS layout components.
* [worker.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/worker.py): **Celery Asynchronous Task Worker.**
  Configures the Celery application bound to the Upstash Redis queue. It implements `process_repository` which clones a GitHub repo to a temporary directory, invokes the parser, runs the AI analyzer on each function, and invokes the database store.
* [trigger.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/trigger.py): **Task Dispatch Script.**
  Reads `GITHUB_URL` from [.env](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/.env) and dispatches the background task asynchronously to Redis (`process_repository.delay(...)`) so the worker process can begin parsing it.
* [slicer.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/slicer.py): **Abstract Syntax Tree (AST) Parser.**
  Utilizes the `tree-sitter` and `tree-sitter-python` Python wrappers to compile a query searching for all function definitions (`function_definition`) in Python files. It safely extracts and return raw code snippets paired with their filenames.
* [analyzer.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/analyzer.py): **Hybrid AI Summary Router.**
  Controls the prompt generation and AI model selection. Attempts to first call Gemini API (`gemini-2.5-flash`) for cloud processing. If the key is missing or quota/rate limit is reached, it seamlessly falls back to querying the local Ollama HTTP server at `http://localhost:11434/api/generate` with the `mistral` model.
* [database.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/database.py): **Database Schema Helper.**
  Declares the schema for `functions` database table including columns for repository URL, file name, function raw code, and AI-generated summary blueprint. Manages SQL connection open/close routines.
* [read_db.py](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/read_db.py): **Pandas CLI Reader.**
  A developer utility script that reads the SQLite database into a Pandas DataFrame and prints a formatted summary table directly to the console for quick validation.
* [requirements.txt](file:///Users/nishchaysaluja/Desktop/Projectify/Mind-Map/requirements.txt): **Project Dependency Specifier.**
  Lists exact version pins for the Flask web server, Celery worker framework, Upstash Redis driver, Google Gemini SDK, tree-sitter packages, and Pandas.
