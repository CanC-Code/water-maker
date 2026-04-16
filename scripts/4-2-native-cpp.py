import os

def generate():
    # Ensure the directory matches where CMake is looking
    cpp_dir = "app/src/main/cpp"
    os.makedirs(cpp_dir, exist_ok=True)

    cpp_content = r"""#include <jni.h>
#include <android/bitmap.h>
#include <android/log.h>
#include <cmath>
#include <algorithm>

#define LOG_TAG "NativeEngine"
#define LOGE(...) __android_log_print(ANDROID_LOG_ERROR, LOG_TAG, __VA_ARGS__)

extern "C"
JNIEXPORT void JNICALL
Java_com_watermarker_NativeEngine_processWatermark(
        JNIEnv* env, jobject thiz,
        jobject base_bmp, jobject overlay_bmp,
        jfloat offset_x, jfloat offset_y,
        jfloat scale, jfloat rotation_deg, jfloat alpha) {

    AndroidBitmapInfo baseInfo;
    AndroidBitmapInfo overInfo;
    void* basePixels;
    void* overPixels;

    if (AndroidBitmap_getInfo(env, base_bmp, &baseInfo) < 0 ||
        AndroidBitmap_getInfo(env, overlay_bmp, &overInfo) < 0) return;

    if (AndroidBitmap_lockPixels(env, base_bmp, &basePixels) < 0 ||
        AndroidBitmap_lockPixels(env, overlay_bmp, &overPixels) < 0) return;

    uint32_t* basePtr = (uint32_t*)basePixels;
    uint32_t* overPtr = (uint32_t*)overPixels;

    float angle = rotation_deg * M_PI / 180.0f;
    float cosA = cos(angle);
    float sinA = sin(angle);

    // Pivot around the center of the overlay
    float centerX = overInfo.width / 2.0f;
    float centerY = overInfo.height / 2.0f;

    for (int y = 0; y < baseInfo.height; ++y) {
        for (int x = 0; x < baseInfo.width; ++x) {
            // Translate point to overlay coordinate space
            float tx = x - offset_x - baseInfo.width / 2.0f;
            float ty = y - offset_y - baseInfo.height / 2.0f;

            // Apply inverse scale and rotation to find source pixel in overlay
            float rx = (tx * cosA + ty * sinA) / scale + centerX;
            float ry = (-tx * sinA + ty * cosA) / scale + centerY;

            if (rx >= 0 && rx < overInfo.width && ry >= 0 && ry < overInfo.height) {
                uint32_t overPixel = overPtr[(int)ry * overInfo.width + (int)rx];
                uint8_t aO = ((overPixel >> 24) & 0xFF) * alpha;
                
                if (aO > 0) {
                    uint32_t basePixel = basePtr[y * baseInfo.width + x];
                    
                    uint8_t rB = (basePixel >> 0) & 0xFF;
                    uint8_t gB = (basePixel >> 8) & 0xFF;
                    uint8_t bB = (basePixel >> 16) & 0xFF;

                    uint8_t rO = (overPixel >> 0) & 0xFF;
                    uint8_t gO = (overPixel >> 8) & 0xFF;
                    uint8_t bO = (overPixel >> 16) & 0xFF;

                    // Standard alpha blending formula
                    float blend = aO / 255.0f;
                    uint8_t rF = (uint8_t)(rO * blend + rB * (1.0f - blend));
                    uint8_t gF = (uint8_t)(gO * blend + gB * (1.0f - blend));
                    uint8_t bF = (uint8_t)(bO * blend + bB * (1.0f - blend));

                    basePtr[y * baseInfo.width + x] = (0xFF << 24) | (bF << 16) | (gF << 8) | rF;
                }
            }
        }
    }

    AndroidBitmap_unlockPixels(env, base_bmp);
    AndroidBitmap_unlockPixels(env, overlay_bmp);
}
"""
    with open(f"{cpp_dir}/native-engine.cpp", "w") as f:
        f.write(cpp_content)
    print("✅ 4-2 Generated native-engine.cpp (Native Pixel Logic)")

if __name__ == "__main__":
    generate()
