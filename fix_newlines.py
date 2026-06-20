from pathlib import Path

path = Path("ui/main_window.py")

if not path.exists():
    raise SystemExit("Could not find ui/main_window.py. Run this from the project root.")

text = path.read_text(encoding="utf-8")

# Convert literal double-escaped newline sequences into real Python newline escapes.
# This changes "\\n" in source strings into "\n" in source strings.
fixed = text.replace("\\\\n", "\\n")

if fixed == text:
    print("No double-escaped newline sequences found.")
else:
    path.write_text(fixed, encoding="utf-8")
    print("Fixed double-escaped newline sequences in ui/main_window.py")
