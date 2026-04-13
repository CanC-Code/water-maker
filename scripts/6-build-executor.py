import os
import subprocess

def run_build():
    print("🏗️  Initializing Final Build...")
    
    try:
        # 1. Generate Gradle Wrapper if it doesn't exist
        if not os.path.exists("gradlew"):
            print("📦 Wrapper not found. Generating via system 'gradle'...")
            subprocess.run(["gradle", "wrapper"], check=True)
        
        # 2. Fix permissions (just in case)
        subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        # 3. Execute the build
        # Using --no-daemon for CI environments to save memory
        print("🚀 Running ./gradlew assembleDebug --no-daemon...")
        subprocess.run(["./gradlew", "assembleDebug", "--no-daemon"], check=True)
        
        print("✅ Build Successful!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed during command: {e.cmd}")
        exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        exit(1)

if __name__ == "__main__":
    run_build()
