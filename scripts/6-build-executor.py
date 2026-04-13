import os
import subprocess

def run_build():
    print("🏗️  Initializing Final Build...")
    
    try:
        # Force a stable Gradle version (8.10.2) to avoid Gradle 9 API breaks
        if not os.path.exists("gradlew"):
            print("📦 Generating stable Gradle 8.10.2 wrapper...")
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        print("🚀 Running ./gradlew assembleDebug --no-daemon...")
        # We use clean to ensure no leftover artifacts from the failed 9.x run
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon"], check=True)
        
        print("✅ Build Successful!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed during command: {e.cmd}")
        exit(1)

if __name__ == "__main__":
    run_build()
