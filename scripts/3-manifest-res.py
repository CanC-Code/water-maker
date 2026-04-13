import os

def generate_resources():
    # 1. Corrected Manifest (Removed deprecated package attribute)
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <application 
        android:label="WaterMarker" 
        android:theme="@style/Theme.WaterMarker"
        android:icon="@mipmap/ic_launcher">
        <activity android:name=".MainActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

    # 2. Logic Fault Fix: Defined colors and theme required for linking
    colors_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_500">#FF6200EE</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>
"""

    themes_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.WaterMarker" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="colorPrimary">@color/purple_500</item>
        <item name="android:statusBarColor">@color/black</item>
    </style>
</resources>
"""

    files = {
        "app/src/main/AndroidManifest.xml": manifest_content,
        "app/src/main/res/values/colors.xml": colors_content,
        "app/src/main/res/values/themes.xml": themes_content
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content.strip())
    print("✅ Manifest, Colors, and Themes generated.")

if __name__ == "__main__":
    generate_resources()
