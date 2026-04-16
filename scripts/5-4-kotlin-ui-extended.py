import os

def generate():
    package_path = "app/src/main/java/com/watermarker"
    os.makedirs(package_path, exist_ok=True)

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
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.gestures.detectDragGestures
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.ArrowForward
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clipToBounds
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.asComposePath
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.layout.onGloballyPositioned
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.io.File
import java.io.FileOutputStream
import kotlin.math.*

// GLOBAL STATE SNAPSHOT FOR UNDO/REDO ENGINE
data class GlobalSnapshot(
    val overlayImageUri: Uri?,
    val overlayText: String,
    val drawingImageUri: Uri?,
    val drawPaths: List<DrawStroke>,
    val overlayOffset: Offset,
    val overlayScale: Float,
    val overlayRotation: Float,
    val drawingOffset: Offset,
    val drawingScale: Float,
    val drawingRotation: Float
)

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
        val colors = listOf(Color.Red, Color.Yellow, Color.Green, Color.Cyan, Color.Blue, Color.Magenta, Color.Red)
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
                    var showInventory by remember { mutableStateOf(false) }
                    var showColorPickerDialog by remember { mutableStateOf(false) }
                    var activeColorContext by remember { mutableStateOf("text") } 

                    var isEyedropperMode by remember { mutableStateOf(false) }
                    var returnToTextDialog by remember { mutableStateOf(false) }

                    var baseImageUri by remember { mutableStateOf<Uri?>(null) }
                    var overlayImageUri by remember { mutableStateOf<Uri?>(null) }
                    var drawingImageUri by remember { mutableStateOf<Uri?>(null) }

                    var showTextDialog by remember { mutableStateOf(false) }
                    var overlayText by remember { mutableStateOf("") }
                    var overlayTextColor by remember { mutableStateOf(Color.Black) }
                    var overlayTextBend by remember { mutableStateOf(0f) }
                    var customTypeface by remember { mutableStateOf<Typeface?>(null) }

                    var isDrawingMode by remember { mutableStateOf(false) }
                    var drawPaths by remember { mutableStateOf(listOf<DrawStroke>()) }
                    var redoPaths by remember { mutableStateOf(listOf<DrawStroke>()) }
                    var currentDrawStroke by remember { mutableStateOf(listOf<Offset>()) }
                    var drawColor by remember { mutableStateOf(Color.Red) }
                    var drawStrokeWidth by remember { mutableStateOf(15f) }

                    var exportQuality by remember { mutableStateOf(100f) }
                    var outputFormat by remember { mutableStateOf("JPEG") }
                    var outputFileName by remember { mutableStateOf("") }

                    var overlayOffset by remember { mutableStateOf(Offset.Zero) }
                    var overlayScale by remember { mutableStateOf(1f) }
                    var overlayRotation by remember { mutableStateOf(0f) }
                    
                    var drawingOffset by remember { mutableStateOf(Offset.Zero) }
                    var drawingScale by remember { mutableStateOf(1f) }
                    var drawingRotation by remember { mutableStateOf(0f) }
                    
                    var baseRotation by remember { mutableStateOf(0f) }
                    var overlayAlpha by remember { mutableStateOf(1f) }

                    var activeLayer by remember { mutableStateOf("Text") }
                    var isLocked by remember { mutableStateOf(false) }

                    var previewWidth by remember { mutableStateOf(1f) }
                    var previewHeight by remember { mutableStateOf(1f) }

                    // GLOBAL HISTORY STACKS (MAX 10)
                    var undoStack by remember { mutableStateOf(listOf<GlobalSnapshot>()) }
                    var redoStack by remember { mutableStateOf(listOf<GlobalSnapshot>()) }

                    val captureSnapshot = {
                        GlobalSnapshot(
                            overlayImageUri, overlayText, drawingImageUri, drawPaths,
                            overlayOffset, overlayScale, overlayRotation,
                            drawingOffset, drawingScale, drawingRotation
                        )
                    }

                    val saveHistory = {
                        undoStack = (undoStack + captureSnapshot()).takeLast(10)
                        redoStack = emptyList()
                    }

                    val performUndo = {
                        if (undoStack.isNotEmpty()) {
                            val current = captureSnapshot()
                            redoStack = (listOf(current) + redoStack).take(10)
                            val prev = undoStack.last()
                            undoStack = undoStack.dropLast(1)
                            
                            overlayImageUri = prev.overlayImageUri
                            overlayText = prev.overlayText
                            drawingImageUri = prev.drawingImageUri
                            drawPaths = prev.drawPaths
                            overlayOffset = prev.overlayOffset
                            overlayScale = prev.overlayScale
                            overlayRotation = prev.overlayRotation
                            drawingOffset = prev.drawingOffset
                            drawingScale = prev.drawingScale
                            drawingRotation = prev.drawingRotation
                        }
                    }

                    val performRedo = {
                        if (redoStack.isNotEmpty()) {
                            val current = captureSnapshot()
                            undoStack = (undoStack + current).takeLast(10)
                            val next = redoStack.first()
                            redoStack = redoStack.drop(1)
                            
                            overlayImageUri = next.overlayImageUri
                            overlayText = next.overlayText
                            drawingImageUri = next.drawingImageUri
                            drawPaths = next.drawPaths
                            overlayOffset = next.overlayOffset
                            overlayScale = next.overlayScale
                            overlayRotation = next.overlayRotation
                            drawingOffset = next.drawingOffset
                            drawingScale = next.drawingScale
                            drawingRotation = next.drawingRotation
                        }
                    }

                    val context = LocalContext.current
                    val coroutineScope = rememberCoroutineScope()

                    val inventoryDir = remember { File(context.filesDir, "saved_overlays").apply { mkdirs() } }
                    var savedOverlays by remember { mutableStateOf(inventoryDir.listFiles()?.toList() ?: emptyList()) }
                    fun refreshInventory() { savedOverlays = inventoryDir.listFiles()?.toList() ?: emptyList() }

                    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> baseImageUri = uri; baseRotation = 0f }
                    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
                        if (uri != null) {
                            saveHistory()
                            overlayImageUri = uri; overlayOffset = Offset.Zero; overlayScale = 1f; overlayRotation = 0f; overlayText = ""
                            activeLayer = "Text"
                        }
                    }
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

                    if (showColorPickerDialog) {
                        AlertDialog(
                            onDismissRequest = { showColorPickerDialog = false },
                            title = { Text(if (activeColorContext == "text") "Text Color" else "Pen Color") },
                            text = {
                                Column(horizontalAlignment = Alignment.CenterHorizontally) {
                                    Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
                                        ColorWheel(onColorSelected = { 
                                            if (activeColorContext == "text") overlayTextColor = it else drawColor = it 
                                        })
                                    }
                                    Spacer(modifier = Modifier.height(16.dp))
                                    Button(onClick = { 
                                        showColorPickerDialog = false
                                        if (activeColorContext == "text") {
                                            showTextDialog = false
                                            returnToTextDialog = true
                                        }
                                        isEyedropperMode = true
                                    }) { Text("🎯 Pick from Image") }
                                }
                            },
                            confirmButton = { Button(onClick = { showColorPickerDialog = false }) { Text("Done") } }
                        )
                    }

                    if (showTextDialog) {
                        AlertDialog(
                            onDismissRequest = { showTextDialog = false },
                            title = { Text("Add Text Overlay") },
                            text = {
                                Column {
                                    OutlinedTextField(
                                        value = overlayText, 
                                        onValueChange = { overlayText = it }, 
                                        label = { Text("Enter text") },
                                        modifier = Modifier.fillMaxWidth()
                                    )
                                    Spacer(modifier = Modifier.height(16.dp))
                                    Text("Curve Text", fontSize = 12.sp)
                                    Slider(value = overlayTextBend, onValueChange = { overlayTextBend = it }, valueRange = -100f..100f)
                                    
                                    Spacer(modifier = Modifier.height(16.dp))
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text("Color:")
                                        Spacer(modifier = Modifier.width(16.dp))
                                        Box(modifier = Modifier
                                            .size(40.dp)
                                            .background(overlayTextColor, shape = CircleShape)
                                            .border(1.dp, Color.Gray, CircleShape)
                                            .clickable { 
                                                activeColorContext = "text"
                                                showColorPickerDialog = true 
                                            }
                                        )
                                    }
                                }
                            },
                            confirmButton = {
                                Button(onClick = {
                                    showTextDialog = false
                                    if (overlayText.isNotEmpty()) {
                                        saveHistory()
                                        val bmp = createTextBitmap(overlayText, overlayTextColor.toArgb(), customTypeface, overlayTextBend)
                                        overlayImageUri?.let { uri -> if (uri.path?.contains("cache/text_") == true) File(uri.path!!).delete() }
                                        val tempFile = File(context.cacheDir, "text_${System.currentTimeMillis()}.png")
                                        FileOutputStream(tempFile).use { out -> bmp.compress(Bitmap.CompressFormat.PNG, 100, out) }
                                        overlayImageUri = Uri.fromFile(tempFile)
                                        activeLayer = "Text"
                                    }
                                }) { Text("Apply Text") }
                            },
                            dismissButton = { TextButton(onClick = { showTextDialog = false }) { Text("Cancel") } }
                        )
                    }

                    Scaffold(
                        topBar = {
                            TopAppBar(
                                title = { Text(if (isDrawingMode) "Draw Overlay" else "Water Marker") },
                                colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.primaryContainer),
                                actions = {
                                    if (isDrawingMode) {
                                        if (drawPaths.isNotEmpty()) {
                                            IconButton(onClick = { 
                                                redoPaths = listOf(drawPaths.last()) + redoPaths
                                                drawPaths = drawPaths.dropLast(1) 
                                            }) { Icon(Icons.Default.ArrowBack, "Undo Stroke") }
                                        }
                                        if (redoPaths.isNotEmpty()) {
                                            IconButton(onClick = { 
                                                drawPaths = drawPaths + redoPaths.first()
                                                redoPaths = redoPaths.drop(1)
                                            }) { Icon(Icons.Default.ArrowForward, "Redo Stroke") }
                                        }
                                        IconButton(onClick = { 
                                            saveHistory()
                                            drawPaths = emptyList() 
                                            redoPaths = emptyList()
                                            drawingImageUri = null
                                        }) { Icon(Icons.Default.Clear, "Clear") }
                                        
                                        IconButton(onClick = {
                                            val baseBitmap = AppState.currentBaseBitmap
                                            if (drawPaths.isNotEmpty() && baseBitmap != null) {
                                                saveHistory()
                                                val bmp = createDrawingBitmap(drawPaths, baseBitmap.width, baseBitmap.height)
                                                val tempFile = File(context.cacheDir, "drawing_${System.currentTimeMillis()}.png")
                                                FileOutputStream(tempFile).use { out -> bmp.compress(Bitmap.CompressFormat.PNG, 100, out) }
                                                
                                                drawingImageUri = Uri.fromFile(tempFile)
                                                drawingOffset = Offset.Zero
                                                drawingScale = 1f
                                                drawingRotation = 0f
                                                activeLayer = "Pen"
                                            }
                                            isDrawingMode = false
                                        }) { Icon(Icons.Default.Check, "Save", tint = Color(0xFF10B981)) }
                                    } else {
                                        if (overlayImageUri != null || drawingImageUri != null) {
                                            IconButton(onClick = {
                                                saveHistory()
                                                if (overlayImageUri != null && drawingImageUri != null) {
                                                    if (activeLayer == "Text") {
                                                        overlayImageUri = null; overlayText = ""; activeLayer = "Pen"
                                                    } else {
                                                        drawingImageUri = null; drawPaths = emptyList(); redoPaths = emptyList(); activeLayer = "Text"
                                                    }
                                                } else if (overlayImageUri != null) {
                                                    overlayImageUri = null; overlayText = ""
                                                } else if (drawingImageUri != null) {
                                                    drawingImageUri = null; drawPaths = emptyList(); redoPaths = emptyList()
                                                }
                                                isLocked = false
                                                Toast.makeText(context, "Layer Removed", Toast.LENGTH_SHORT).show()
                                            }) { Icon(Icons.Default.Delete, "Remove Layer", tint = Color.Red) }
                                        }

                                        // GLOBAL UNDO ENGINE
                                        IconButton(onClick = { performUndo() }, enabled = undoStack.isNotEmpty()) {
                                            Icon(Icons.Default.ArrowBack, "Undo Layer Change", tint = if (undoStack.isNotEmpty()) MaterialTheme.colorScheme.onSurface else Color.Gray.copy(alpha = 0.4f))
                                        }
                                        
                                        // GLOBAL REDO ENGINE
                                        IconButton(onClick = { performRedo() }, enabled = redoStack.isNotEmpty()) {
                                            Icon(Icons.Default.ArrowForward, "Redo Layer Change", tint = if (redoStack.isNotEmpty()) MaterialTheme.colorScheme.onSurface else Color.Gray.copy(alpha = 0.4f))
                                        }

                                        IconButton(onClick = { showMenu = true }) { Icon(Icons.Default.Menu, "Menu") }
                                        DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false }) {
                                            DropdownMenuItem(text = { Text("Toggle Dark Mode") }, onClick = { showMenu = false; isDarkMode = !isDarkMode })
                                            HorizontalDivider()
                                            DropdownMenuItem(text = { Text("Load Main Image") }, onClick = { showMenu = false; basePicker.launch("image/*") })
                                            DropdownMenuItem(text = { Text("Load Image Overlay") }, onClick = { showMenu = false; overlayPicker.launch("image/*") })
                                            DropdownMenuItem(text = { Text("Add Text Overlay") }, onClick = { showMenu = false; showTextDialog = true })
                                            DropdownMenuItem(text = { Text("Draw Overlay") }, onClick = { showMenu = false; isDrawingMode = true }, enabled = baseImageUri != null)
                                            DropdownMenuItem(text = { Text("Saved Overlays") }, onClick = { showMenu = false; showInventory = true; refreshInventory() })
                                            DropdownMenuItem(text = { Text("Import Custom Font (.ttf)") }, onClick = { showMenu = false; fontPicker.launch("*/*") })
                                        }
                                    }
                                }
                            )
                        },
                        bottomBar = {
                            Surface(
                                color = MaterialTheme.colorScheme.surfaceVariant,
                                modifier = Modifier.fillMaxWidth()
                            ) {
                                Column(modifier = Modifier.padding(16.dp)) {
                                    if (isDrawingMode) {
                                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                            Text("Size: ${drawStrokeWidth.toInt()}", fontSize = 14.sp)
                                            Slider(
                                                value = drawStrokeWidth, 
                                                onValueChange = { drawStrokeWidth = it }, 
                                                valueRange = 5f..100f,
                                                modifier = Modifier.weight(1f).padding(horizontal = 16.dp)
                                            )
                                        }
                                        Spacer(modifier = Modifier.height(8.dp))
                                        
                                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {
                                            val quickColors = listOf(Color.Red, Color.Black, Color.White, Color.Blue, Color.Green, Color.Yellow)
                                            quickColors.forEach { col ->
                                                Box(modifier = Modifier
                                                    .size(36.dp)
                                                    .background(col, shape = CircleShape)
                                                    .clickable { drawColor = col }
                                                    .border(2.dp, if (drawColor == col) Color.Gray else Color.Transparent, CircleShape)
                                                )
                                            }
                                            Box(modifier = Modifier
                                                .size(36.dp)
                                                .background(Brush.sweepGradient(listOf(Color.Red, Color.Yellow, Color.Green, Color.Cyan, Color.Blue, Color.Magenta, Color.Red)), shape = CircleShape)
                                                .clickable { 
                                                    activeColorContext = "pen"
                                                    showColorPickerDialog = true 
                                                }
                                                .border(2.dp, if (!quickColors.contains(drawColor)) Color.DarkGray else Color.Transparent, CircleShape)
                                            )
                                            Button(
                                                onClick = { activeColorContext = "pen"; isEyedropperMode = true },
                                                modifier = Modifier.size(45.dp),
                                                contentPadding = PaddingValues(0.dp)
                                            ) { Text("🎯", fontSize = 18.sp) }
                                        }
                                    } else {
                                        if (overlayImageUri != null && drawingImageUri != null) {
                                            Row(
                                                modifier = Modifier
                                                    .fillMaxWidth()
                                                    .padding(bottom = 12.dp)
                                                    .background(MaterialTheme.colorScheme.background, CircleShape)
                                                    .border(1.dp, MaterialTheme.colorScheme.outline, CircleShape),
                                                horizontalArrangement = Arrangement.SpaceEvenly
                                            ) {
                                                val textBg = if (activeLayer == "Text" && !isLocked) MaterialTheme.colorScheme.primary else Color.Transparent
                                                val penBg = if (activeLayer == "Pen" && !isLocked) MaterialTheme.colorScheme.primary else Color.Transparent
                                                val lockBg = if (isLocked) MaterialTheme.colorScheme.primary else Color.Transparent

                                                TextButton(onClick = { activeLayer = "Text"; isLocked = false }, modifier = Modifier.weight(1f).background(textBg, CircleShape)) { Text("Move Text", color = if (activeLayer == "Text" && !isLocked) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface) }
                                                TextButton(onClick = { activeLayer = "Pen"; isLocked = false }, modifier = Modifier.weight(1f).background(penBg, CircleShape)) { Text("Move Pen", color = if (activeLayer == "Pen" && !isLocked) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface) }
                                                TextButton(onClick = { isLocked = true }, modifier = Modifier.weight(1f).background(lockBg, CircleShape)) { Text("🔒 Locked", color = if (isLocked) MaterialTheme.colorScheme.onPrimary else MaterialTheme.colorScheme.onSurface) }
                                            }
                                        }

                                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                            Button(onClick = {
                                                if (overlayImageUri != null) {
                                                    val destFile = File(inventoryDir, "overlay_${System.currentTimeMillis()}.png")
                                                    context.contentResolver.openInputStream(overlayImageUri!!)?.use { input -> destFile.outputStream().use { input.copyTo(it) } }
                                                    Toast.makeText(context, "Saved to Inventory!", Toast.LENGTH_SHORT).show()
                                                    refreshInventory()
                                                } else Toast.makeText(context, "No active overlay to save.", Toast.LENGTH_SHORT).show()
                                            }) { Text("Save Overlay") }
                                            OutlinedButton(onClick = { baseRotation = (baseRotation + 90f) % 360f }, enabled = baseImageUri != null) { Text("Rotate Base") }
                                        }

                                        Spacer(modifier = Modifier.height(10.dp))
                                        Text("Opacity: ${(overlayAlpha * 100).toInt()}%", fontSize = 12.sp)
                                        Slider(value = overlayAlpha, onValueChange = { overlayAlpha = it }, valueRange = 0f..1f)
                                        
                                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                                            Row(verticalAlignment = Alignment.CenterVertically) {
                                                listOf("JPEG", "PNG", "WEBP").forEach { format ->
                                                    Row(verticalAlignment = Alignment.CenterVertically) { 
                                                        RadioButton(selected = outputFormat == format, onClick = { outputFormat = format })
                                                        Text(format, fontSize = 12.sp) 
                                                    }
                                                }
                                            }
                                        }

                                        Spacer(modifier = Modifier.height(10.dp))

                                        // QOL: Custom File Name Input
                                        OutlinedTextField(
                                            value = outputFileName,
                                            onValueChange = { outputFileName = it },
                                            label = { Text("Output File Name (Optional)") },
                                            placeholder = { Text("e.g. MyWatermark") },
                                            singleLine = true,
                                            modifier = Modifier.fillMaxWidth()
                                        )

                                        Spacer(modifier = Modifier.height(10.dp))

                                        Button(
                                            onClick = {
                                                val baseBmp = AppState.currentBaseBitmap
                                                val overlayBmp = AppState.currentOverlayBitmap
                                                val drawingBmp = AppState.currentDrawingBitmap
                                                
                                                if (baseBmp != null) {
                                                    Toast.makeText(context, "Processing Image...", Toast.LENGTH_SHORT).show()
                                                    coroutineScope.launch(Dispatchers.IO) {
                                                        try {
                                                            val boxW = previewWidth
                                                            val boxH = previewHeight
                                                            val baseScaleUI = min(boxW / baseBmp.width, boxH / baseBmp.height)
                                                            val mutableBase = baseBmp.copy(Bitmap.Config.ARGB_8888, true)

                                                            if (overlayBmp != null) {
                                                                val processOverlay = overlayBmp.copy(Bitmap.Config.ARGB_8888, false)
                                                                val overScaleUI = min(boxW / overlayBmp.width, boxH / overlayBmp.height)
                                                                val realOverScale = (overScaleUI * overlayScale) / baseScaleUI
                                                                val realOffsetX = overlayOffset.x / baseScaleUI
                                                                val realOffsetY = overlayOffset.y / baseScaleUI
                                                                nativeEngine.processWatermark(mutableBase, processOverlay, realOffsetX, realOffsetY, realOverScale, overlayRotation, overlayAlpha)
                                                            }

                                                            if (drawingBmp != null) {
                                                                val drawOverlay = drawingBmp.copy(Bitmap.Config.ARGB_8888, false)
                                                                val drawScaleUI = min(boxW / drawingBmp.width, boxH / drawingBmp.height)
                                                                val realDrawScale = (drawScaleUI * drawingScale) / baseScaleUI
                                                                val realDrawOffsetX = drawingOffset.x / baseScaleUI
                                                                val realDrawOffsetY = drawingOffset.y / baseScaleUI
                                                                nativeEngine.processWatermark(mutableBase, drawOverlay, realDrawOffsetX, realDrawOffsetY, realDrawScale, drawingRotation, overlayAlpha)
                                                            }

                                                            withContext(Dispatchers.Main) {
                                                                val outputPath = File(context.cacheDir, "final.${outputFormat.lowercase()}").absolutePath
                                                                FileOutputStream(outputPath).use { out ->
                                                                    val cf = if (outputFormat == "PNG") Bitmap.CompressFormat.PNG else Bitmap.CompressFormat.JPEG
                                                                    mutableBase.compress(cf, exportQuality.toInt(), out)
                                                                }
                                                                
                                                                // Apply Custom Name OR Fallback to Timestamp
                                                                val finalName = if (outputFileName.isNotBlank()) outputFileName else "Watermark_${System.currentTimeMillis()}"
                                                                
                                                                val savedUri = saveToGallery(context, File(outputPath), "$finalName.${outputFormat.lowercase()}")
                                                                if (savedUri != null) Toast.makeText(context, "✅ Saved to Gallery!", Toast.LENGTH_LONG).show()
                                                                else Toast.makeText(context, "❌ Error saving image.", Toast.LENGTH_LONG).show()
                                                            }
                                                        } catch (e: Exception) { withContext(Dispatchers.Main) { Toast.makeText(context, "❌ Process failed.", Toast.LENGTH_LONG).show() } }
                                                    }
                                                }
                                            },
                                            modifier = Modifier.fillMaxWidth().height(50.dp)
                                        ) { Text("SAVE IMAGE") } // QOL: Clearer Button Label
                                    }
                                }
                            }
                        }
                    ) { paddingValues ->
                        Box(modifier = Modifier.fillMaxSize().padding(paddingValues).padding(16.dp), contentAlignment = Alignment.Center) {

                            if (showInventory) {
                                AlertDialog(
                                    onDismissRequest = { showInventory = false },
                                    title = { Text("Saved Overlays") },
                                    text = {
                                        if (savedOverlays.isEmpty()) Text("No overlays saved yet.")
                                        else LazyVerticalGrid(columns = GridCells.Fixed(2)) {
                                            items(savedOverlays) { file ->
                                                Box(modifier = Modifier.padding(4.dp).background(Color.LightGray).aspectRatio(1f)) {
                                                    val bmp = remember { loadBitmapFromFile(file.absolutePath)?.asImageBitmap() }
                                                    if (bmp != null) {
                                                        Image(bitmap = bmp, contentDescription = "Asset", modifier = Modifier.fillMaxSize().clickable {
                                                            saveHistory()
                                                            overlayImageUri = Uri.fromFile(file)
                                                            overlayOffset = Offset.Zero; overlayScale = 1f; overlayRotation = 0f
                                                            overlayText = ""
                                                            showInventory = false
                                                        })
                                                    }
                                                    IconButton(onClick = { file.delete(); refreshInventory() }, modifier = Modifier.align(Alignment.TopEnd)) {
                                                        Icon(Icons.Default.Delete, "Delete", tint = Color.Red)
                                                    }
                                                }
                                            }
                                        }
                                    },
                                    confirmButton = { Button(onClick = { showInventory = false }) { Text("Close") } }
                                )
                            }

                            Box(modifier = Modifier.fillMaxSize().background(if (isDarkMode) Color(0xFF2D2D2D) else Color(0xFFE0E0E0)).clipToBounds()
                                .onGloballyPositioned { coordinates ->
                                    previewWidth = coordinates.size.width.toFloat()
                                    previewHeight = coordinates.size.height.toFloat()
                                }) {

                                val baseBitmap = remember(baseImageUri, baseRotation) { loadAndRotateStrictBitmap(context, baseImageUri, baseRotation) }
                                val overlayBitmap = remember(overlayImageUri) { loadStrictBitmap(context, overlayImageUri) }
                                val drawingBitmap = remember(drawingImageUri) { loadStrictBitmap(context, drawingImageUri) }

                                val baseScaleUI = if (baseBitmap != null) min(previewWidth / baseBitmap.width, previewHeight / baseBitmap.height) else 1f
                                val dx = if (baseBitmap != null) (previewWidth - baseBitmap.width * baseScaleUI) / 2f else 0f
                                val dy = if (baseBitmap != null) (previewHeight - baseBitmap.height * baseScaleUI) / 2f else 0f

                                // Base Layer
                                if (baseBitmap != null) {
                                    Image(bitmap = baseBitmap.asImageBitmap(), contentDescription = null, modifier = Modifier.fillMaxSize(), contentScale = ContentScale.Fit)
                                }
                                
                                // Text Overlay Layer
                                if (overlayBitmap != null) {
                                    Image(bitmap = overlayBitmap.asImageBitmap(), contentDescription = null, modifier = Modifier
                                        .fillMaxSize()
                                        .graphicsLayer(
                                            translationX = overlayOffset.x,
                                            translationY = overlayOffset.y,
                                            scaleX = overlayScale,
                                            scaleY = overlayScale,
                                            rotationZ = overlayRotation,
                                            alpha = overlayAlpha
                                        ),
                                        contentScale = ContentScale.Fit
                                    )
                                }

                                // Baked Drawing Layer
                                if (drawingBitmap != null && !isDrawingMode) {
                                    Image(bitmap = drawingBitmap.asImageBitmap(), contentDescription = null, modifier = Modifier
                                        .fillMaxSize()
                                        .graphicsLayer(
                                            translationX = drawingOffset.x,
                                            translationY = drawingOffset.y,
                                            scaleX = drawingScale,
                                            scaleY = drawingScale,
                                            rotationZ = drawingRotation,
                                            alpha = overlayAlpha
                                        ),
                                        contentScale = ContentScale.Fit
                                    )
                                }

                                val effectiveLayer = if (overlayBitmap != null && drawingBitmap == null) "Text"
                                                     else if (drawingBitmap != null && overlayBitmap == null) "Pen"
                                                     else activeLayer
                                val effectiveLocked = isLocked && overlayBitmap != null && drawingBitmap != null

                                if (!isDrawingMode && !isEyedropperMode && (overlayBitmap != null || drawingBitmap != null)) {
                                    Box(modifier = Modifier
                                        .fillMaxSize()
                                        .pointerInput(effectiveLayer, effectiveLocked) {
                                            detectTransformGestures { _, pan, zoom, rotation ->
                                                if (effectiveLocked) {
                                                    val rad = rotation * (PI / 180.0)
                                                    val cosR = cos(rad).toFloat()
                                                    val sinR = sin(rad).toFloat()

                                                    if (overlayBitmap != null) {
                                                        val zx = overlayOffset.x * zoom
                                                        val zy = overlayOffset.y * zoom
                                                        overlayOffset = Offset(zx * cosR - zy * sinR + pan.x, zx * sinR + zy * cosR + pan.y)
                                                        overlayScale = (overlayScale * zoom).coerceIn(0.1f, 10f)
                                                        overlayRotation += rotation
                                                    }
                                                    if (drawingBitmap != null) {
                                                        val zx = drawingOffset.x * zoom
                                                        val zy = drawingOffset.y * zoom
                                                        drawingOffset = Offset(zx * cosR - zy * sinR + pan.x, zx * sinR + zy * cosR + pan.y)
                                                        drawingScale = (drawingScale * zoom).coerceIn(0.1f, 10f)
                                                        drawingRotation += rotation
                                                    }
                                                } else {
                                                    if (effectiveLayer == "Text" && overlayBitmap != null) {
                                                        overlayOffset += pan
                                                        overlayScale = (overlayScale * zoom).coerceIn(0.1f, 10f)
                                                        overlayRotation += rotation
                                                    } else if (effectiveLayer == "Pen" && drawingBitmap != null) {
                                                        drawingOffset += pan
                                                        drawingScale = (drawingScale * zoom).coerceIn(0.1f, 10f)
                                                        drawingRotation += rotation
                                                    }
                                                }
                                            }
                                        }
                                        .pointerInput(effectiveLayer) {
                                            detectTapGestures(
                                                onDoubleTap = {
                                                    if (effectiveLayer == "Text" && overlayText.isNotEmpty()) showTextDialog = true
                                                }
                                            )
                                        }
                                    )
                                }

                                if (isDrawingMode && !isEyedropperMode && baseBitmap != null) {
                                    Canvas(modifier = Modifier.fillMaxSize().pointerInput(Unit) {
                                        detectDragGestures(
                                            onDragStart = { offset ->
                                                val bx = (offset.x - dx) / baseScaleUI
                                                val by = (offset.y - dy) / baseScaleUI
                                                currentDrawStroke = listOf(Offset(bx, by))
                                                redoPaths = emptyList()
                                            },
                                            onDrag = { change, _ ->
                                                val bx = (change.position.x - dx) / baseScaleUI
                                                val by = (change.position.y - dy) / baseScaleUI
                                                currentDrawStroke = currentDrawStroke + Offset(bx, by)
                                            },
                                            onDragEnd = {
                                                if (currentDrawStroke.size > 1) {
                                                    val androidPath = android.graphics.Path()
                                                    androidPath.moveTo(currentDrawStroke.first().x, currentDrawStroke.first().y)
                                                    for (i in 1 until currentDrawStroke.size) {
                                                        androidPath.lineTo(currentDrawStroke[i].x, currentDrawStroke[i].y)
                                                    }
                                                    drawPaths = drawPaths + DrawStroke(androidPath, drawColor.toArgb(), drawStrokeWidth / baseScaleUI)
                                                }
                                                currentDrawStroke = emptyList()
                                            }
                                        )
                                    }) {
                                        drawContext.canvas.save()
                                        drawContext.canvas.translate(dx, dy)
                                        drawContext.canvas.scale(baseScaleUI, baseScaleUI)
                                        
                                        drawPaths.forEach { stroke ->
                                            drawPath(
                                                path = stroke.path.asComposePath(),
                                                color = Color(stroke.color),
                                                style = Stroke(width = stroke.width, cap = StrokeCap.Round, join = StrokeJoin.Round)
                                            )
                                        }
                                        currentDrawStroke.takeIf { it.size > 1 }?.let { points ->
                                            val composePath = androidx.compose.ui.graphics.Path()
                                            composePath.moveTo(points.first().x, points.first().y)
                                            for (i in 1 until points.size) {
                                                composePath.lineTo(points[i].x, points[i].y)
                                            }
                                            drawPath(
                                                path = composePath,
                                                color = drawColor,
                                                style = Stroke(width = drawStrokeWidth / baseScaleUI, cap = StrokeCap.Round, join = StrokeJoin.Round)
                                            )
                                        }
                                        drawContext.canvas.restore()
                                    }
                                }

                                if (isEyedropperMode) {
                                    val updateColor = { offset: Offset ->
                                        if (baseBitmap != null) {
                                            val bx = ((offset.x - dx) / baseScaleUI).toInt().coerceIn(0, baseBitmap.width - 1)
                                            val by = ((offset.y - dy) / baseScaleUI).toInt().coerceIn(0, baseBitmap.height - 1)
                                            val pickedColor = Color(baseBitmap.getPixel(bx, by))
                                            if (activeColorContext == "text") overlayTextColor = pickedColor else drawColor = pickedColor
                                        }
                                    }

                                    Box(
                                        modifier = Modifier
                                            .fillMaxSize()
                                            .background(Color.Black.copy(alpha = 0.3f))
                                            .pointerInput(Unit) {
                                                detectDragGestures { change, _ -> updateColor(change.position) }
                                            }
                                            .pointerInput(Unit) {
                                                detectTapGestures { offset ->
                                                    updateColor(offset)
                                                    isEyedropperMode = false
                                                    if (returnToTextDialog) {
                                                        showTextDialog = true
                                                        returnToTextDialog = false
                                                    }
                                                }
                                            }
                                    ) {
                                        Box(
                                            modifier = Modifier
                                                .align(Alignment.TopCenter)
                                                .padding(top = 32.dp)
                                                .background(Color.Black.copy(alpha = 0.8f), CircleShape)
                                                .padding(horizontal = 24.dp, vertical = 12.dp)
                                        ) {
                                            Text("🎯 Eyedropper: Tap or drag to extract color", color = Color.White, fontSize = 14.sp)
                                        }
                                    }
                                }

                                LaunchedEffect(baseBitmap, overlayBitmap, drawingBitmap) {
                                    AppState.currentBaseBitmap = baseBitmap
                                    AppState.currentOverlayBitmap = overlayBitmap
                                    AppState.currentDrawingBitmap = drawingBitmap
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
"""
    with open(f"{package_path}/MainActivity.kt", "w") as f:
        f.write(main_activity_content)
    print("✅ 5-4 Generated UI (Custom Image Naming & Clear Output Buttons)")

if __name__ == "__main__":
    generate()
