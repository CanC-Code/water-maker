import os
import subprocess
import sys

def run_build():
    # Logic Fix: Get absolute project root to prevent pathing errors
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    os.chdir(project_root)

    print("🏗️  Initializing Final Build...")
    
    try:
        # 1. Ensure Gradle Wrapper exists (Forcing 8.10.2 for stability)
        if not os.path.exists("gradlew"):
            print("📦 Generating stable Gradle 8.10.2 wrapper...")
            # We use 'gradle' from the system path only once to bootstrap
            subprocess.run(["gradle", "wrapper", "--gradle-version", "8.10.2"], check=True)
        
        # Ensure the wrapper is executable
        if sys.platform != "win32":
            subprocess.run(["chmod", "+x", "gradlew"], check=True)
        
        # 2. Execute Clean and Assemble
        print("🚀 Running: ./gradlew clean assembleDebug --no-daemon")
        # Logic Fix: Added '--rerun-tasks' to ensure a completely fresh APK signature
        subprocess.run(["./gradlew", "clean", "assembleDebug", "--no-daemon", "--rerun-tasks"], check=True)
        
        # 3. Verify Output
        apk_path = "app/build/outputs/apk/debug/app-debug.apk"
        if os.path.exists(apk_path):
            print(f"✅ Build Successful!")
            print(f"📦 APK Location: {os.path.abspath(apk_path)}")
            print("\n💡 INSTALLATION TIP:")
            print("If you still get 'App not installed', uninstall the old version")
            print("using: adb uninstall com.watermarker")
        else:
            print("❌ Error: Build finished but APK was not found at expected path.")

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed with exit code {e.returncode}")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_build()
