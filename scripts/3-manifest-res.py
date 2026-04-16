import os

def generate():
    manifest_dir = "app/src/main"
    res_values_dir = "app/src/main/res/values"
    os.makedirs(manifest_dir, exist_ok=True)
    os.makedirs(res_values_dir, exist_ok=True)

    # 1. Generate colors.xml
    colors_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_200">#FFBB86FC</color>
    <color name="purple_500">#FF6200EE</color>
    <color name="purple_700">#FF3700B3</color>
    <color name="teal_200">#FF03DAC5</color>
    <color name="teal_700">#FF018786</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
</resources>
"""
    with open(f"{res_values_dir}/colors.xml", "w") as f:
        f.write(colors_content)

    # 2. Generate themes.xml (DEFINES Theme.Watermarker)
    themes_content = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Watermarker" parent="Theme.Material3.DayNight.NoActionBar">
        <item name="colorPrimary">@color/purple_500</item>
        <item name="android:statusBarColor">@color/purple_700</item>
    </style>
</resources>
"""
    with open(f"{res_values_dir}/themes.xml", "w") as f:
        f.write(themes_content)

    # 3. Generate AndroidManifest.xml (Includes AdMob and correctly linked Theme)
    manifest_content = """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

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
            android:exported="true">
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
    
    print("✅ 3 Generated Manifest, Themes, and Colors (Theme.Watermarker Fix Applied)")

if __name__ == "__main__":
    generate()
