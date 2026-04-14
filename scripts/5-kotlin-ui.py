import os

def generate_ui():
    package_path = "app/src/main/java/com/watermarker"
    
    main_activity_content = r"""package com.watermarker

import android.content.Context
import android.graphics.*
import android.net.Uri
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import java.io.File
import java.io.FileOutputStream
import kotlin.math.*

// --- Custom Color Wheel Component ---
@Composable
fun ColorWheel(onColorSelected: (Color) -> Unit) {
    var currentPosition by remember { mutableStateOf(Offset.Unspecified) }
    val wheelRadius = 100.dp
    
    Canvas(modifier = Modifier
        .size(wheelRadius * 2)
        .pointerInput(Unit) {
            detectDragGestures { change, _ ->
                currentPosition = change.position
            }
        }
        .pointerInput(Unit) {
            detectTapGestures { offset ->
                currentPosition = offset
            }
        }
    ) {
        val center = Offset(size.width / 2f, size.height / 2f)
        val radius = size.minDimension / 2f
        
        // Hue sweep gradient
        val colors = listOf(Color.Red, Color.Magenta, Color.Blue, Color.Cyan, Color.Green, Color.Yellow, Color.Red)
        drawCircle(
            brush = Brush.sweepGradient(colors, center = center),
            radius = radius,
            center = center
        )
        // Saturation radial gradient (White in center -> Transparent at edges)
        drawCircle(
            brush = Brush.radialGradient(
                colors = listOf(Color.White, Color.Transparent),
                center = center,
                radius = radius
            ),
            radius = radius,
            center = center
        )
        
        // Calculate color if touched
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
                
                // Draw the touch indicator
                drawCircle(color = Color.Black, radius = 15f, center = currentPosition, style = Stroke(width = 4f))
            }
        }
    }
}

class MainActivity : ComponentActivity() {
    
    @OptIn(ExperimentalMaterial3Api::class)
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                var showMenu by remember { mutableStateOf(false) }
                var baseImageUri by remember { mutableStateOf<Uri?>(null) }
                var overlayImageUri by remember { mutableStateOf<Uri?>(null) }
                
                var showTextDialog by remember { mutableStateOf(false) }
                var overlayText by remember { mutableStateOf("") }
                var overlayTextColor by remember { mutableStateOf(Color.Black) }
                var customTypeface by remember { mutableStateOf<Typeface?>(null) }
                
                var exportQuality by remember { mutableStateOf(100f) }
                var outputFormat by remember { mutableStateOf("JPEG") }
                
                val context = LocalContext.current

                // Launchers for picking files
                val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> baseImageUri = uri }
                val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> overlayImageUri = uri }
                
                val fontPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                    uri?.let {
                        try {
                            val inputStream = context.contentResolver.openInputStream(it)
                            val tempFile = File(context.cacheDir, "custom_font.ttf")
                            FileOutputStream(tempFile).use { out -> inputStream?.copyTo(out) }
                            customTypeface = Typeface.createFromFile(tempFile)
                            Toast.makeText(context, "Custom Font loaded successfully!", Toast.LENGTH_SHORT).show()
                        } catch (e: Exception) {
                            e.printStackTrace()
                            Toast.makeText(context, "Failed to load font file.", Toast.LENGTH_SHORT).show()
                        }
                    }
                }

                Scaffold(
                    topBar = {
                        TopAppBar(
                            title = { Text("WaterMaker") },
                            actions = {
                                IconButton(onClick = { showMenu = true }) {
                                    Icon(Icons.Default.Menu, contentDescription = "Menu")
                                }
                                DropdownMenu(
                                    expanded = showMenu,
                                    onDismissRequest = { showMenu = false }
                                ) {
                                    DropdownMenuItem(
                                        text = { Text("Load Base Image") },
                                        onClick = { showMenu = false; basePicker.launch("image/*") }
                                    )
                                    DropdownMenuItem(
                                        text = { Text("Load Overlay Image") },
                                        onClick = { showMenu = false; overlayPicker.launch("image/*") }
                                    )
                                    DropdownMenuItem(
                                        text = { Text("Add Text Overlay") },
                                        onClick = { showMenu = false; showTextDialog = true }
                                    )
                                    DropdownMenuItem(
                                        text = { Text("Import Font (.ttf)") },
                                        onClick = { showMenu = false; fontPicker.launch("*/*") }
                                    )
                                }
                            }
                        )
                    }
                ) { paddingValues ->
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(paddingValues)
                            .padding(16.dp),
                        horizontalAlignment = Alignment.CenterHorizontally
                    ) {
                        
                        // Text Creation Card
                        if (showTextDialog) {
                            Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                                Column(modifier = Modifier.padding(16.dp), horizontalAlignment = Alignment.CenterHorizontally) {
                                    Text("Create Text Overlay", style = MaterialTheme.typography.titleMedium)
                                    Spacer(modifier = Modifier.height(8.dp))
                                    OutlinedTextField(
                                        value = overlayText,
                                        onValueChange = { overlayText = it },
                                        label = { Text("Type text here") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Spacer(modifier = Modifier.height(16.dp))
                                    Text("Drag to pick a color:")
                                    Spacer(modifier = Modifier.height(8.dp))
                                    ColorWheel { color ->
                                        overlayTextColor = color
                                    }
                                    Spacer(modifier = Modifier.height(16.dp))
                                    Button(onClick = {
                                        showTextDialog = false
                                        if (overlayText.isNotEmpty()) {
                                            // Convert text and selected font to a Bitmap image
                                            val bitmap = createTextBitmap(overlayText, overlayTextColor.toArgb(), customTypeface)
                                            val tempFile = File(context.cacheDir, "text_overlay.png")
                                            FileOutputStream(tempFile).use { out ->
                                                bitmap.compress(Bitmap.CompressFormat.PNG, 100, out)
                                            }
                                            // Set the text image as our overlay
                                            overlayImageUri = Uri.fromFile(tempFile)
                                            Toast.makeText(context, "Text overlay generated!", Toast.LENGTH_SHORT).show()
                                        }
                                    }) {
                                        Text("Apply Text Overlay")
                                    }
                                }
                            }
                        }

                        Spacer(modifier = Modifier.height(20.dp))
                        Text("Base Image Selected: ${baseImageUri != null}", fontSize = 14.sp)
                        Text("Overlay Selected: ${overlayImageUri != null}", fontSize = 14.sp)
                        Text("Custom Font Loaded: ${customTypeface != null}", fontSize = 14.sp)
                        
                        Spacer(modifier = Modifier.height(30.dp))
                        Text("Export Quality: ${exportQuality.toInt()}%")
                        Slider(
                            value = exportQuality,
                            onValueChange = { exportQuality = it },
                            valueRange = 10f..100f,
                            enabled = outputFormat != "PNG",
                            colors = SliderDefaults.colors(
                                thumbColor = Color(0xFF38BDF8),
                                activeTrackColor = Color(0xFF38BDF8)
                            )
                        )
                        
                        Spacer(modifier = Modifier.height(10.dp))
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text("Output Format:")
                            Spacer(modifier = Modifier.width(8.dp))
                            listOf("JPEG", "PNG", "WEBP").forEach { format ->
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    RadioButton(
                                        selected = outputFormat == format,
                                        onClick = { outputFormat = format }
                                    )
                                    Text(format, fontSize = 14.sp)
                                }
                            }
                        }
                        
                        Spacer(modifier = Modifier.weight(1f))
                        Button(
                            onClick = {
                                Toast.makeText(context, "Sending to Native Engine...", Toast.LENGTH_SHORT).show()
                                // Call your existing NativeEngine wrapper here
                            },
                            modifier = Modifier.fillMaxWidth().height(50.dp)
                        ) {
                            Text("PROCESS WATERMARK")
                        }
                    }
                }
            }
        }
    }
    
    // Renders the user's string into a transparent PNG bitmap
    private fun createTextBitmap(text: String, color: Int, typeface: Typeface?): Bitmap {
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            this.color = color
            this.textSize = 200f // Large enough resolution
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
        
        // Draw the text in the center
        canvas.drawText(text, bmpWidth / 2f, baseline + 30f, paint)
        return bitmap
    }
}
"""

    files = {
        f"{package_path}/MainActivity.kt": main_activity_content.strip()
    }

    print("🎨 Updating Kotlin UI with Hamburger Menu, Color Wheel, and Custom Font rendering...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Complete: You can now rebuild your project to see the new UI tools.")

if __name__ == "__main__":
    generate_ui()
