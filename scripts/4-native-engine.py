import os

def generate_native_engine():
    cpp_dir = "app/src/main/cpp"
    os.makedirs(cpp_dir, exist_ok=True)
    
    cmake_content = """cmake_minimum_required(VERSION 3.18.1)
project("watermarker")

add_library(watermarker SHARED watermarker.cpp)

find_library(log-lib log)
target_link_libraries(watermarker ${log-lib} jnigraphics)
"""

    cpp_content = """#include <jni.h>
#include <android/log.h>
#include <android/bitmap.h>
#include <cmath>
#include <algorithm>

#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, "NativeEngine", __VA_ARGS__)

uint32_t getPixelBilinear(uint32_t* img, int width, int height, float x, float y) {
    int x1 = std::floor(x);
    int y1 = std::floor(y);
    int x2 = std::min(x1 + 1, width - 1);
    int y2 = std::min(y1 + 1, height - 1);

    if (x1 < 0 || x1 >= width || y1 < 0 || y1 >= height) return 0; 

    float dx = x - x1;
    float dy = y - y1;

    uint32_t p11 = img[y1 * width + x1];
    uint32_t p21 = img[y1 * width + x2];
    uint32_t p12 = img[y2 * width + x1];
    uint32_t p22 = img[y2 * width + x2];

    auto blend = [&](int shift) {
        float c11 = (p11 >> shift) & 0xFF;
        float c21 = (p21 >> shift) & 0xFF;
        float c12 = (p12 >> shift) & 0xFF;
        float c22 = (p22 >> shift) & 0xFF;
        return (uint32_t)((c11 * (1 - dx) * (1 - dy)) + (c21 * dx * (1 - dy)) +
                          (c12 * (1 - dx) * dy) + (c22 * dx * dy));
    };

    uint32_t a = blend(24);
    uint32_t r = blend(16);
    uint32_t g = blend(8);
    uint32_t b = blend(0);

    return (a << 24) | (r << 16) | (g << 8) | b;
}

extern "C" JNIEXPORT jboolean JNICALL
Java_com_watermarker_NativeEngine_processWatermark(JNIEnv* env, jobject,
                                                   jobject baseBitmap,
                                                   jobject overlayBitmap,
                                                   jfloat realOffsetX, jfloat realOffsetY,
                                                   jfloat realOverScale, jfloat overlayRotation,
                                                   jfloat overlayAlpha) {
    
    AndroidBitmapInfo baseInfo, overInfo;
    void* basePixels;
    void* overPixels;

    if (AndroidBitmap_getInfo(env, baseBitmap, &baseInfo) < 0 ||
        AndroidBitmap_getInfo(env, overlayBitmap, &overInfo) < 0) return JNI_FALSE;

    if (baseInfo.format != ANDROID_BITMAP_FORMAT_RGBA_8888 ||
        overInfo.format != ANDROID_BITMAP_FORMAT_RGBA_8888) return JNI_FALSE;

    if (AndroidBitmap_lockPixels(env, baseBitmap, &basePixels) < 0) return JNI_FALSE;
    if (AndroidBitmap_lockPixels(env, overlayBitmap, &overPixels) < 0) {
        AndroidBitmap_unlockPixels(env, baseBitmap);
        return JNI_FALSE;
    }

    uint32_t* baseData = (uint32_t*)basePixels;
    uint32_t* overData = (uint32_t*)overPixels;

    int baseW = baseInfo.width;
    int baseH = baseInfo.height;
    int overW = overInfo.width;
    int overH = overInfo.height;

    float rad = overlayRotation * M_PI / 180.0f;
    float cosR = std::cos(-rad);
    float sinR = std::sin(-rad);

    float cx = (overW * realOverScale) / 2.0f;
    float cy = (overH * realOverScale) / 2.0f;
    
    // UI gives us exact offsets relative to the center of the base image!
    float overlayCenterX = (baseW / 2.0f) + realOffsetX;
    float overlayCenterY = (baseH / 2.0f) + realOffsetY;

    // Rendering Loop
    for (int y = 0; y < baseH; ++y) {
        for (int x = 0; x < baseW; ++x) {
            float px = x - overlayCenterX;
            float py = y - overlayCenterY;

            float srcX = px * cosR - py * sinR + cx;
            float srcY = px * sinR + py * cosR + cy;

            float origSrcX = srcX / realOverScale;
            float origSrcY = srcY / realOverScale;

            if (origSrcX >= 0 && origSrcX < overW - 1 && origSrcY >= 0 && origSrcY < overH - 1) {
                uint32_t pxl = getPixelBilinear(overData, overW, overH, origSrcX, origSrcY);
                uint8_t a = (pxl >> 24) & 0xFF;
                
                if (a > 0) {
                    float alpha = (a / 255.0f) * overlayAlpha;
                    uint8_t sr = (pxl >> 16) & 0xFF;
                    uint8_t sg = (pxl >> 8) & 0xFF;
                    uint8_t sb = pxl & 0xFF;

                    uint32_t basePxl = baseData[y * baseW + x];
                    uint8_t br = (basePxl >> 16) & 0xFF;
                    uint8_t bg = (basePxl >> 8) & 0xFF;
                    uint8_t bb = basePxl & 0xFF;

                    uint8_t nr = (uint8_t)((sr * alpha) + (br * (1 - alpha)));
                    uint8_t ng = (uint8_t)((sg * alpha) + (bg * (1 - alpha)));
                    uint8_t nb = (uint8_t)((sb * alpha) + (bb * (1 - alpha)));

                    baseData[y * baseW + x] = (255 << 24) | (nr << 16) | (ng << 8) | nb;
                }
            }
        }
    }

    AndroidBitmap_unlockPixels(env, baseBitmap);
    AndroidBitmap_unlockPixels(env, overlayBitmap);

    return JNI_TRUE;
}
"""
    files = {
        f"{cpp_dir}/CMakeLists.txt": cmake_content.strip(),
        f"{cpp_dir}/watermarker.cpp": cpp_content.strip(),
    }
    for path, content in files.items():
        with open(path, "w") as f:
            f.write(content)
    print("✅ Fixed Native Engine generated with absolute alignment math!")

if __name__ == "__main__":
    generate_native_engine()
