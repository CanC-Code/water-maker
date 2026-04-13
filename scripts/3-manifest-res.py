import os

def generate_resources():
    # 1. AndroidManifest.xml
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

    # 2. Adaptive Icon: Background (A solid blue-ish color)
    icon_bg = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#0F172A" android:pathData="M0,0h108v108h-108z" />
</vector>
"""

    # 3. Adaptive Icon: Foreground (A simple 'W' or placeholder)
    icon_fg = """<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp" android:height="108dp" android:viewportWidth="108" android:viewportHeight="108">
    <path android:fillColor="#38BDF8" android:pathData="M30,30h48v48h-48z" />
</vector>
"""

    # 4. Adaptive Icon Wrapper (The actual mipmap files)
    icon_wrapper = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@drawable/ic_launcher_background" />
    <foreground android:drawable="@drawable/ic_launcher_foreground" />
</adaptive-icon>
"""

    # 5. Themes & Strings
    strings_content = """<resources><string name="app_name">Water Marker</string></resources>"""
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
        "app/src/main/res/values/themes.xml": themes_content,
        "app/src/main/res/drawable/ic_launcher_background.xml": icon_bg,
        "app/src/main/res/drawable/ic_launcher_foreground.xml": icon_fg,
        "app/src/main/res/mipmap-anydpi-v26/ic_launcher.xml": icon_wrapper,
        "app/src/main/res/mipmap-anydpi-v26/ic_launcher_round.xml": icon_wrapper
    }

    print("🏷️ Generating Manifest and Icon Resources...")
    for path, content in files.items():
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w") as f:
                f.write(content.strip())
            print(f"✅ Created: {path}")
        except Exception as e:
            print(f"❌ Failed to write {path}: {e}")

if __name__ == "__main__":
    generate_resources()
