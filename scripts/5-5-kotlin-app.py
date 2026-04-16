import os

def generate():
    package_path = "app/src/main/java/com/watermarker"
    os.makedirs(package_path, exist_ok=True)

    app_content = """package com.watermarker

import android.app.Activity
import android.app.Application
import android.os.Bundle
import androidx.lifecycle.DefaultLifecycleObserver
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.ProcessLifecycleOwner
import com.google.android.gms.ads.AdError
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.FullScreenContentCallback
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.appopen.AppOpenAd
import java.util.Date

class WatermarkerApp : Application(), Application.ActivityLifecycleCallbacks, DefaultLifecycleObserver {

    private lateinit var appOpenAdManager: AppOpenAdManager
    private var currentActivity: Activity? = null

    override fun onCreate() {
        super.onCreate()
        registerActivityLifecycleCallbacks(this)
        
        // Initialize the Mobile Ads SDK
        MobileAds.initialize(this) {}
        
        // Observe the app process lifecycle to trigger App Open Ads
        ProcessLifecycleOwner.get().lifecycle.addObserver(this)
        appOpenAdManager = AppOpenAdManager()
        
        // Pre-fetch an ad on boot
        appOpenAdManager.loadAd()
    }

    /**
     * Triggered by DefaultLifecycleObserver when the app returns to the foreground.
     * We removed 'super.onStart' to resolve the 'Multiple supertypes' compilation error.
     */
    override fun onStart(owner: LifecycleOwner) {
        appOpenAdManager.showAdIfAvailable(currentActivity)
    }

    override fun onActivityStarted(activity: Activity) {
        currentActivity = activity
    }

    override fun onActivityResumed(activity: Activity) {
        currentActivity = activity
    }

    // Required overrides for ActivityLifecycleCallbacks (unused)
    override fun onActivityCreated(activity: Activity, savedInstanceState: Bundle?) {}
    override fun onActivityPaused(activity: Activity) {}
    override fun onActivityStopped(activity: Activity) {}
    override fun onActivitySaveInstanceState(activity: Activity, outState: Bundle) {}
    override fun onActivityDestroyed(activity: Activity) {
        if (currentActivity == activity) {
            currentActivity = null
        }
    }

    inner class AppOpenAdManager {
        private var appOpenAd: AppOpenAd? = null
        private var isLoadingAd = false
        var isShowingAd = false
        private var loadTime: Long = 0

        fun loadAd() {
            if (isLoadingAd || isAdAvailable()) return
            isLoadingAd = true
            
            val request = AdRequest.Builder().build()
            
            // Your Ad Unit ID: ca-app-pub-7732503595590477/4459993522
            AppOpenAd.load(
                this@WatermarkerApp,
                "ca-app-pub-7732503595590477/4459993522",
                request,
                AppOpenAd.APP_OPEN_AD_ORIENTATION_PORTRAIT,
                object : AppOpenAd.AppOpenAdLoadCallback() {
                    override fun onAdLoaded(ad: AppOpenAd) {
                        appOpenAd = ad
                        isLoadingAd = false
                        loadTime = Date().time
                    }
                    override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                        isLoadingAd = false
                    }
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

        fun showAdIfAvailable(activity: Activity?) {
            if (isShowingAd) return
            if (!isAdAvailable()) {
                loadAd()
                return
            }
            appOpenAd?.fullScreenContentCallback = object : FullScreenContentCallback() {
                override fun onAdDismissedFullScreenContent() {
                    appOpenAd = null
                    isShowingAd = false
                    loadAd()
                }
                override fun onAdFailedToShowFullScreenContent(adError: AdError) {
                    appOpenAd = null
                    isShowingAd = false
                    loadAd()
                }
                override fun onAdShowedFullScreenContent() {
                    isShowingAd = true
                }
            }
            activity?.let {
                appOpenAd?.show(it)
            }
        }
    }
}
"""
    with open(f"{package_path}/WatermarkerApp.kt", "w") as f:
        f.write(app_content)
    print("✅ 5-5 Generated WatermarkerApp.kt (Fixed Compilation & AdMob Ready)")

if __name__ == "__main__":
    generate()
