import os

def generate():
    package_path = "app/src/main/java/com/watermarker"
    os.makedirs(package_path, exist_ok=True)

    utils_content = r"""package com.watermarker

import android.content.Context
import android.graphics.*
import android.net.Uri
import java.io.File
import kotlin.math.abs

// Object to hold the current application state for the Native Engine
object AppState {
    var currentBaseBitmap: Bitmap? = null
    var currentOverlayBitmap: Bitmap? = null
}

// Data class bridging Compose vector paths to Android graphics
data class DrawStroke(
    val path: android.graphics.Path,
    val color: Int,
    val width: Float
)

fun calculateInSampleSize(options: BitmapFactory.Options, reqWidth: Int, reqHeight: Int): Int {
    val (height: Int, width: Int) = options.outHeight to options.outWidth
    var inSampleSize = 1
    if (height > reqHeight || width > reqWidth) {
        val halfHeight: Int = height / 2
        val halfWidth: Int = width / 2
        while (halfHeight / inSampleSize >= reqHeight && halfWidth / inSampleSize >= reqWidth) {
            inSampleSize *= 2
        }
    }
    return inSampleSize
}

fun loadBitmapFromFile(path: String): Bitmap? {
    return try { BitmapFactory.decodeFile(path) } catch (e: Exception) { null }
}

fun loadStrictBitmap(context: Context, uri: Uri?): Bitmap? {
    if (uri == null) return null
    return try {
        val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, options) }

        options.inSampleSize = calculateInSampleSize(options, 1920, 1080)
        options.inJustDecodeBounds = false
        options.inPreferredConfig = Bitmap.Config.ARGB_8888
        options.inMutable = false
        options.inScaled = false

        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, options) }
    } catch (e: Exception) { null }
}

fun loadAndRotateStrictBitmap(context: Context, uri: Uri?, rotation: Float): Bitmap? {
    if (uri == null) return null
    return try {
        val options = BitmapFactory.Options().apply { inJustDecodeBounds = true }
        context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, options) }

        options.inSampleSize = calculateInSampleSize(options, 1920, 1080)
        options.inJustDecodeBounds = false
        options.inPreferredConfig = Bitmap.Config.ARGB_8888
        options.inMutable = true
        options.inScaled = false

        val bitmap = context.contentResolver.openInputStream(uri)?.use { BitmapFactory.decodeStream(it, null, options) } ?: return null

        if (rotation != 0f) {
            val matrix = Matrix().apply { postRotate(rotation) }
            val rotated = Bitmap.createBitmap(bitmap, 0, 0, bitmap.width, bitmap.height, matrix, true)
            if (rotated.isMutable) rotated else rotated.copy(Bitmap.Config.ARGB_8888, true)
        } else {
            if (bitmap.isMutable) bitmap else bitmap.copy(Bitmap.Config.ARGB_8888, true)
        }
    } catch (e: Exception) { null }
}

fun saveToGallery(context: Context, file: File, fileName: String): Uri? {
    val values = android.content.ContentValues().apply {
        put(android.provider.MediaStore.MediaColumns.DISPLAY_NAME, fileName)
        put(android.provider.MediaStore.MediaColumns.MIME_TYPE, "image/${file.extension}")
        put(android.provider.MediaStore.MediaColumns.RELATIVE_PATH, android.os.Environment.DIRECTORY_PICTURES + "/WaterMarker")
    }
    return try {
        val uri = context.contentResolver.insert(android.provider.MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
        uri?.also { destUri -> context.contentResolver.openOutputStream(destUri)?.use { out -> file.inputStream().use { input -> input.copyTo(out) } } }
    } catch (e: Exception) { null }
}

// Proper Circular Arc calculation preventing upside-down text
fun createTextBitmap(text: String, color: Int, typeface: Typeface?, bendAmount: Float): Bitmap {
    val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        this.color = color
        this.textSize = 200f
        this.typeface = typeface ?: Typeface.DEFAULT
        this.textAlign = Paint.Align.CENTER
    }

    val textWidth = paint.measureText(text)
    val textHeight = paint.descent() - paint.ascent()

    if (bendAmount == 0f || textWidth <= 0f) {
        val bmpWidth = (textWidth + 100).toInt().coerceAtLeast(1)
        val bmpHeight = (textHeight + 100).toInt().coerceAtLeast(1)
        val bitmap = Bitmap.createBitmap(bmpWidth, bmpHeight, Bitmap.Config.ARGB_8888)
        val canvas = android.graphics.Canvas(bitmap)
        val baseline = bmpHeight / 2f - (paint.descent() + paint.ascent()) / 2f
        canvas.drawText(text, bmpWidth / 2f, baseline, paint)
        return bitmap
    }

    // Mathematically define the circular sweep
    val maxSweep = 160f 
    val sweep = (abs(bendAmount) / 100f) * maxSweep
    val sweepRads = (sweep * Math.PI / 180.0)
    val radius = (textWidth / sweepRads).toFloat()

    // Calculate arc height (sagitta) to fit perfectly in the bounding box
    val sagitta = radius * (1f - kotlin.math.cos(sweepRads / 2.0)).toFloat()
    
    val bmpWidth = (textWidth + 300).toInt()
    val bmpHeight = (sagitta + textHeight + 300).toInt()

    val bitmap = Bitmap.createBitmap(bmpWidth, bmpHeight, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)
    val midX = bmpWidth / 2f
    val path = Path()

    if (bendAmount > 0) {
        // Smile curve (Text anchors to bottom of a huge circle)
        val centerY = bmpHeight / 2f + sagitta / 2f - radius
        val oval = RectF(midX - radius, centerY - radius, midX + radius, centerY + radius)
        
        // FIX: Start at bottom-left and sweep negative to guarantee a left-to-right upright text!
        path.addArc(oval, 90f + sweep / 2f, -sweep)
        canvas.drawTextOnPath(text, path, 0f, textHeight / 4f, paint)
    } else {
        // Frown curve (Text anchors to top of a huge circle)
        val centerY = bmpHeight / 2f - sagitta / 2f + radius
        val oval = RectF(midX - radius, centerY - radius, midX + radius, centerY + radius)
        
        // Starts top-left, sweeps clockwise (upright)
        path.addArc(oval, 270f - sweep / 2f, sweep)
        canvas.drawTextOnPath(text, path, 0f, textHeight * 0.75f, paint)
    }

    return bitmap
}

fun createDrawingBitmap(strokes: List<DrawStroke>, width: Int, height: Int): Bitmap {
    val safeWidth = if (width > 0) width else 1080
    val safeHeight = if (height > 0) height else 1920
    val bitmap = Bitmap.createBitmap(safeWidth, safeHeight, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)

    for (stroke in strokes) {
        val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            this.color = stroke.color
            this.style = Paint.Style.STROKE
            this.strokeWidth = stroke.width
            this.strokeCap = Paint.Cap.ROUND
            this.strokeJoin = Paint.Join.ROUND
        }
        canvas.drawPath(stroke.path, paint)
    }
    return bitmap
}
"""
    with open(f"{package_path}/OverlayUtils.kt", "w") as f:
        f.write(utils_content)
    print("✅ 5-3 Generated OverlayUtils.kt (Upright Geometry Enforced)")

if __name__ == "__main__":
    generate()
