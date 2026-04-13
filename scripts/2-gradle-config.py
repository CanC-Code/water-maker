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
kotlin.code.style=official
"""

    # 3. Root build.gradle
    root_build_gradle = """
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:8.7.0'
        classpath 'org.jetbrains.kotlin:kotlin-gradle-plugin:2.1.0'
        classpath 'org.jetbrains.kotlin:compose-compiler-gradle-plugin:2.1.0'
    }
}
"""

    # 4. app/build.gradle (Added Material & AppCompat dependencies)
    app_build_gradle = """
plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
    id 'org.jetbrains.kotlin.plugin.compose'
}

android {
    namespace 'com.watermarker'
    compileSdk 35

    defaultConfig {
        applicationId "com.watermarker"
        minSdk 24
        targetSdk 35
        versionCode 1
        versionName "1.0"

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
    
    applicationVariants.all { variant ->
        variant.outputs.all {
            outputFileName = "water-marker.apk"
        }
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.15.0'
    implementation 'androidx.appcompat:appcompat:1.7.0'
    implementation 'com.google.android.material:material:1.12.0'
    implementation 'androidx.lifecycle:lifecycle-runtime-ktx:2.8.0'
    implementation 'androidx.activity:activity-compose:1.10.0'
    implementation platform('androidx.compose:compose-bom:2025.02.00')
    implementation 'androidx.compose.ui:ui'
    implementation 'androidx.compose.ui:ui-graphics'
    implementation 'androidx.compose.material3:material3'
}
"""

    files = {
        "settings.gradle": settings_gradle,
        "gradle.properties": gradle_properties,
        "build.gradle": root_build_gradle,
        "app/build.gradle": app_build_gradle
    }

    print("📝 Updating Gradle dependencies to include Material XML themes...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, "w") as f:
            f.write(content.strip())
    print("✅ Dependencies updated.")

if __name__ == "__main__":
    generate_gradle_files()
