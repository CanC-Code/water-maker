import os

def generate_ui():
    package_path = "app/src/main/java/com/watermarker"

    # 1. Native Engine Bridge
    engine_content = """package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    companion object { init { System.loadLibrary("watermarker") } }
    external fun blendImages(base: Bitmap, overlay: Bitmap, x: Float, y: Float, scale: Float, rotation: Float, opacity: Float)
}
"""

    # 2. Compliant App Open Ad Manager (With Fail-Fast Logic & Test ID)
    ad_manager_content = """package com.watermarker

import android.app.Activity
import android.content.Context
import com.google.android.gms.ads.AdError
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.FullScreenContentCallback
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.appopen.AppOpenAd
import java.util.Date

class AppOpenAdManager {
    private var appOpenAd: AppOpenAd? = null
    private var isLoadingAd = false
    var isShowingAd = false
    var isAdFailed = false // <-- Added to allow the splash screen to fail-fast
    var isInitialLaunch = true 
    private var loadTime: Long = 0
    
    // IMPORTANT: Official Google Test Ad ID for App Open Ads.
    // Replace with "ca-app-pub-7732503595590477/4459993522" ONLY when publishing to the Play Store.
    private val adUnitId = "ca-app-pub-3940256099942544/9257395921"

    interface OnShowAdCompleteListener {
        fun onShowAdComplete()
    }

    fun loadAd(context: Context) {
        if (isLoadingAd || isAdAvailable()) return
        isLoadingAd = true
        isAdFailed = false
        val request = AdRequest.Builder().build()
        
        AppOpenAd.load(
            context, adUnitId, request,
            object : AppOpenAd.AppOpenAdLoadCallback() {
                override fun onAdLoaded(ad: AppOpenAd) {
                    appOpenAd = ad
                    isLoadingAd = false
                    loadTime = Date().time
                }
                override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                    isLoadingAd = false
                    isAdFailed = true // <-- Tells Splash Screen to stop waiting
                }
            }
        )
    }

    private fun wasLoadTimeLessThanNHoursAgo(numHours: Long): Boolean {
        val dateDifference = Date().time - loadTime
        val numMilliSecondsPerHour: Long = 3600000
        return dateDifference < (numMilliSecondsPerHour * numHours)
    }

    fun isAdAvailable(): Boolean {
        return appOpenAd != null && wasLoadTimeLessThanNHoursAgo(4)
    }

    fun showAdIfAvailable(activity: Activity, onShowAdCompleteListener: OnShowAdCompleteListener) {
        if (isShowingAd) return
        if (!isAdAvailable()) {
            loadAd(activity)
            onShowAdCompleteListener.onShowAdComplete()
            return
        }

        appOpenAd?.fullScreenContentCallback = object : FullScreenContentCallback() {
            override fun onAdDismissedFullScreenContent() {
                appOpenAd = null
                isShowingAd = false
                onShowAdCompleteListener.onShowAdComplete()
                loadAd(activity) // Pre-load the next ad
            }
            override fun onAdFailedToShowFullScreenContent(adError: AdError) {
                appOpenAd = null
                isShowingAd = false
                onShowAdCompleteListener.onShowAdComplete()
                loadAd(activity)
            }
            override fun onAdShowedFullScreenContent() {
                isShowingAd = true
            }
        }
        appOpenAd?.show(activity)
    }
}
"""

    # 3. Application Class (Lifecycle Observer)
    app_class_content = """package com.watermarker

import android.app.Activity
import android.app.Application
import android.os.Bundle
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.ProcessLifecycleOwner
import com.google.android.gms.ads.MobileAds

class WaterMarkerApp : Application(), Application.ActivityLifecycleCallbacks, DefaultLifecycleObserver {
    lateinit var appOpenAdManager: AppOpenAdManager
    private var currentActivity: Activity? = null

    override fun onCreate() {
        super<Application>.onCreate() 
        registerActivityLifecycleCallbacks(this)
        MobileAds.initialize(this) {}
        ProcessLifecycleOwner.get().lifecycle.addObserver(this)
        
        appOpenAdManager = AppOpenAdManager()
        appOpenAdManager.loadAd(this) 
    }

    override fun onStart(owner: LifecycleOwner) {
        super<DefaultLifecycleObserver>.onStart(owner)
        currentActivity?.let {
            if (!appOpenAdManager.isInitialLaunch) {
                appOpenAdManager.showAdIfAvailable(it, object : AppOpenAdManager.OnShowAdCompleteListener {
                    override fun onShowAdComplete() {}
                })
            }
        }
    }

    override fun onActivityStarted(activity: Activity) {
        if (!appOpenAdManager.isShowingAd) currentActivity = activity
    }
    override fun onActivityResumed(activity: Activity) { currentActivity = activity }
    override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {}
    override fun onActivityPaused(activity: Activity) {}
    override fun onActivityStopped(activity: Activity) {}
    override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) {}
    override fun onActivityDestroyed(activity: Activity) { 
        if (currentActivity == activity) currentActivity = null 
    }
}
"""

    # 4. Main UI 
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
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val app = application as WaterMarkerApp

        setContent { 
            var isAppReady by remember { mutableStateOf(false) }

            // SPLASH SCREEN LOGIC
            LaunchedEffect(Unit) {
                if (app.appOpenAdManager.isInitialLaunch) {
                    val startTime = System.currentTimeMillis()
                    
                    // Logic Fix: Wait UNLESS the ad explicitly fails or succeeds
                    while (!app.appOpenAdManager.isAdAvailable() && 
                           !app.appOpenAdManager.isAdFailed && 
                           System.currentTimeMillis() - startTime < 3000) {
                        delay(100)
                    }
                    
                    app.appOpenAdManager.showAdIfAvailable(this@MainActivity, object : AppOpenAdManager.OnShowAdCompleteListener {
                        override fun onShowAdComplete() {
                            app.appOpenAdManager.isInitialLaunch = false
                            isAppReady = true
                        }
                    })
                } else {
                    isAppReady = true
                }
            }

            if (!isAppReady) {
                Box(modifier = Modifier.fillMaxSize().background(Color(0xFF020617)), contentAlignment = Alignment.Center) {
                    Column(horizontalAlignment = Alignment.CenterHorizontally) {
                        Text("PRO OVERLAY STUDIO", color = Color(0xFF38BDF8), fontSize = 22.sp, fontWeight = FontWeight.ExtraBold)
                        Spacer(modifier = Modifier.height(24.dp))
                        CircularProgressIndicator(color = Color.White)
                    }
                }
            } else {
                WaterMarkerUI() 
            }
        }
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
    
    var fileName by remember { mutableStateOf("MyWatermark") }
    var outputFormat by remember { mutableStateOf("JPG") }
    var overlayX by remember { mutableStateOf(0f) }
    var overlayY by remember { mutableStateOf(0f) }
    var overlayScale by remember { mutableStateOf(1f) }
    var overlayRotation by remember { mutableStateOf(0f) }
    var baseRotation by remember { mutableStateOf(0f) }
    var opacity by remember { mutableStateOf(1.0f) }
    var exportQuality by remember { mutableStateOf(0.9f) }
    var isSaving by remember { mutableStateOf(false) }

    val formats = listOf("PNG", "JPG", "WEBP")

    val basePicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { baseBitmap = decodeUri(context, it); baseRotation = 0f }
    }
    val overlayPicker = rememberLauncherForActivityResult(ActivityResultContracts.GetContent()) { uri ->
        uri?.let { activeOverlay = decodeUri(context, it); overlayX = 0f; overlayY = 0f; overlayScale = 1f; overlayRotation = 0f }
    }

    Scaffold(snackbarHost = { SnackbarHost(snackbarHostState) }, containerColor = Color(0xFF020617)) { paddingValues ->
        Column(modifier = Modifier.fillMaxSize().padding(paddingValues)) {
            
            Row(modifier = Modifier.fillMaxWidth().padding(8.dp), horizontalArrangement = Arrangement.SpaceEvenly, verticalAlignment = Alignment.CenterVertically) {
                Button(onClick = { basePicker.launch("image/*") }) { Text("SUBJECT", fontSize = 11.sp) }
                IconButton(onClick = { baseRotation = (baseRotation + 90f) % 360f }) { Icon(Icons.Default.Refresh, "Rotate", tint = Color.White) }
                Button(onClick = { overlayPicker.launch("image/*") }) { Text("OVERLAY", fontSize = 11.sp) }
            }

            BoxWithConstraints(modifier = Modifier.weight(1f).fillMaxWidth().background(Color.Black).clipToBounds()) {
                val constraints = this
                baseBitmap?.let { base ->
                    val isPortrait = (baseRotation / 90f) % 2 != 0f
                    val bw = if (isPortrait) base.height else base.width
                    val bh = if (isPortrait) base.width else base.height
                    val canvasRatio = constraints.maxWidth.value / constraints.maxHeight.value
                    val imageRatio = bw.toFloat() / bh.toFloat()
                    val fitScale = if (imageRatio > canvasRatio) constraints.maxWidth.value / bw.toFloat() else constraints.maxHeight.value / bh.toFloat()

                    Canvas(modifier = Modifier.fillMaxSize().pointerInput(Unit) {
                        detectTransformGestures { _, pan, zoom, rot ->
                            overlayX += pan.x / fitScale; overlayY += pan.y / fitScale; overlayScale *= zoom; overlayRotation += rot
                        }
                    }) {
                        drawContext.canvas.save()
                        drawContext.canvas.translate(size.width / 2f, size.height / 2f)
                        drawContext.canvas.scale(fitScale, fitScale)
                        
                        drawContext.canvas.save()
                        drawContext.canvas.rotate(baseRotation)
                        drawImage(base.asImageBitmap(), dstOffset = IntOffset(-base.width / 2, -base.height / 2))
                        drawContext.canvas.restore()

                        activeOverlay?.let { over ->
                            drawContext.canvas.save()
                            drawContext.canvas.translate(overlayX, overlayY)
                            drawContext.canvas.rotate(overlayRotation)
                            drawContext.canvas.scale(overlayScale, overlayScale)
                            drawImage(over.asImageBitmap(), alpha = opacity, dstOffset = IntOffset(-over.width / 2, -over.height / 2))
                            drawContext.canvas.restore()
                        }
                        drawContext.canvas.restore()
                    }
                } ?: Box(Modifier.fillMaxSize(), contentAlignment = Alignment.Center) { Text("Load a subject image", color = Color.Gray) }
            }

            Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = Color(0xFF0F172A)), shape = RoundedCornerShape(topStart = 16.dp, topEnd = 16.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    OutlinedTextField(value = fileName, onValueChange = { fileName = it }, label = { Text("Filename") }, modifier = Modifier.fillMaxWidth(), singleLine = true, colors = OutlinedTextFieldDefaults.colors(unfocusedTextColor = Color.White, focusedTextColor = Color.White))
                    Spacer(Modifier.height(8.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                        Text("Format:", color = Color.White, fontWeight = FontWeight.Bold)
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            formats.forEach { format ->
                                FilterChip(selected = outputFormat == format, onClick = { outputFormat = format }, label = { Text(format) }, colors = FilterChipDefaults.filterChipColors(selectedContainerColor = Color(0xFF38BDF8), selectedLabelColor = Color(0xFF020617)))
                            }
                        }
                    }
                    Spacer(Modifier.height(4.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(if (outputFormat == "PNG") "PNG is Lossless" else "Export Quality", color = Color.Gray, fontSize = 12.sp)
                        Text(if (outputFormat == "PNG") "100%" else "${(exportQuality * 100).toInt()}%", color = Color(0xFF38BDF8), fontSize = 12.sp)
                    }
                    Slider(value = exportQuality, onValueChange = { exportQuality = it }, enabled = outputFormat != "PNG", colors = SliderDefaults.colors(thumbColor = Color(0xFF38BDF8), activeTrackColor = Color(0xFF38BDF8)))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text("Overlay Opacity", color = Color.Gray, fontSize = 12.sp)
                        Text("${(opacity * 100).toInt()}%", color = Color(0xFF38BDF8), fontSize = 12.sp)
                    }
                    Slider(value = opacity, onValueChange = { opacity = it }, colors = SliderDefaults.colors(thumbColor = Color(0xFF38BDF8), activeTrackColor = Color(0xFF38BDF8)))
                    
                    Button(
                        onClick = {
                            if (baseBitmap != null && activeOverlay != null) {
                                scope.launch {
                                    isSaving = true
                                    val success = saveCustomFormat(context, baseBitmap!!, activeOverlay!!, overlayX, overlayY, overlayScale, overlayRotation, opacity, baseRotation, fileName, outputFormat, exportQuality)
                                    isSaving = false
                                    if(success) snackbarHostState.showSnackbar("Exported successfully!") else snackbarHostState.showSnackbar("Failed to export image.")
                                }
                            } else { scope.launch { snackbarHostState.showSnackbar("Please load both images first.") } }
                        },
                        modifier = Modifier.fillMaxWidth(), colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF38BDF8))
                    ) { Text(if (isSaving) "PROCESSING..." else "EXPORT IMAGE", color = Color(0xFF020617), fontWeight = FontWeight.ExtraBold) }
                }
            }
        }
    }
}

