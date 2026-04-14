import os

def generate_resources():
    # Logic Fault Fix: Ensure the activity is clearly defined and the 
    # application tag includes the necessary attributes for modern Android.
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

    <application 
        android:allowBackup="true"
        android:label="WaterMarker" 
        android:theme="@style/Theme.WaterMarker"
        android:extractNativeLibs="true">
        
        <activity 
            android:name="com.watermarker.MainActivity" 
            android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""

    colors_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_500">#FF6200EE</color>
    <color name="black">#FF000000</color>
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
        "app/src/main/AndroidManifest.xml": manifest_content.strip(),
        "app/src/main/res/values/colors.xml": colors_content.strip(),
        "app/src/main/res/values/themes.xml": themes_content.strip()
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Manifest and Resources updated with explicit activity paths.")

if __name__ == "__main__":
    generate_resources()
