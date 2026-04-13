import os

def generate_resources():
    # 1. AndroidManifest.xml
    # Note: We request permissions for media access
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.WaterMarker">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@style/Theme.WaterMarker">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

    # 2. strings.xml
    strings_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Water Marker</string>
</resources>
"""

    # 3. themes.xml (Material 3)
    themes_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.WaterMarker" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="colorPrimary">#38bdf8</item>
    </style>
</resources>
"""

    files = {
        "app/src/main/AndroidManifest.xml": manifest_content,
        "app/src/main/res/values/strings.xml": strings_content,
        "app/src/main/res/values/themes.xml": themes_content
    }

    print("🏷️  Generating Manifest and Resources...")
    for path, content in files.items():
        try:
            # Ensure the directory exists before writing (redundancy check)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content.strip())
            print(f"✅ Generated: {path}")
        except Exception as e:
            print(f"❌ Failed to write {path}: {e}")

if __name__ == "__main__":
    generate_resources()