fun decodeUri(context: Context, uri: Uri): Bitmap? {
    return try { context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, BitmapFactory.Options().apply { inMutable = true }) } } catch (e: Exception) { null }
}

suspend fun saveCustomFormat(context: Context, base: Bitmap, overlay: Bitmap, x: Float, y: Float, s: Float, r: Float, a: Float, baseRot: Float, name: String, format: String, quality: Float): Boolean {
    return withContext(Dispatchers.IO) {
        try {
            val matrixBase = Matrix().apply { postRotate(baseRot) }
            val finalBase = Bitmap.createBitmap(base, 0, 0, base.width, base.height, matrixBase, true)
            
            val result = Bitmap.createBitmap(finalBase.width, finalBase.height, Bitmap.Config.ARGB_8888)
            val canvas = Canvas(result)
            
            if (format == "JPG") canvas.drawColor(android.graphics.Color.WHITE)
            
            canvas.drawBitmap(finalBase, 0f, 0f, null)

            val paint = Paint().apply { alpha = (a * 255).toInt(); isFilterBitmap = true }
            val matrixOverlay = Matrix().apply {
                postTranslate(-overlay.width / 2f, -overlay.height / 2f)
                postScale(s, s)
                postRotate(r)
                postTranslate(result.width / 2f + x, result.height / 2f + y)
            }
            canvas.drawBitmap(overlay, matrixOverlay, paint)
            
            val ext = format.lowercase()
            val compressFormat = when (format) {
                "JPG" -> Bitmap.CompressFormat.JPEG
                "WEBP" -> if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    if ((quality*100).toInt() >= 100) Bitmap.CompressFormat.WEBP_LOSSLESS else Bitmap.CompressFormat.WEBP_LOSSY
                } else { @Suppress("DEPRECATION") Bitmap.CompressFormat.WEBP }
                else -> Bitmap.CompressFormat.PNG
            }
            val values = ContentValues().apply {
                put(MediaStore.MediaColumns.DISPLAY_NAME, "$name.$ext"); put(MediaStore.MediaColumns.MIME_TYPE, "image/$ext")
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) put(MediaStore.MediaColumns.RELATIVE_PATH, "Pictures/WaterMarker")
            }
            val uri = context.contentResolver.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
            uri?.let { context.contentResolver.openOutputStream(it)?.use { stream -> result.compress(compressFormat, (quality * 100).toInt(), stream) } }
            true
        } catch (e: Exception) { false }
    }
}
"""

    files = {
        f"{package_path}/NativeEngine.kt": engine_content.strip(),
        f"{package_path}/AppOpenAdManager.kt": ad_manager_content.strip(),
        f"{package_path}/WaterMarkerApp.kt": app_class_content.strip(),
        f"{package_path}/MainActivity.kt": main_activity_content.strip()
    }

    print("🎨 Applying Final Fixes: Splash Screen Fast-Fail & Canvas Rendering...")
    for path, content in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
    print("✅ Complete: Ready for build!")

if __name__ == "__main__":
    generate_ui()
