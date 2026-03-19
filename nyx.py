print("STARTING V19...")

import os, json, random, hashlib, subprocess, requests, time
from bs4 import BeautifulSoup

# ------------------------------
# INIT
# ------------------------------

def choose_name():
    return random.choice(["Nyx", "Astra", "Orion", "Kael", "Vera"])

state = {
    "ai_name": choose_name(),
    "last_file": None
}

BASE_DIR = os.getcwd()
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
MEMORY_FILE = os.path.join(BASE_DIR, "memory.json")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ------------------------------
# MEMORY SYSTEM
# ------------------------------

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"success": [], "failures": [], "patterns": {}}

def save_memory():
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=2)

memory = load_memory()

# ------------------------------
# AUTH
# ------------------------------

PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()

def auth():
    return hashlib.sha256(input("Enter password: ").encode()).hexdigest() == PASSWORD_HASH

# ------------------------------
# WEB INTELLIGENCE
# ------------------------------

def web_search(query):
    try:
        res = requests.get(f"https://html.duckduckgo.com/html/?q={query}", timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        return [r.get("href") for r in soup.find_all("a", class_="result__a", limit=5)]
    except:
        return []

def extract(url):
    try:
        html = requests.get(url, timeout=5).text
        soup = BeautifulSoup(html, "html.parser")
        return {
            "text": [p.get_text() for p in soup.find_all("p")][:5],
            "code": [c.get_text() for c in soup.find_all("code")][:5]
        }
    except:
        return None

# ------------------------------
# PATTERN DETECTION
# ------------------------------

def detect_patterns(contents):
    patterns = set()

    for c in contents:
        combined = " ".join(c["code"]).lower()

        if "beautifulsoup" in combined:
            patterns.add("scraper")

        if "socket" in combined:
            patterns.add("network")

    return patterns

# ------------------------------
# CODE SYNTHESIS
# ------------------------------

def synthesize(patterns):
    if "scraper" in patterns:
        return """import requests
from bs4 import BeautifulSoup

url = input("URL: ")
res = requests.get(url)
soup = BeautifulSoup(res.text, "html.parser")

for link in soup.find_all("a"):
    print(link.get("href"))
"""

    if "network" in patterns:
        return """import socket
target = input("Target: ")
for port in range(1,1025):
    s = socket.socket()
    if s.connect_ex((target, port)) == 0:
        print("Open:", port)
    s.close()
"""

    return "# No reliable code generated"

# ------------------------------
# FILE SYSTEM
# ------------------------------

def save_code(code):
    name = f"script_{random.randint(1000,9999)}.py"
    path = os.path.join(OUTPUT_DIR, name)

    with open(path, "w") as f:
        f.write(code)

    state["last_file"] = path
    return path

def run_code(path):
    try:
        result = subprocess.run(
            ["python", path],
            capture_output=True,
            text=True,
            timeout=6
        )
        return result.stdout, result.stderr
    except Exception as e:
        return "", str(e)

# ------------------------------
# AUTO DEBUG LOOP
# ------------------------------

def autofix(path, attempts=3):
    for i in range(attempts):
        out, err = run_code(path)

        if not err:
            memory["success"].append(path)
            save_memory()
            return "[SUCCESS]\n" + out

        with open(path, "r") as f:
            code = f.read()

        if "ModuleNotFoundError" in err:
            code = "import requests\n" + code

        if "SyntaxError" in err:
            code = code.replace("== =", "==")

        with open(path, "w") as f:
            f.write(code)

    memory["failures"].append(path)
    save_memory()
    return "[FAILED AFTER RETRIES]"

# ------------------------------
# ANALYSIS / IMPROVEMENT
# ------------------------------

def analyze(path):
    with open(path) as f:
        lines = f.readlines()

    return f"""
Lines: {len(lines)}
Imports: {[l.strip() for l in lines if "import" in l]}
Loops: {[l.strip() for l in lines if "for " in l]}
"""

def improve(path):
    with open(path) as f:
        code = f.read()

    cleaned = "\n".join(dict.fromkeys(code.split("\n")))

    with open(path, "w") as f:
        f.write(cleaned)

    return "Improved."

# ------------------------------
# TASK ENGINE
# ------------------------------

def execute(user):
    urls = web_search(user)
    contents = []

    for u in urls:
        data = extract(u)
        if data:
            contents.append(data)

    patterns = detect_patterns(contents)
    code = synthesize(patterns)

    path = save_code(code)

    out, err = run_code(path)

    if err:
        result = autofix(path)
    else:
        result = out

    return f"""
Saved: {path}

Result:
{result}
"""

# ------------------------------
# COMMAND SYSTEM
# ------------------------------

def command(cmd):
    parts = cmd.split()

    if cmd == "/help":
        print("""
/run last → run last script
/run <file> → run specific script
/files → list scripts
/edit <file> → edit script
/analyze <file> → analyze script
/improve <file> → improve script
/autofix <file> → fix script
/memory → view memory
/clear-memory → wipe memory
""")

    elif parts[0] == "/run":
        path = state["last_file"] if parts[1] == "last" else parts[1]
        print(run_code(path))

    elif cmd == "/files":
        print(os.listdir(OUTPUT_DIR))

    elif parts[0] == "/edit":
        path = parts[1]
        print("Paste code (END to finish):")
        lines = []
        while True:
            l = input()
            if l == "END":
                break
            lines.append(l)
        with open(path, "w") as f:
            f.write("\n".join(lines))

    elif parts[0] == "/analyze":
        print(analyze(parts[1]))

    elif parts[0] == "/improve":
        print(improve(parts[1]))

    elif parts[0] == "/autofix":
        print(autofix(parts[1]))

    elif cmd == "/memory":
        print(memory)

    elif cmd == "/clear-memory":
        memory.clear()
        save_memory()
        print("Memory cleared.")

# ------------------------------
# MAIN
# ------------------------------

def main():
    if not auth():
        print("Denied")
        return

    print(f"[{state['ai_name']}] V19 Ready")

    while True:
        user = input("> ")

        if user.startswith("/"):
            command(user)
            continue

        print(execute(user))

if __name__ == "__main__":
    main()