import os

def create_structure():
    # Logic Fix: Get the absolute path of the project root
    # This ensures it works regardless of where you call the script from.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    # Added necessary folders for adaptive icons and theme resources
    folders = [
        "app/src/main/cpp",
        "app/src/main/java/com/watermarker",
        "app/src/main/res/drawable",
        "app/src/main/res/values",
        "app/src/main/res/mipmap-hdpi",
        "app/src/main/res/mipmap-anydpi-v26", # Required for modern icons
        "app/src/main/res/xml",               # Useful for file providers
        "gradle/wrapper"
    ]

    print("🏗️ Initializing project structure...")
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"  Created: {folder}")
    
    print("✅ Structure initialized successfully.")

if __name__ == "__main__":
    create_structure()
