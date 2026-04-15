import os

def generate_ui():
    package_path = "app/src/main/java/com/watermarker"
    
    app_class_content = """package com.watermarker
import android.app.Application
import com.google.android.gms.ads.MobileAds
class WaterMarkerApp : Application() {
    lateinit var appOpenAdManager: AppOpenAdManager
    override fun onCreate() {
        super.onCreate()
        MobileAds.initialize(this) {}
        appOpenAdManager = AppOpenAdManager(this)
        appOpenAdManager.loadAd()
    }
}"""

    ad_manager_content = """package com.watermarker
import android.content.Context
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.appopen.AppOpenAd
class AppOpenAdManager(private val context: Context) {
    private var appOpenAd: AppOpenAd? = null
    private var isLoadingAd = false
    fun loadAd() {
        if (isLoadingAd || appOpenAd != null) return
        isLoadingAd = true
        val request = AdRequest.Builder().build()
        AppOpenAd.load(context, "ca-app-pub-3940256099942544/3419835294", request,
            object : AppOpenAd.AppOpenAdLoadCallback() {
                override fun onAdLoaded(ad: AppOpenAd) { appOpenAd = ad; isLoadingAd = false }
                override fun onAdFailedToLoad(e: LoadAdError) { isLoadingAd = false }
            }
        )
    }
}"""

    # JNI Signature accepts Android Bitmaps directly!
    engine_content = """package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    init { System.loadLibrary("watermarker") }
    external fun processWatermark(baseBitmap: Bitmap, overlayBitmap: Bitmap,
                                  overlayX: Float, overlayY: Float, overlayScale: Float, overlayRotation: Float,
                                  overlayAlpha: Float, previewWidth: Float, previewHeight: Float): Boolean
}"""

    main_activity_content = r"""package com.watermarker

import android.content.Context
import android.graphics.*
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.ImageBitmap
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import kotlin.math.*

@Composable
fun ColorWheel(onColorSelected: (Color) -> Unit) {
    var currentPosition by remember { mutableStateOf(Offset.Unspecified) }
    Canvas(modifier = Modifier
        .size(200.dp)
        .pointerInput(Unit) { detectDragGestures { change, _ -> currentPosition = change.position } }
        .pointerInput(Unit) { detectTapGestures { offset -> currentPosition = offset } }
    ) {
        val center = Offset(size.width / 2f, size.height / 2f)
        val radius = size.minDimension / 2f
        val colors = listOf(Color.Red, Color.Magenta, Color.Blue, Color.Cyan, Color.Green, Color.Yellow, Color.Red)
        drawCircle(brush = Brush.sweepGradient(colors, center = center), radius = radius, center = center)
        drawCircle(brush = Brush.radialGradient(listOf(Color.White, Color.Transparent), center = center, radius = radius), radius = radius, center = center)
        if (currentPosition != Offset.Unspecified) {
            val dx = currentPosition.x - center.x
            val dy = currentPosition.y - center.y
            val dist = sqrt(dx*dx + dy*dy)
            if (dist <= radius) {
                val angle = (atan2(dy.toDouble(), dx.toDouble()) * 180 / PI + 360) % 360
                val hsv = floatArrayOf(angle.toFloat(), (dist / radius).toFloat(), 1f)
                onColorSelected(Color(android.graphics.Color.HSVToColor(hsv)))
                drawCircle(color = Color.Black, radius = 15f, center = currentPosition, style = Stroke(width = 4f))
            }
        }
    }
}

class MainActivity : ComponentActivity() {
    private val nativeEngine = NativeEngine()
    
    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            val systemDark = isSystemInDarkTheme()
            var isDarkMode by remember { mutableStateOf(systemDark) }
            
            MaterialTheme(colorScheme = if (isDarkMode) darkColorScheme() else lightColorScheme()) {
                Surface(color = MaterialTheme.colorScheme.background) {
                    var showMenu by remember { mutableStateOf(false) }
                    var baseImageUri by remember { mutableStateOf<Uri?>(null) }
                    var overlayImageUri by remember { mutableStateOf<Uri?>(null) }
                    var showTextDialog by remember { mutableStateOf(false) }
                    var overlayText by remember { mutableStateOf("") }
                    var overlayTextColor by remember { mutableStateOf(Color.Black) }
                    var customTypeface by remember { mutableStateOf<Typeface?>(null) }
                    var exportQuality by remember { mutableStateOf(100f) }
                    var outputFormat by remember { mutableStateOf("JPEG") }
                    
                    var baseRotation by remember { mutableStateOf(0f) }
                    var overlayOffset by remember { mutableStateOf(Offset.Zero) }
                    var overlayScale by remember { mutableStateOf(1f) }
                    var overlayRotation by remember { mutableStateOf(0f) }
                    var overlayAlpha by remember { mutableStateOf(1f) } 
                    
                    var previewWidth by remember { mutableStateOf(1f) }
                    var previewHeight by remember { mutableStateOf(1f) }
                    
                    val context = LocalContext.current
                    val coroutineScope = rememberCoroutineScope()
                    
                    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> baseImageUri = uri; baseRotation = 0f }
                    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> overlayImageUri = uri; overlayOffset = Offset.Zero; overlayScale = 1f; overlayRotation = 0f }
                    val fontPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                        uri?.let {
                            try {
                                val tempFile = File(context.cacheDir, "custom_font.ttf")
                                FileOutputStream(tempFile).use { out -> context.contentResolver.openInputStream(it)?.copyTo(out) }
                                customTypeface = Typeface.createFromFile(tempFile)
                                Toast.makeText(context, "Font loaded!", Toast.LENGTH_SHORT).show()
                            } catch (e: Exception) { Toast.makeText(context, "Failed to load font.", Toast.LENGTH_SHORT).show() }
                        }
                    }

                    Scaffold(
                        topBar = {
                            TopAppBar(
                                title = { Text("WaterMarker") },
                                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                                actions = {
                                    IconButton(onClick = { showMenu = true }) { Icon(Icons.Default.Menu, "Menu") }
                                    DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
                                        DropdownMenuItem(text = { Text("Toggle Theme") }, onClick = { showMenu = false; isDarkMode = !isDarkMode })
                                        HorizontalDivider()
                                        DropdownMenuItem(text = { Text("Load Base Image") }, onClick = { showMenu = false; basePicker.launch("image/*") })
                                        DropdownMenuItem(text = { Text("Load Overlay Image") }, onClick = { showMenu = false; overlayPicker.launch("image/*") })
                                        DropdownMenuItem(text = { Text("Add Text Overlay") }, onClick = { showMenu = false; showTextDialog = true })
                                        DropdownMenuItem(text = { Text("Import Font (.ttf)") }, onClick = { showMenu = false; fontPicker.launch("*/*") })
                                    }
                                }
                            )
                        }
                    ) { paddingValues ->
                        Column(modifier = Modifier.fillMaxSize().padding(paddingValues).padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                            if (showTextDialog) {
                                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                                    Column(modifier = Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                        Text("Create Text", style = MaterialTheme.typography.titleMedium)
                                        OutlinedTextField(value = overlayText, onValueChange = { overlayText = it }, label = { Text("Type text") })
                                        Spacer(modifier = Modifier.height(16.dp))
                                        ColorWheel { color -> overlayTextColor = color }
                                        Spacer(modifier = Modifier.height(16.dp))
                                        Button(onClick = {
                                            showTextDialog = false
                                            if (overlayText.isNotEmpty()) {
                                                val bmp = createTextBitmap(overlayText, overlayTextColor.toArgb(), customTypeface)
                                                val tempFile = File(context.cacheDir, "text.png")
                                                FileOutputStream(tempFile).use { out -> bmp.compress(Bitmap.CompressFormat.PNG, 100, out) }
                                                overlayImageUri = Uri.fromFile(tempFile)
                                                overlayOffset = Offset.Zero; overlayScale = 1f; overlayRotation = 0f
                                            }
                                        }) { Text("Apply") }
                                    }
                                }
                            }

                            Box(modifier = Modifier.fillMaxWidth().weight(1f).background(if (isDarkMode) Color(0xFF2D2D2D) else Color(0xFFE0E0E0)).clipToBounds()
                                .onGloballyPositioned { coordinates ->
                                    previewWidth = coordinates.size.width.toFloat()
                                    previewHeight = coordinates.size.height.toFloat()
                                }) {
                                val baseBitmap = remember(baseImageUri) { loadBitmapFromUri(context, baseImageUri) }
                                val overlayBitmap = remember(overlayImageUri) { loadBitmapFromUri(context, overlayImageUri) }
                                if (baseBitmap != null) {
                                    Image(bitmap = baseBitmap, contentDescription = null, modifier = Modifier.fillMaxSize().rotate(baseRotation), contentScale = ContentScale.Fit)
                                }
                                if (overlayBitmap != null) {
                                    Image(bitmap = overlayBitmap, contentDescription = null, modifier = Modifier
                                        .graphicsLayer(translationX = overlayOffset.x, translationY = overlayOffset.y, scaleX = overlayScale, scaleY = overlayScale, rotationZ = overlayRotation, alpha = overlayAlpha)
                                        .pointerInput(Unit) {
                                            detectTransformGestures { _, pan, zoom, rotation ->
                                                overlayOffset += pan
                                                overlayScale = (overlayScale * zoom).coerceIn(0.1f, 10f)
                                                overlayRotation += rotation
                                            }
                                        }
                                    )
                                }
                            }
                            
                            Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.End) {
                                OutlinedButton(onClick = { baseRotation += 90f }, enabled = baseImageUri != null) { Text("Rotate Base 90°") }
                            }
                            
                            Spacer(modifier = Modifier.height(10.dp))
                            
                            Text("Opacity Layer: ${(overlayAlpha * 100).toInt()}%", fontSize = 12.sp)
                            Slider(value = overlayAlpha, onValueChange = { overlayAlpha = it }, valueRange = 0f..1f)
                            
                            Text("Export Quality: ${exportQuality.toInt()}%", fontSize = 12.sp)
                            Slider(value = exportQuality, onValueChange = { exportQuality = it }, valueRange = 10f..100f, enabled = outputFormat != "PNG")
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                listOf("JPEG", "PNG", "WEBP").forEach { format ->
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        RadioButton(selected = outputFormat == format, onClick = { outputFormat = format })
                                        Text(format, fontSize = 14.sp)
                                    }
                                }
                            }
                            
                            Spacer(modifier = Modifier.height(10.dp))
                            Button(
                                onClick = { 
                                    if (baseImageUri != null && overlayImageUri != null) {
                                        Toast.makeText(context, "Processing purely in Native memory...", Toast.LENGTH_SHORT).show()
                                        coroutineScope.launch(Dispatchers.IO) {
                                            try {
                                                // Load Bitmaps strictly into ARGB_8888 for JNI support
                                                val mutableBase = prepareBaseImageBitmap(context, baseImageUri!!, baseRotation)
                                                val overlayBmp = loadStrictBitmap(context, overlayImageUri!!)
                                                
                                                if (mutableBase == null || overlayBmp == null) {
                                                    withContext(Dispatchers.Main) { Toast.makeText(context, "❌ Error loading image memory.", Toast.LENGTH_LONG).show() }
                                                    return@launch
                                                }
                                                
                                                // Execute C++ directly on the RAM blocks!
                                                val success = try {
                                                    nativeEngine.processWatermark(mutableBase, overlayBmp, overlayOffset.x, overlayOffset.y, 
                                                        overlayScale, overlayRotation, overlayAlpha, previewWidth, previewHeight)
                                                } catch (t: Throwable) {
                                                    false
                                                }
                                                
                                                withContext(Dispatchers.Main) {
                                                    if (success) {
                                                        // Convert modified RAM directly to file
                                                        val outputPath = File(context.cacheDir, "final.${outputFormat.lowercase()}").absolutePath
                                                        FileOutputStream(outputPath).use { out ->
                                                            val cf = if (outputFormat == "PNG") Bitmap.CompressFormat.PNG else Bitmap.CompressFormat.JPEG
                                                            mutableBase.compress(cf, exportQuality.toInt(), out)
                                                        }
                                                        
                                                        val savedUri = saveToGallery(context, File(outputPath), "Watermark_${System.currentTimeMillis()}.${outputFormat.lowercase()}")
                                                        if (savedUri != null) Toast.makeText(context, "✅ Saved to Gallery!", Toast.LENGTH_LONG).show()
                                                    } else {
                                                        Toast.makeText(context, "❌ Native Engine Error.", Toast.LENGTH_LONG).show()
                                                    }
                                                }
                                            } catch (e: Exception) {
                                                withContext(Dispatchers.Main) { Toast.makeText(context, "❌ Crash Prevented.", Toast.LENGTH_LONG).show() }
                                            }
                                        }
                                    }
                                },
                                modifier = Modifier.fillMaxWidth().height(50.dp)
                            ) { Text("PROCESS WATERMARK") }
                        }
                    }
                }
            }
        }
    }
    
    // UI Preview Loader
    private fun loadBitmapFromUri(context: Context, uri: Uri?): ImageBitmap? {
        if (uri == null) return null
        return try { BitmapFactory.decodeStream(context.contentResolver.openInputStream(uri))?.asImageBitmap() } catch (e: Exception) { null }
    }

    // Engine Loaders (Strict ARGB_8888 mapping)
    private fun loadStrictBitmap(context: Context, uri: Uri): Bitmap? {
        return try {
            val options = BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.ARGB_8888; inMutable = false }
            BitmapFactory.decodeStream(context.contentResolver.openInputStream(uri), null, options)
        } catch (e: Exception) { null }
    }

    private fun prepareBaseImageBitmap(context: Context, uri: Uri, rotation: Float): Bitmap? {
        return try {
            val options = BitmapFactory.Options().apply { inPreferredConfig = Bitmap.Config.ARGB_8888; inMutable = true }
            val bitmap = BitmapFactory.decodeStream(context.contentResolver.openInputStream(uri), null, options) ?: return null
            
            if (rotation != 0f) {
                val matrix = Matrix().apply { postRotate(rotation) }
                Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
            } else {
                // Must explicitly copy to guarantee mutability for JNI
                bitmap.copy(Bitmap.Config.ARGB_8888, true)
            }
        } catch (e: Exception) { null }
    }

    private fun saveToGallery(context: Context, file: File, fileName: String): Uri? {
        val values = android.content.ContentValues().apply {
            put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME, fileName)
            put(android.provider.MediaStore.MediaColumns.MIME_TYPE, "image/${file.extension}")
            put(android.provider.MediaStore.MediaColumns.RELATIVE_PATH, android.os.Environment.DIRECTORY_PICTURES + "/WaterMarker")
        }
        return try {
            val uri = context.contentResolver.insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
            uri?.also { destUri ->
                context.contentResolver.openOutputStream(destUri)?.use { out ->
                    file.inputStream().use { input -> input.copyTo(out) }
                }
            }
        } catch (e: Exception) { null }
    }

    private fun createTextBitmap(text: String, color: Int, typeface: Typeface?): Bitmap {
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { this.color = color; this.textSize = 200f; this.typeface = typeface ?: Typeface.DEFAULT; this.textAlign = Paint.Align.CENTER }
        val baseline = -paint.ascent()
        val width = (paint.measureText(text) + 60).toInt()
        val height = (baseline + paint.descent() + 60).toInt()
        val bmpWidth = if(width > 0) width else 100
        val bmpHeight = if(height > 0) height else 100
        val bitmap = Bitmap.createBitmap(bmpWidth, bmpHeight, Bitmap.Config.ARGB_8888)
        android.graphics.Canvas(bitmap).drawText(text, bmpWidth / 2f, baseline + 30f, paint)
        return bitmap
    }
}
"""

    files = {
        f"{package_path}/WaterMarkerApp.kt": app_class_content.strip(),
        f"{package_path}/AppOpenAdManager.kt": ad_manager_content.strip(),
        f"{package_path}/NativeEngine.kt": engine_content.strip(),
        f"{package_path}/MainActivity.kt": main_activity_content.strip()
    }

    print("🎨 Generating UI synced directly to Native Memory Engine...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)

if __name__ == "__main__":
    generate_ui()
