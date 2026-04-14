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
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { WaterMarkerUI() }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WaterMarkerUI() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    val snackbarHostState = remember { SnackbarHostState() }
    
    var baseBitmap by remember { mutableStateOf<Bitmap?>(null) }
    var activeOverlay by remember { mutableStateOf<Bitmap?>(null) }
    
    // UI & Transformation State
    var fileName by remember { mutableStateOf("MyWatermark") }
    var outputFormat by remember { mutableStateOf("PNG") }
    var overlayX by remember { mutableStateOf(0f) }
    var overlayY by remember { mutableStateOf(0f) }
    var overlayScale by remember { mutableStateOf(1f) }
    var overlayRotation by remember { mutableStateOf(0f) }
    var baseRotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(1.0f) }
    var isSaving by remember { mutableStateOf(false) }

    val formats = listOf("PNG", "JPG", "WEBP")

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { 
            baseBitmap = decodeUri(context, it)
            baseRotation = 0f // Reset rotation on new image
        }
    }
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { 
            activeOverlay = decodeUri(context, it)
            overlayX = 0f
            overlayY = 0f
            overlayScale = 1f
            overlayRotation = 0f
        }
    }

    Scaffold(
        snackbarHost = { SnackbarHost(snackbarHostState) },
        containerColor = Color(0xFF020617)
    ) { paddingValues ->
        Column(modifier = Modifier.fillMaxSize().padding(paddingValues)) {
            
            // 1. Toolbar
            Row(
                modifier = Modifier.fillMaxWidth().padding(8.dp), 
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Button(onClick = { basePicker.launch("image/*") }) { Text("SUBJECT", fontSize = 11.sp) }
                IconButton(onClick = { baseRotation = (baseRotation + 90f) % 360f }) {
                    Icon(Icons.Default.Refresh, "Rotate Subject", tint = Color.White)
                }
                Button(onClick = { overlayPicker.launch("image/*") }) { Text("OVERLAY", fontSize = 11.sp) }
            }

            // 2. The Workspace Canvas
            BoxWithConstraints(modifier = Modifier.weight(1f).fillMaxWidth().background(Color.Black).clipToBounds()) {
                val constraints = this
                baseBitmap?.let { base ->
                    
                    // Account for rotation when calculating fit-to-screen
                    val isPortrait = (baseRotation / 90f) % 2 != 0f
                    val bw = if (isPortrait) base.height else base.width
                    val bh = if (isPortrait) base.width else base.height

                    val canvasRatio = constraints.maxWidth.value / constraints.maxHeight.value
                    val imageRatio = bw.toFloat() / bh.toFloat()
                    
                    val fitScale = if (imageRatio > canvasRatio) {
                        constraints.maxWidth.value / bw.toFloat()
                    } else {
                        constraints.maxHeight.value / bh.toFloat()
                    }

                    Canvas(modifier = Modifier.fillMaxSize().pointerInput(Unit) {
                        detectTransformGestures { _, pan, zoom, rot ->
                            overlayX += pan.x / fitScale
                            overlayY += pan.y / fitScale
                            overlayScale *= zoom
                            overlayRotation += rot
                        }
                    }) {
                        drawContext.canvas.save()
                        drawContext.canvas.translate(size.width / 2f, size.height / 2f)
                        drawContext.canvas.scale(fitScale, fitScale)

                        // Draw the Base (Subject) Image with rotation
                        drawContext.canvas.save()
                        drawContext.canvas.rotate(baseRotation)
                        drawImage(base.asImageBitmap(), dstOffset = IntOffset(-base.width / 2, -base.height / 2))
                        drawContext.canvas.restore()

                        // Draw Overlay relative to Base center
                        activeOverlay?.let { over ->
                            drawContext.canvas.save()
                            drawContext.canvas.translate(overlayX, overlayY)
                            drawContext.canvas.rotate(overlayRotation)
                            drawContext.canvas.scale(overlayScale, overlayScale)
                            drawImage(
                                over.asImageBitmap(), 
                                alpha = opacity,
                                dstOffset = IntOffset(-over.width / 2, -over.height / 2)
                            )
                            drawContext.canvas.restore()
                        }
                        drawContext.canvas.restore()
                    }
                } ?: Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                    Text("Load a subject image to begin", color = Color.Gray)
                }
            }

            // 3. QOL Footer Controls
            Card(
                modifier = Modifier.fillMaxWidth(), 
                colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)),
                shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp)
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    
                    // Filename Input
                    OutlinedTextField(
                        value = fileName,
                        onValueChange = { fileName = it },
                        label = { Text("Filename") },
                        modifier = Modifier.fillMaxWidth(),
                        singleLine = true,
                        colors = OutlinedTextFieldDefaults.colors(
                            unfocusedTextColor = Color.White, 
                            focusedTextColor = Color.White,
                            unfocusedLabelColor = Color.Gray,
                            focusedLabelColor = Color(0xFF38BDF8)
                        )
                    )
                    
                    Spacer(Modifier.height(8.dp))
                    
                    // Format Selector
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                        Text("Format:", color = Color.White, fontWeight = FontWeight.Bold)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            formats.forEach { format ->
                                FilterChip(
                                    selected = outputFormat == format,
                                    onClick = { outputFormat = format },
                                    label = { Text(format) },
                                    colors = FilterChipDefaults.filterChipColors(
                                        selectedContainerColor = Color(0xFF38BDF8),
                                        selectedLabelColor = Color(0xFF020617)
                                    )
                                )
                            }
                        }
                    }

                    Spacer(Modifier.height(8.dp))
                    
                    // Opacity Slider
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Opacity", color = Color.Gray)
                        Text("${(opacity * 100).toInt()}%", color = Color(0xFF38BDF8))
                    }
                    Slider(value = opacity, onValueChange = { opacity = it }, colors = SliderDefaults.colors(thumbColor = Color(0xFF38BDF8), activeTrackColor = Color(0xFF38BDF8)))
                    
                    // Save Button
                    Button(
                        onClick = {
                            if (baseBitmap != null && activeOverlay != null) {
                                scope.launch {
                                    isSaving = true
                                    val success = saveCustomFormat(context, baseBitmap!!, activeOverlay!!, overlayX, overlayY, overlayScale, overlayRotation, opacity, baseRotation, fileName, outputFormat)
                                    isSaving = false
                                    
                                    if(success) {
                                        snackbarHostState.showSnackbar("Image successfully exported!")
                                    } else {
                                        snackbarHostState.showSnackbar("Failed to export image.")
                                    }
                                }
                            } else {
                                scope.launch { snackbarHostState.showSnackbar("Please load both images first.") }
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
                    ) {
                        Text(if (isSaving) "PROCESSING..." else "EXPORT IMAGE", color = Color(0xFF020617), fontWeight = FontWeight.ExtraBold)
                    }
                }
            }
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return try {
        context.contentResolver.openInputStream(uri)?.use { 
            BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply { inMutable = true })
        }
    } catch (e: Exception) { null }
}

