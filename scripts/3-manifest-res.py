import os

def generate_manifest_and_res():
    manifest_path = "app/src/main/AndroidManifest.xml"
    res_dir = "app/src/main/res"

    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="29" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />

    <application
        android:name=".WaterMarkerApp"
        android:largeHeap="true"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:label="@string/app_name"
        android:supportsRtl="true"
        android:theme="@style/Theme.WaterMarker">

        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-7732503595590477~5528698466"/>

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

    strings_content = """<resources>\n    <string name="app_name">Water Marker</string>\n</resources>"""
    themes_content = """<resources>\n    <style name="Theme.WaterMarker" parent="android:Theme.Material.Light.NoActionBar">\n        <item name="android:statusBarColor">#38BDF8</item>\n    </style>\n</resources>"""

    files = {
        manifest_path: manifest_content.strip(),
        f"{res_dir}/values/strings.xml": strings_content.strip(),
        f"{res_dir}/values/themes.xml": themes_content.strip(),
    }

    print("📄 Generating Manifest (App Name Corrected)...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f: f.write(content)

if __name__ == "__main__":
    generate_manifest_and_res()
