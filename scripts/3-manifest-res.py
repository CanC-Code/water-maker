import os

def generate_resources():
    manifest = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <application 
        android:label="WaterMarker" 
        android:theme="@style/Theme.WaterMarker"
        android:allowBackup="true">
        
        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-7732503595590477~5528698466"/>

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

    # ... (colors and themes stay the same as previous updates) ...
    colors = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_500">#FF6200EE</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>"""

    themes = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.WaterMarker" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="colorPrimary">#38BDF8</item>
        <item name="android:statusBarColor">#020617</item>
    </style>
</resources>"""

    files = {
        "app/src/main/AndroidManifest.xml": manifest.strip(),
        "app/src/main/res/values/colors.xml": colors.strip(),
        "app/src/main/res/values/themes.xml": themes.strip()
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Manifest updated with AdMob App ID.")

if __name__ == "__main__":
    generate_resources()
