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
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.OutputStream

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

    Column(modifier = Modifier.fillMaxSize().background(Color(0xFF020617)).padding(16.dp),
           horizontalAlignment = Alignment.CenterHorizontally,
           verticalArrangement = Arrangement.Center) {
        
        Button(onClick = { basePicker.launch("image/*") }) { Text("1. LOAD SUBJECT IMAGE") }
        Spacer(modifier = Modifier.height(10.dp))
        Button(onClick = { overlayPicker.launch("image/*") }) { Text("2. LOAD OVERLAY") }
        Spacer(modifier = Modifier.height(30.dp))
        
        Button(
            onClick = {
                if (baseBitmap != null && activeOverlay != null) {
                    scope.launch {
                        isSaving = true
                        saveFullResolution(context, baseBitmap!!, activeOverlay!!, 0f, 0f, 0.5f, 0f, 0.8f)
                        isSaving = false
                    }
                } else {
                    Toast.makeText(context, "Please select both images", Toast.LENGTH_SHORT).show()
                }
            },
            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
        ) {
            Text(if (isSaving) "PROCESSING..." else "SAVE WATERMARKED IMAGE")
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return try {
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) }
    } catch (e: Exception) { null }
}

suspend fun saveFullResolution(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float) {
    withContext(Dispatchers.Default) {
        // Create a copy to work on
        val finalBitmap = base.copy(Bitmap.Config.ARGB_8888, true)
        
        // Apply Native Blending
        NativeEngine().blendImages(finalBitmap, overlay, x, y, scale, rotation, opacity)

        // Metadata for the image file
        val filename = "WM_${System.currentTimeMillis()}.png"
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, filename)
            put(MediaStore.MediaColumns.MIME_TYPE, "image/png")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.MediaColumns.RELATIVE_PATH, "Pictures/WaterMarker")
            }
        }

        val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
        
        try {
            uri?.let {
                context.contentResolver.openOutputStream(it)?.use { stream ->
                    finalBitmap.compress(Bitmap.CompressFormat.PNG, 100, stream)
                }
            }
            withContext(Dispatchers.Main) {
                Toast.makeText(context, "Image Saved to Gallery!", Toast.LENGTH_LONG).show()
            }
        } catch (e: Exception) {
            withContext(Dispatchers.Main) {
                Toast.makeText(context, "Error saving image", Toast.LENGTH_SHORT).show()
            }
        }
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
    print("✅ Kotlin UI and Saving Logic updated.")

if __name__ == "__main__":
    generate_ui()
