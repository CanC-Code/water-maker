import os
import subprocess

def run_build():
    print("🏗️  Initializing Final Build...")
    
    # Check if gradlew exists, if not, we need to generate it via 'gradle wrapper'
    # But in GitHub Actions, we usually just use the installed gradle.
    try:
        # Give execution permission
        subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        # Run the build
        print("🚀 Running ./gradlew assembleDebug...")
        subprocess.run(["./gradlew", "assembleDebug"], check=True)
        
        print("✅ Build Successful! APK located in app/build/outputs/apk/debug/")
    except Exception as e:
        print(f"❌ Build failed: {e}")
        exit(1)

if __name__ == "__main__":
    run_build()
