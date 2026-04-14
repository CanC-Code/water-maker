import os

def generate_manifest_and_res():
    manifest_path = "app/src/main/AndroidManifest.xml"
    res_dir = "app/src/main/res"
    
    # 1. Generate AndroidManifest.xml
    # Removed deprecated package attribute and missing mipmap icon references
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    
    <application
        android:name=".WaterMarkerApp"
        android:allowBackup="true"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.WaterMarker">
        
        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-3940256099942544~3347511713"/>

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

    # 2. Generate basic string resources
    strings_content = """<resources>
    <string name="app_name">WaterMaker</string>
</resources>
"""

    # 3. Generate basic theme resource
    themes_content = """<resources>
    <style name="Theme.WaterMarker" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:statusBarColor">#38BDF8</item>
    </style>
</resources>
"""

    files = {
        manifest_path: manifest_content.strip(),
        f"{res_dir}/values/strings.xml": strings_content.strip(),
        f"{res_dir}/values/themes.xml": themes_content.strip(),
    }

    print("📄 Generating fixed AndroidManifest.xml without missing icon references...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Manifest setup complete.")

if __name__ == "__main__":
    generate_manifest_and_res()
