import os

def generate():
    manifest_dir = "app/src/main"
    os.makedirs(manifest_dir, exist_ok=True)

    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.watermarker">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />

    <application
        android:name=".WatermarkerApp"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="Water Marker"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.Watermarker">

        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="ca-app-pub-7732503595590477~5528698466"/>

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@style/Theme.Watermarker">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
"""
    with open(f"{manifest_dir}/AndroidManifest.xml", "w") as f:
        f.write(manifest_content)
    print("✅ 3 Generated AndroidManifest.xml (AdMob Configured)")

if __name__ == "__main__":
    generate()
