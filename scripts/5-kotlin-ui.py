import os

def generate_ui():
    engine_content = """package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    companion object { init { System.loadLibrary("watermarker") } }
    external fun blendImages(base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float)
}
"""

    main_activity_content = """package com.watermarker

import android.content.ContentValues
import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.Matrix
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.MediaStore
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { WaterMarkerUI() }
    }
}

@Composable
fun WaterMarkerUI() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var baseBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var activeOverlay by remember { mutableStateOf<Bitmap?>(null) }
    var isSaving by remember { mutableStateOf(false) }

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { baseBitmap = decodeUri(context, it) }
    }

    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { activeOverlay = decodeUri(context, it) }
    }

    Column(modifier = Modifier.fillMaxSize().background(Color.Black)) {
        Button(onClick = { basePicker.launch("image/*") }) { Text("Load Image") }
        Button(onClick = { overlayPicker.launch("image/*") }) { Text("Load Overlay") }
        
        Button(onClick = {
            if (baseBitmap != null && activeOverlay != null) {
                scope.launch {
                    isSaving = true
                    saveFullResolution(context, baseBitmap!!, activeOverlay!!, 0f, 0f, 1f, 0f, 0.8f, 0f)
                    isSaving = false
                }
            }
        }) {
            Text(if (isSaving) "Saving..." else "Save APK")
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return context.contentResolver.openInputStream(uri)?.use { 
        BitmapFactory.decodeStream(it)
    }
}

suspend fun saveFullResolution(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float, baseRotation: Float) {
    withContext(Dispatchers.Default) {
        val finalBase = base.copy(Bitmap.Config.ARGB_8888, true)
        NativeEngine().blendImages(finalBase, overlay, x, y, scale, rotation, opacity)
        // ... storage logic ...
        withContext(Dispatchers.Main) { Toast.makeText(context, "Saved", Toast.LENGTH_SHORT).show() }
    }
}
"""

    package_path = "app/src/main/java/com/watermarker"
    files = {
        f"{package_path}/NativeEngine.kt": engine_content.strip(),
        f"{package_path}/MainActivity.kt": main_activity_content.strip()
    }

    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Kotlin UI updated.")

if __name__ == "__main__":
    generate_ui()
