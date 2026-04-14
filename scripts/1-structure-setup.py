import os

def create_structure():
    if os.path.basename(os.getcwd()) == "scripts":
        os.chdir("..")
        
    folders = [
        "app/src/main/cpp",
        "app/src/main/java/com/watermarker",
        "app/src/main/res/drawable",
        "app/src/main/res/values",
        "app/src/main/res/mipmap-hdpi",
        "gradle/wrapper"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
    print("✅ Structure initialized.")

if __name__ == "__main__":
    create_structure()
