import os

def generate_native():
    cmake = """
cmake_minimum_required(VERSION 3.22.1)
project("watermarker")
add_library(watermarker SHARED native-lib.cpp)
find_library(log-lib log)
find_library(jnigraphics-lib jnigraphics)
target_link_libraries(watermarker ${log-lib} ${jnigraphics-lib})
"""

    cpp = """
#include <jni.h>
#include <android/bitmap.h>

extern "C" JNIEXPORT void JNICALL
Java_com_watermarker_NativeEngine_blendImages(JNIEnv* env, jobject thiz, jobject base, jobject overlay, jfloat x, jfloat y, jfloat scale, jfloat rotation, jfloat opacity) {
    // Native pixel merge bridge
}
"""

    files = {
        "app/src/main/cpp/CMakeLists.txt": cmake.strip(),
        "app/src/main/cpp/native-lib.cpp": cpp.strip()
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Native Engine bridge complete.")

if __name__ == "__main__":
    generate_native()
