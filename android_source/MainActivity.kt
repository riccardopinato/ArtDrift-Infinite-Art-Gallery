package com.riccardopinato.artdrift

import android.app.WallpaperManager
import android.os.Build
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel
import java.io.ByteArrayInputStream

/** User-triggered wallpaper only: no Accessibility or background service. */
class MainActivity : FlutterActivity() {
    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, "artdrift/wallpaper")
            .setMethodCallHandler { call, result ->
                if (call.method != "setWallpaper") {
                    result.notImplemented()
                    return@setMethodCallHandler
                }
                val bytes = call.argument<ByteArray>("bytes")
                val target = call.argument<String>("target")
                if (bytes == null || bytes.isEmpty() || bytes.size > 24 * 1024 * 1024) {
                    result.error("INVALID_IMAGE", "Wallpaper data invalid", null)
                    return@setMethodCallHandler
                }
                val flags = when (target) {
                    "home" -> WallpaperManager.FLAG_SYSTEM
                    "lock" -> WallpaperManager.FLAG_LOCK
                    "both" -> WallpaperManager.FLAG_SYSTEM or WallpaperManager.FLAG_LOCK
                    else -> {
                        result.error("INVALID_TARGET", "Invalid wallpaper target", null)
                        return@setMethodCallHandler
                    }
                }
                if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) {
                    result.error("UNSUPPORTED", "Requires Android 7 or newer", null)
                    return@setMethodCallHandler
                }
                val manager = WallpaperManager.getInstance(applicationContext)
                if (!manager.isWallpaperSupported || !manager.isSetWallpaperAllowed) {
                    result.error("DISABLED", "Wallpaper is not permitted on this device", null)
                    return@setMethodCallHandler
                }
                Thread {
                    try {
                        ByteArrayInputStream(bytes).use { input ->
                            manager.setStream(input, null, true, flags)
                        }
                        runOnUiThread { result.success(true) }
                    } catch (e: Exception) {
                        runOnUiThread { result.error("WALLPAPER_ERROR", e.message, null) }
                    }
                }.start()
            }
    }
}
