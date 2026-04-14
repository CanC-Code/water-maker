import os

def generate_ui():
    package_path = "app/src/main/java/com/watermarker"
    
    # --- 1. Application Class ---
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
}
"""

    # --- 2. App Open Ad Manager ---
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
        
        val adUnitId = "ca-app-pub-3940256099942544/3419835294"
        val request = AdRequest.Builder().build()
        
        AppOpenAd.load(
            context, adUnitId, request,
            object : AppOpenAd.AppOpenAdLoadCallback() {
                override fun onAdLoaded(ad: AppOpenAd) {
                    appOpenAd = ad
                    isLoadingAd = false
                }
                override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                    isLoadingAd = false
                }
            }
        )
    }
}
"""

    # --- 3. Native Engine Wrapper ---
    engine_content = """package com.watermarker

class NativeEngine {
    init {
        System.loadLibrary("watermarker")
    }
    external fun processWatermark(baseImagePath: String, overlayImagePath: String, outputPath: String, quality: Int): Boolean
}
"""

    # --- 4. Main Activity & Compose UI ---
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
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.io.File
import java.io.FileOutputStream
import kotlin.math.*

@Composable
fun ColorWheel(onColorSelected: (Color) -> Unit) {
    var currentPosition by remember { mutableStateOf(Offset.Unspecified) }
    val wheelRadius = 100.dp
    
    Canvas(modifier = Modifier
        .size(wheelRadius * 2)
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
                val saturation = dist / radius
                val hsv = floatArrayOf(angle.toFloat(), saturation.toFloat(), 1f)
                val colorInt = android.graphics.Color.HSVToColor(hsv)
                onColorSelected(Color(colorInt))
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
            // Dynamic Theme State
            val systemDark = isSystemInDarkTheme()
            var isDarkMode by remember { mutableStateOf(systemDark) }
            val colorScheme = if (isDarkMode) darkColorScheme() else lightColorScheme()

            MaterialTheme(colorScheme = colorScheme) {
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
                    
                    // Base Image State
                    var baseRotation by remember { mutableStateOf(0f) }

                    // Overlay Transform States
                    var overlayOffset by remember { mutableStateOf(Offset.Zero) }
                    var overlayScale by remember { mutableStateOf(1f) }
                    var overlayRotation by remember { mutableStateOf(0f) }
                    
                    val context = LocalContext.current
                    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> 
                        baseImageUri = uri 
                        baseRotation = 0f
                    }
                    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> 
                        overlayImageUri = uri
                        overlayOffset = Offset.Zero
                        overlayScale = 1f
                        overlayRotation = 0f
                    }
                    val fontPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                        uri?.let {
                            try {
                                val inputStream = context.contentResolver.openInputStream(it)
                                val tempFile = File(context.cacheDir, "custom_font.ttf")
                                FileOutputStream(tempFile).use { out -> inputStream?.copyTo(out) }
                                customTypeface = Typeface.createFromFile(tempFile)
                                Toast.makeText(context, "Custom Font loaded successfully!", Toast.LENGTH_SHORT).show()
                            } catch (e: Exception) {
                                Toast.makeText(context, "Failed to load font file.", Toast.LENGTH_SHORT).show()
                            }
                        }
                    }

                    Scaffold(
                        topBar = {
                            TopAppBar(
                                title = { Text("WaterMaker") },
                                colors = TopAppBarDefaults.topAppBarColors(
                                    containerColor = MaterialTheme.colorScheme.primaryContainer,
                                    titleContentColor = MaterialTheme.colorScheme.onPrimaryContainer
                                ),
                                actions = {
                                    IconButton(onClick = { showMenu = true }) { Icon(Icons.Default.Menu, contentDescription = "Menu") }
                                    DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
                                        DropdownMenuItem(text = { Text("Toggle Theme (Light/Dark)") }, onClick = { showMenu = false; isDarkMode = !isDarkMode })
                                        Divider()
                                        DropdownMenuItem(text = { Text("Load Base Image") }, onClick = { showMenu = false; basePicker.launch("image/*") })
                                        DropdownMenuItem(text = { Text("Load Overlay Image") }, onClick = { showMenu = false; overlayPicker.launch("image/*") })
                                        DropdownMenuItem(text = { Text("Add Text Overlay") }, onClick = { showMenu = false; showTextDialog = true })
                                        DropdownMenuItem(text = { Text("Import Font (.ttf)") }, onClick = { showMenu = false; fontPicker.launch("*/*") })
                                    }
                                }
                            )
                        }
                    ) { paddingValues ->
                        Column(
                            modifier = Modifier.fillMaxSize().padding(paddingValues).padding(16.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            if (showTextDialog) {
                                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                                    Column(modifier = Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                        Text("Create Text Overlay", style = MaterialTheme.typography.titleMedium)
                                        Spacer(modifier = Modifier.height(8.dp))
                                        OutlinedTextField(value = overlayText, onValueChange = { overlayText = it }, label = { Text("Type text here") }, modifier = Modifier.fillMaxWidth())
                                        Spacer(modifier = Modifier.height(16.dp))
                                        Text("Drag to pick a color:")
                                        Spacer(modifier = Modifier.height(8.dp))
                                        ColorWheel { color -> overlayTextColor = color }
                                        Spacer(modifier = Modifier.height(16.dp))
                                        Button(onClick = {
                                            showTextDialog = false
                                            if (overlayText.isNotEmpty()) {
                                                val bitmap = createTextBitmap(overlayText, overlayTextColor.toArgb(), customTypeface)
                                                val tempFile = File(context.cacheDir, "text_overlay.png")
                                                FileOutputStream(tempFile).use { out -> bitmap.compress(Bitmap.CompressFormat.PNG, 100, out) }
                                                overlayImageUri = Uri.fromFile(tempFile)
                                                
                                                // Reset overlay transforms for new text
                                                overlayOffset = Offset.Zero
                                                overlayScale = 1f
                                                overlayRotation = 0f
                                                
                                                Toast.makeText(context, "Text overlay generated!", Toast.LENGTH_SHORT).show()
                                            }
                                        }) { Text("Apply Text Overlay") }
                                    }
                                }
                            }

                            // --- PREVIEW CANVAS WORK AREA ---
                            val canvasBgColor = if (isDarkMode) Color(0xFF2D2D2D) else Color(0xFFE0E0E0)
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .weight(1f) // Takes up remaining middle space
                                    .background(canvasBgColor) 
                                    .clipToBounds()
                            ) {
                                val baseBitmap = remember(baseImageUri) { loadBitmapFromUri(context, baseImageUri) }
                                val overlayBitmap = remember(overlayImageUri) { loadBitmapFromUri(context, overlayImageUri) }

                                if (baseBitmap != null) {
                                    Image(
                                        bitmap = baseBitmap,
                                        contentDescription = "Base Image",
                                        modifier = Modifier
                                            .fillMaxSize()
                                            .rotate(baseRotation), // Rotate base image
                                        contentScale = ContentScale.Fit
                                    )
                                } else {
                                    Text(
                                        "Load a base image from the menu",
                                        modifier = Modifier.align(Alignment.Center),
                                        color = if (isDarkMode) Color.LightGray else Color.DarkGray
                                    )
                                }

                                if (overlayBitmap != null) {
                                    Image(
                                        bitmap = overlayBitmap,
                                        contentDescription = "Overlay Image",
                                        modifier = Modifier
                                            .offset { IntOffset(overlayOffset.x.roundToInt(), overlayOffset.y.roundToInt()) }
                                            .graphicsLayer(
                                                scaleX = overlayScale,
                                                scaleY = overlayScale,
                                                rotationZ = overlayRotation
                                            )
                                            .pointerInput(Unit) {
                                                detectTransformGestures { _, pan, zoom, rotation ->
                                                    overlayOffset += pan
                                                    overlayScale = (overlayScale * zoom).coerceIn(0.1f, 10f) // Allow scaling from 10% to 1000%
                                                    overlayRotation += rotation
                                                }
                                            }
                                    )
                                }
                            }
                            
                            // Base Image Controls
                            Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.End) {
                                OutlinedButton(
                                    onClick = { baseRotation += 90f },
                                    enabled = baseImageUri != null
                                ) {
                                    Text("Rotate Base 90°")
                                }
                            }
                            
                            Spacer(modifier = Modifier.height(10.dp))
                            Text("Export Quality: ${exportQuality.toInt()}%")
                            Slider(value = exportQuality, onValueChange = { exportQuality = it }, valueRange = 10f..100f, enabled = outputFormat != "PNG")
                            Spacer(modifier = Modifier.height(10.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("Output Format:")
                                Spacer(modifier = Modifier.width(8.dp))
                                listOf("JPEG", "PNG", "WEBP").forEach { format ->
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        RadioButton(selected = outputFormat == format, onClick = { outputFormat = format })
                                        Text(format, fontSize = 14.sp)
                                    }
                                }
                            }
                            Spacer(modifier = Modifier.height(10.dp))
                            Button(
                                onClick = { Toast.makeText(context, "Ready for Native Engine...", Toast.LENGTH_SHORT).show() },
                                modifier = Modifier.fillMaxWidth().height(50.dp)
                            ) { Text("PROCESS WATERMARK") }
                        }
                    }
                }
            }
        }
    }
    
    private fun loadBitmapFromUri(context: Context, uri: Uri?): ImageBitmap? {
        if (uri == null) return null
        return try {
            val stream = context.contentResolver.openInputStream(uri)
            BitmapFactory.decodeStream(stream)?.asImageBitmap()
        } catch (e: Exception) {
            null
        }
    }

    private fun createTextBitmap(text: String, color: Int, typeface: Typeface?): Bitmap {
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            this.color = color
            this.textSize = 200f
            this.typeface = typeface ?: Typeface.DEFAULT
            this.textAlign = Paint.Align.CENTER
        }
        val baseline = -paint.ascent()
        val width = (paint.measureText(text) + 60).toInt()
        val height = (baseline + paint.descent() + 60).toInt()
        val bmpWidth = if(width > 0) width else 100
        val bmpHeight = if(height > 0) height else 100
        val bitmap = Bitmap.createBitmap(bmpWidth, bmpHeight, Bitmap.Config.ARGB_8888)
        val canvas = android.graphics.Canvas(bitmap)
        canvas.drawText(text, bmpWidth / 2f, baseline + 30f, paint)
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

    print("🎨 Generating UI with Free Overlay Transform, Base Rotation, and Dark Mode...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Complete: Rebuild your project to test the new controls!")

if __name__ == "__main__":
    generate_ui()
