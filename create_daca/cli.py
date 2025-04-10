import sys
import shutil
import subprocess
from pathlib import Path

def create_project(project_name: str):
    target_dir = Path.cwd() / project_name
    template_dir = Path(__file__).parent / "template"

    if target_dir.exists():
        print(f"Error: Directory '{project_name}' already exists.")
        sys.exit(1)

    shutil.copytree(template_dir, target_dir)
    subprocess.run(["uv", "sync"], cwd=target_dir / "chat_service", check=True)
    subprocess.run(["uv", "sync"], cwd=target_dir / "agent_memory_service", check=True)
    print(f"Created DACA project '{project_name}' at {target_dir}")

def main():
    if len(sys.argv) < 2:
        print("Usage: create-daca <project-name>")
        sys.exit(1)
    create_project(sys.argv[1])

if __name__ == "__main__":
    main()