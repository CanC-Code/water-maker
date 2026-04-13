import os

def generate_gradle_files():
    # 1. settings.gradle
    settings_gradle = """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "WaterMarker"
include ':app'
"""

    # 2. gradle.properties
    gradle_properties = """
android.useAndroidX=true
android.nonTransitiveRClass=true
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
"""

    # 3. Root build.gradle
    root_build_gradle = """
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.2.2'
        classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:1.9.20'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}
"""

    # 4. app/build.gradle
    # Note: We include externalNativeBuild for our upcoming C++ engine
    app_build_gradle = """
plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}

android {
    namespace 'com.watermarker'
    compileSdk 34

    defaultConfig {
        applicationId "com.watermarker"
        minSdk 24
        targetSdk 34
        versionCode 1
        versionName "1.0"

        testInstrumentationRunner "androidx.test.runner.AndroidJUnitRunner"
        
        externalNativeBuild {
            cmake {
                cppFlags "-std=c++17"
            }
        }
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    
    externalNativeBuild {
        cmake {
            path "src/main/cpp/CMakeLists.txt"
        }
    }

    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    
    kotlinOptions {
        jvmTarget = '17'
    }

    buildFeatures {
        compose true
    }

    composeOptions {
        kotlinCompilerExtensionVersion '1.5.4'
    }
    
    // Explicitly naming the output APK
    applicationVariants.all { variant ->
        variant.outputs.all {
            outputFileName = "water-marker.apk"
        }
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.7.0'
    implementation 'androidx.activity:activity-compose:1.8.2'
    implementation platform('androidx.compose:compose-bom:2023.10.01')
    implementation 'androidx.compose.ui:ui'
    implementation 'androidx.compose.ui:ui-graphics'
    implementation 'androidx.compose.ui:ui-tooling-preview'
    implementation 'androidx.compose.material3:material3'
}
"""

    # Write files to disk
    files = {
        "settings.gradle": settings_gradle,
        "gradle.properties": gradle_properties,
        "build.gradle": root_build_gradle,
        "app/build.gradle": app_build_gradle
    }

    print("📝 Writing Gradle configuration files...")
    for path, content in files.items():
        try:
            with open(path, "w") as f:
                f.write(content.strip())
            print(f"✅ Generated: {path}")
        except Exception as e:
            print(f"❌ Failed to write {path}: {e}")

if __name__ == "__main__":
    generate_gradle_files()
