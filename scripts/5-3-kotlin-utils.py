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

fun createTextBitmap(text: String, color: Int, typeface: Typeface?, bendAmount: Float): Bitmap {
    val paint = Paint(Paint.ANTI_ALIAS_FLAG).apply { 
        this.color = color; 
        this.textSize = 200f; 
        this.typeface = typeface ?: Typeface.DEFAULT; 
        this.textAlign = Paint.Align.CENTER 
    }
    
    val textWidth = paint.measureText(text)
    // Make the box larger to accommodate curved text
    val bmpSize = (textWidth + 400).toInt() 
    
    val bitmap = Bitmap.createBitmap(bmpSize, bmpSize, Bitmap.Config.ARGB_8888)
    val canvas = android.graphics.Canvas(bitmap)

    val midX = bmpSize / 2f
    val midY = bmpSize / 2f

    if (bendAmount == 0f) {
        val baseline = midY - (paint.descent() + paint.ascent()) / 2f
        canvas.drawText(text, midX, baseline, paint)
    } else {
        // Create a curved path for the text
        val path = Path()
        val startX = 100f
        val endX = bmpSize - 100f
        // bendAmount ranges from -100 to 100. We multiply to create an extreme curve point.
        val controlY = midY + (bendAmount * 10f) 
        
        path.moveTo(startX, midY)
        path.quadTo(midX, controlY, endX, midY)
        
        // drawTextOnPath aligns to the path stroke, adjust vertical offset
        canvas.drawTextOnPath(text, path, 0f, 0f, paint)
    }
    return bitmap
}
"""
    with open(f"{package_path}/OverlayUtils.kt", "w") as f:
        f.write(utils_content)
    print("✅ 5-3 Generated OverlayUtils.kt (Text Curving & Bitmap Management)")

if __name__ == "__main__":
    generate()
