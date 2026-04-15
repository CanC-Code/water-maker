import os

def generate():
    package_path = "app/src/main/java/com/watermarker"
    os.makedirs(package_path, exist_ok=True)

    # FIX: Removed DefaultLifecycleObserver from the class signature.
    # It is now an anonymous object inside ProcessLifecycleOwner to prevent 'super' conflicts.
    app_class_content = """package com.watermarker

import android.app.Activity
import android.app.Application
import android.os.Bundle
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.ProcessLifecycleOwner
import com.google.android.gms.ads.MobileAds

class WaterMarkerApp : Application(), Application.ActivityLifecycleCallbacks {
    private lateinit var appOpenAdManager: AppOpenAdManager
    private var currentActivity: Activity? = null

    override fun onCreate() {
        super.onCreate()
        registerActivityLifecycleCallbacks(this)
        MobileAds.initialize(this) {}
        
        // Setup App Open Ad tracking
        appOpenAdManager = AppOpenAdManager(this)
        
        ProcessLifecycleOwner.get().lifecycle.addObserver(object : DefaultLifecycleObserver {
            override fun onStart(owner: LifecycleOwner) {
                super.onStart(owner)
                currentActivity?.let { appOpenAdManager.showAdIfAvailable(it) }
            }
        })
    }

    // Activity Lifecycle Tracking
    override fun onActivityStarted(activity: Activity) { currentActivity = activity }
    override fun onActivityResumed(activity: Activity) { currentActivity = activity }
    override fun onActivityPaused(activity: Activity) {}
    override fun onActivityStopped(activity: Activity) {}
    override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) {}
    override fun onActivityDestroyed(activity: Activity) { if (currentActivity == activity) currentActivity = null }
    override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {}
}"""

    ad_manager_content = """package com.watermarker

import android.app.Activity
import android.content.Context
import com.google.android.gms.ads.AdError
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.FullScreenContentCallback
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.appopen.AppOpenAd
import java.util.Date

class AppOpenAdManager(private val context: Context) {
    private var appOpenAd: AppOpenAd? = null
    private var isLoadingAd = false
    private var isShowingAd = false
    private var loadTime: Long = 0

    init { loadAd() } // Pre-load on init

    fun loadAd() {
        if (isLoadingAd || isAdAvailable()) return
        isLoadingAd = true
        val request = AdRequest.Builder().build()
        // Updated AdMob Ad Unit ID
        AppOpenAd.load(context, "ca-app-pub-7732503595590477/4459993522", request,
            object : AppOpenAd.AppOpenAdLoadCallback() {
                override fun onAdLoaded(ad: AppOpenAd) {
                    appOpenAd = ad
                    isLoadingAd = false
                    loadTime = Date().time
                }
                override fun onAdFailedToLoad(e: LoadAdError) { isLoadingAd = false }
            }
        )
    }

    private fun wasLoadTimeLessThanNHoursAgo(numHours: Long): Boolean {
        val dateDifference = Date().time - loadTime
        val numMilliSecondsPerHour: Long = 3600000
        return dateDifference < numMilliSecondsPerHour * numHours
    }

    private fun isAdAvailable(): Boolean {
        return appOpenAd != null && wasLoadTimeLessThanNHoursAgo(4)
    }

    fun showAdIfAvailable(activity: Activity) {
        if (isShowingAd) return
        if (!isAdAvailable()) {
            loadAd()
            return
        }

        appOpenAd?.fullScreenContentCallback = object : FullScreenContentCallback() {
            override fun onAdDismissedFullScreenContent() {
                appOpenAd = null
                isShowingAd = false
                loadAd() // Preload the next ad
            }
            override fun onAdFailedToShowFullScreenContent(error: AdError) {
                appOpenAd = null
                isShowingAd = false
                loadAd()
            }
            override fun onAdShowedFullScreenContent() {
                isShowingAd = true
            }
        }
        appOpenAd?.show(activity)
    }
}"""

    engine_content = """package com.watermarker
import android.graphics.Bitmap
class NativeEngine {
    init { System.loadLibrary("watermarker") }
    external fun processWatermark(baseBitmap: Bitmap, overlayBitmap: Bitmap,
                                  realOffsetX: Float, realOffsetY: Float,
                                  realOverScale: Float, overlayRotation: Float,
                                  overlayAlpha: Float): Boolean
}"""

    with open(f"{package_path}/WaterMarkerApp.kt", "w") as f: f.write(app_class_content)
    with open(f"{package_path}/AppOpenAdManager.kt", "w") as f: f.write(ad_manager_content)
    with open(f"{package_path}/NativeEngine.kt", "w") as f: f.write(engine_content)
    print("✅ 5-1 Generated Kotlin Core (Fixed Class Signature)")

if __name__ == "__main__":
    generate()
