import os
import subprocess
import sys

def run_build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    print("🏗️ Initializing Final Build...")
    
    try:
        if not os.path.exists("gradlew"):
            print("📦 Generating stable Gradle 8.10.2 wrapper...")
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        if sys.platform != "win32":
            subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        print("🚀 Running Clean Build...")
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        print("✅ Build Successful!")

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code {e.returncode}")
        sys.exit(1) # Ensure CI recognizes the failure
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_build()
