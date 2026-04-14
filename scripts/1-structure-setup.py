import os

def create_structure():
    # Detect the project root safely
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    folders = [
        "app/src/main/cpp",
        "app/src/main/java/com/watermarker",
        "app/src/main/res/drawable",
        "app/src/main/res/values",
        "app/src/main/res/mipmap-hdpi",
        "app/src/main/res/mipmap-anydpi-v26",
        "gradle/wrapper"
    ]

    print("🏗️ Initializing project structure...")
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("✅ Structure initialized.")

if __name__ == "__main__":
    create_structure()
