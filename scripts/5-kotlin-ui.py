import os

def generate_ui():
    package_path = "app/src/main/java/com/example/watermaker"
    
    engine_content = """
package com.example.watermaker

class NativeEngine {
    external fun processImage(inputPath: String, outputPath: String, watermarkPath: String, quality: Int)
    companion object {
        init {
            System.loadLibrary("watermaker")
        }
    }
}
"""

    ad_manager_content = """
package com.example.watermaker

import android.content.Context

class AppOpenAdManager(private val context: Context) {
    fun showAdIfAvailable() {
        // App Open Ad logic goes here
    }
}
"""

    app_class_content = """
package com.example.watermaker

import android.app.Application

class WaterMarkerApp : Application() {
    override fun onCreate() {
        super.onCreate()
    }
}
"""

    # Updated MainActivity with Hamburger Menu, Font Loading, Text Input, and Color Picker
    main_activity_content = """
package com.example.watermaker

import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            MaterialTheme {
                WaterMarkerScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun WaterMarkerScreen() {
    var menuExpanded by remember { mutableStateOf(false) }
    var baseImageUri by remember { mutableStateOf<Uri?>(null) }
    var overlayImageUri by remember { mutableStateOf<Uri?>(null) }
    var fontUri by remember { mutableStateOf<Uri?>(null) }
    
    var overlayText by remember { mutableStateOf("") }
    
    // Color state
    var textColor by remember { mutableStateOf(Color.White) }
    var showColorPicker by remember { mutableStateOf(false) }

    // Launchers for fetching files
    val baseImageLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> baseImageUri = uri }
    val overlayImageLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> overlayImageUri = uri }
    val fontLauncher = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri -> fontUri = uri }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("WaterMaker") },
                navigationIcon = {
                    Box {
                        IconButton(onClick = { menuExpanded = true }) {
                            Icon(Icons.Default.Menu, contentDescription = "Menu")
                        }
                        DropdownMenu(
                            expanded = menuExpanded,
                            onDismissRequest = { menuExpanded = false }
                        ) {
                            DropdownMenuItem(
                                text = { Text("Load Base Image") },
                                onClick = {
                                    menuExpanded = false
                                    baseImageLauncher.launch("image/*")
                                }
                            )
                            DropdownMenuItem(
                                text = { Text("Load Overlay Image") },
                                onClick = {
                                    menuExpanded = false
                                    overlayImageLauncher.launch("image/*")
                                }
                            )
                            DropdownMenuItem(
                                text = { Text("Import Custom Font (.ttf)") },
                                onClick = {
                                    menuExpanded = false
                                    fontLauncher.launch("*/*") // Can be restricted to font/ttf if device supports MIME
                                }
                            )
                        }
                    }
                }
            )
        }
    ) { paddingValues ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(16.dp)
        ) {
            // Text Input
            OutlinedTextField(
                value = overlayText,
                onValueChange = { overlayText = it },
                label = { Text("Manually type overlay text") },
                modifier = Modifier.fillMaxWidth()
            )
            
            Spacer(modifier = Modifier.height(16.dp))
            
            // Color Picker Toggle
            Button(onClick = { showColorPicker = !showColorPicker }) {
                Text(if (showColorPicker) "Hide Color Options" else "Select Text Color")
            }

            // RGB Slider Interface (Native replacement for Color Wheel)
            if (showColorPicker) {
                var r by remember { mutableFloatStateOf(textColor.red) }
                var g by remember { mutableFloatStateOf(textColor.green) }
                var b by remember { mutableFloatStateOf(textColor.blue) }

                Column(modifier = Modifier.padding(vertical = 16.dp)) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("R", color = Color.Red, modifier = Modifier.width(20.dp))
                        Slider(value = r, onValueChange = { r = it; textColor = Color(r, g, b) }, modifier = Modifier.weight(1f))
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("G", color = Color.Green, modifier = Modifier.width(20.dp))
                        Slider(value = g, onValueChange = { g = it; textColor = Color(r, g, b) }, modifier = Modifier.weight(1f))
                    }
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("B", color = Color.Blue, modifier = Modifier.width(20.dp))
                        Slider(value = b, onValueChange = { b = it; textColor = Color(r, g, b) }, modifier = Modifier.weight(1f))
                    }
                    
                    // Color Preview Circle
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.Center
                    ) {
                        Box(modifier = Modifier.size(40.dp).background(textColor, CircleShape))
                    }
                }
            }

            Spacer(modifier = Modifier.height(24.dp))
            
            // Status Preview Area
            Text("Assets Loaded:", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))
            Text("Base Image: ${if (baseImageUri != null) "Loaded ✅" else "Pending"}")
            Text("Overlay Image: ${if (overlayImageUri != null) "Loaded ✅" else "Pending"}")
            Text("Custom Font: ${if (fontUri != null) "Loaded ✅" else "Pending"}")
        }
    }
}
"""

    files = {
        f"{package_path}/NativeEngine.kt": engine_content.strip(),
        f"{package_path}/AppOpenAdManager.kt": ad_manager_content.strip(),
        f"{package_path}/WaterMarkerApp.kt": app_class_content.strip(),
        f"{package_path}/MainActivity.kt": main_activity_content.strip()
    }

    print("🎨 Updating Kotlin logic with requested Dropdown Menu, Font Picker, and Color Customization...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Complete: New UI elements successfully generated.")

if __name__ == "__main__":
    generate_ui()