suspend fun saveCustomFormat(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, s: Float, r: Float, a: Float, baseRot: Float, name: String, format: String): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            // 1. Handle Source Rotation
            val matrixBase = Matrix()
            matrixBase.postRotate(baseRot)
            val finalBase = Bitmap.createBitmap(base, 0, 0, base.width, base.height, matrixBase, true)

            // 2. Prepare the Canvas
            val result = finalBase.copy(Bitmap.Config.ARGB_8888, true)
            val canvas = Canvas(result)
            
            // JPG Fix: Draw white background to replace alpha transparency
            if (format == "JPG") {
                canvas.drawColor(android.graphics.Color.WHITE)
                canvas.drawBitmap(finalBase, 0f, 0f, null)
            }

            val paint = Paint().apply { 
                alpha = (a * 255).toInt()
                isFilterBitmap = true 
            }
            
            // 3. Align the Overlay correctly
            val matrixOverlay = Matrix()
            matrixOverlay.postTranslate(-overlay.width / 2f, -overlay.height / 2f)
            matrixOverlay.postScale(s, s)
            matrixOverlay.postRotate(r)
            matrixOverlay.postTranslate(result.width / 2f + x, result.height / 2f + y)
            
            canvas.drawBitmap(overlay, matrixOverlay, paint)

            // 4. File Setup
            val cleanName = name.replace("[^a-zA-Z0-9]".toRegex(), "_")
            val ext = format.lowercase()
            val mime = "image/${if (ext == "jpg") "jpeg" else ext}"
            
            val compressFormat = when (format) {
                "JPG" -> Bitmap.CompressFormat.JPEG
                "PNG" -> Bitmap.CompressFormat.PNG
                "WEBP" -> if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) Bitmap.CompressFormat.WEBP_LOSSLESS else Bitmap.CompressFormat.WEBP
                else -> Bitmap.CompressFormat.PNG
            }

            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, "$cleanName.$ext")
                put(MediaStore.MediaColumns.MIME_TYPE, mime)
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                    put(MediaStore.MediaColumns.RELATIVE_PATH, "Pictures/WaterMarker")
                }
            }

            // 5. Write to Disk
            val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
            uri?.let {
                context.contentResolver.openOutputStream(it)?.use { stream ->
                    result.compress(compressFormat, 100, stream)
                }
            }
            true
        } catch (e: Exception) {
            false
        }
    }
}
"""

    package_path = "app/src/main/java/com/watermarker"
    files = {
        f"{package_path}/NativeEngine.kt": engine_content.strip(),
        f"{package_path}/MainActivity.kt": main_activity_content.strip()
    }

    print("🎨 Updating GUI...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Studio UI updated: Format selection, Source Rotation, and Snackbars added.")

if __name__ == "__main__":
    generate_ui()
