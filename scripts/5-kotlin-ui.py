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
import android.graphics.*
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
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
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
    
    var overlayX by remember { mutableStateOf(0f) }
    var overlayY by remember { mutableStateOf(0f) }
    var overlayScale by remember { mutableStateOf(0.5f) }
    var overlayRotation by remember { mutableStateOf(0f) }
    var baseRotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(0.8f) }
    var isSaving by remember { mutableStateOf(false) }

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { baseBitmap = decodeUri(context, it) }
    }
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { activeOverlay = decodeUri(context, it) }
    }

    Column(modifier = Modifier.fillMaxSize().background(Color(0xFF020617))) {
        Row(modifier = Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.SpaceBetween) {
            Button(onClick = { basePicker.launch("image/*") }) { Text("LOAD IMAGE", fontSize = 10.sp) }
            Button(onClick = { overlayPicker.launch("image/*") }) { Text("LOAD OVERLAY", fontSize = 10.sp) }
            IconButton(onClick = { baseRotation = (baseRotation + 90f) % 360f }) {
                Icon(Icons.Default.Refresh, "Rotate", tint = Color.White)
            }
        }

        Box(modifier = Modifier.weight(1f).fillMaxWidth().clipToBounds()
            .pointerInput(Unit) {
                detectTransformGestures { _, pan, zoom, rot ->
                    overlayX += pan.x
                    overlayY += pan.y
                    overlayScale *= zoom
                    overlayRotation += rot
                }
            }
        ) {
            baseBitmap?.let { base ->
                Canvas(modifier = Modifier.fillMaxSize()) {
                    val canvasWidth = size.width
                    val canvasHeight = size.height
                    
                    drawContext.canvas.save()
                    drawContext.canvas.translate(canvasWidth / 2f, canvasHeight / 2f)
                    drawContext.canvas.rotate(baseRotation)
                    drawImage(base.asImageBitmap(), dstOffset = androidx.compose.ui.unit.IntOffset(-(base.width/2), -(base.height/2)))
                    drawContext.canvas.restore()

                    activeOverlay?.let { over ->
                        drawContext.canvas.save()
                        drawContext.canvas.translate(canvasWidth / 2f + overlayX, canvasHeight / 2f + overlayY)
                        drawContext.canvas.rotate(overlayRotation)
                        drawContext.canvas.scale(overlayScale, overlayScale)
                        drawImage(over.asImageBitmap(), alpha = opacity, dstOffset = androidx.compose.ui.unit.IntOffset(-(over.width/2), -(over.height/2)))
                        drawContext.canvas.restore()
                    }
                }
            }
        }

        Column(modifier = Modifier.background(Color(0xFF0F172A)).padding(16.dp)) {
            Slider(value = opacity, onValueChange = { opacity = it })
            Button(
                onClick = {
                    if (baseBitmap != null && activeOverlay != null) {
                        scope.launch {
                            isSaving = true
                            saveFullResolution(context, baseBitmap!!, activeOverlay!!, overlayX, overlayY, overlayScale, overlayRotation, opacity, baseRotation)
                            isSaving = false
                        }
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
            ) {
                Text(if (isSaving) "SAVING..." else "SAVE WATERMARKED IMAGE")
            }
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return try {
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it) }
    } catch (e: Exception) { null }
}

suspend fun saveFullResolution(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, s: Float, r: Float, a: Float, br: Float) {
    withContext(Dispatchers.IO) {
        val result = base.copy(Bitmap.Config.ARGB_8888, true)
        NativeEngine().blendImages(result, overlay, x, y, s, r, a)
        
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.DISPLAY_NAME, "WM_${System.currentTimeMillis()}.png")
            put(MediaStore.MediaColumns.MIME_TYPE, "image/png")
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                put(MediaStore.MediaColumns.RELATIVE_PATH, "Pictures/WaterMarker")
            }
        }

        val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
        uri?.let {
            context.contentResolver.openOutputStream(it)?.use { stream ->
                result.compress(Bitmap.CompressFormat.PNG, 100, stream)
            }
        }
        withContext(Dispatchers.Main) { Toast.makeText(context, "Saved to Gallery", Toast.LENGTH_SHORT).show() }
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
    print("✅ Kotlin UI with Canvas and gestures updated.")

if __name__ == "__main__":
    generate_ui()
