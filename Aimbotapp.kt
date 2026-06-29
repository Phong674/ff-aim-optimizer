package com.your.overlayapp

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.app.*
import android.content.Context
import android.content.Intent
import android.graphics.*
import android.graphics.PixelFormat
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.provider.Settings
import android.view.*
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.NotificationCompat
import java.util.concurrent.Executors

// ===== 1. MainActivity =====
class MainActivity : AppCompatActivity() {
    private val REQUEST_OVERLAY = 1
    private val REQUEST_PROJECTION = 2

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Tạo layout động: 2 nút
        val layout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            gravity = Gravity.CENTER
            setPadding(32, 32, 32, 32)
        }
        val btnStart = Button(this).apply {
            text = "BẬT OVERLAY & AIMBOT"
            setOnClickListener {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this@MainActivity)) {
                    startActivityForResult(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                        android.net.Uri.parse("package:$packageName")), REQUEST_OVERLAY)
                    return@setOnClickListener
                }
                if (!isAccessibilityEnabled()) {
                    startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
                    Toast.makeText(this@MainActivity, "Bật GestureService trong Trợ năng", Toast.LENGTH_LONG).show()
                    return@setOnClickListener
                }
                val pm = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
                startIntentSenderForResult(pm.createScreenCaptureIntent().intentSender, REQUEST_PROJECTION, null, 0, 0, 0)
            }
        }
        val btnStop = Button(this).apply {
            text = "TẮT OVERLAY"
            setOnClickListener {
                stopService(Intent(this@MainActivity, OverlayService::class.java))
                Toast.makeText(this@MainActivity, "Đã tắt", Toast.LENGTH_SHORT).show()
            }
        }
        layout.addView(btnStart)
        layout.addView(btnStop, LinearLayout.LayoutParams(
            LinearLayout.LayoutParams.WRAP_CONTENT,
            LinearLayout.LayoutParams.WRAP_CONTENT
        ).apply { topMargin = 48 })
        setContentView(layout)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        when (requestCode) {
            REQUEST_OVERLAY -> if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && Settings.canDrawOverlays(this))
                Toast.makeText(this, "Quyền overlay đã cấp", Toast.LENGTH_SHORT).show()
            REQUEST_PROJECTION -> if (resultCode == RESULT_OK && data != null) {
                OverlayService.projectionIntent = data
                startService(Intent(this, OverlayService::class.java))
                Toast.makeText(this, "Overlay đang chạy", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun isAccessibilityEnabled(): Boolean {
        val enabled = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
        return enabled?.contains(packageName) == true
    }
}

// ===== 2. OverlayService =====
class OverlayService : Service() {
    private lateinit var windowManager: WindowManager
    private lateinit var overlayView: View
    private val mainHandler = Handler(Looper.getMainLooper())
    private val executor = Executors.newSingleThreadExecutor()
    private var mediaProjection: MediaProjection? = null
    private var virtualDisplay: VirtualDisplay? = null
    private var imageReader: ImageReader? = null
    private var targetX = -1f
    private var targetY = -1f
    private val density by lazy { resources.displayMetrics.density }

    companion object {
        var projectionIntent: Intent? = null
        const val CHANNEL_ID = "overlay_channel"
        const val NOTIF_ID = 1
    }

    override fun onCreate() {
        super.onCreate()
        windowManager = getSystemService(WINDOW_SERVICE) as WindowManager
        createOverlayView()
        startForeground(NOTIF_ID, buildNotification())
        startMediaProjection()
        startDetectionLoop()
    }

    private fun createOverlayView() {
        val layout = object : FrameLayout(this) {
            private val linePaint = Paint().apply { color = Color.RED; style = Paint.Style.STROKE; strokeWidth = 4f; isAntiAlias = true }
            private val circlePaint = Paint().apply { color = Color.GREEN; style = Paint.Style.STROKE; strokeWidth = 3f; isAntiAlias = true }
            private val dotPaint = Paint().apply { color = Color.RED; style = Paint.Style.FILL }
            private val aimPaint = Paint().apply { color = Color.YELLOW; style = Paint.Style.FILL_AND_STROKE; strokeWidth = 5f }

            override fun onDraw(canvas: Canvas?) {
                super.onDraw(canvas)
                val w = width.toFloat(); val h = height.toFloat(); val cx = w/2f; val cy = h/2f
                canvas?.drawLine(0f, 0f, w, h, linePaint)
                canvas?.drawLine(0f, h, w, 0f, linePaint)
                canvas?.drawCircle(cx, cy, 10f, dotPaint)
                val radiusPx = 30f * density
                canvas?.drawCircle(cx, cy, radiusPx, circlePaint)
                if (targetX >= 0 && targetY >= 0) canvas?.drawCircle(targetX, targetY, 20f, aimPaint)
            }
        }

        val params = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL or
                        WindowManager.LayoutParams.FLAG_LAYOUT_IN_SCREEN,
                PixelFormat.TRANSLUCENT
            )
        } else {
            WindowManager.LayoutParams(
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.MATCH_PARENT,
                WindowManager.LayoutParams.TYPE_PHONE,
                WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE or
                        WindowManager.LayoutParams.FLAG_NOT_TOUCH_MODAL,
                PixelFormat.TRANSLUCENT
            )
        }
        params.gravity = Gravity.TOP or Gravity.START
        overlayView = layout
        windowManager.addView(overlayView, params)
    }

    private fun buildNotification(): Notification {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val ch = NotificationChannel(CHANNEL_ID, "Overlay", NotificationManager.IMPORTANCE_LOW)
            getSystemService(NotificationManager::class.java).createNotificationChannel(ch)
        }
        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("Overlay ESP đang chạy")
            .setSmallIcon(android.R.drawable.ic_menu_camera)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    private fun startMediaProjection() {
        val intent = projectionIntent ?: return
        val pm = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        mediaProjection = pm.getMediaProjection(Activity.RESULT_OK, intent)
        val w = resources.displayMetrics.widthPixels
        val h = resources.displayMetrics.heightPixels
        imageReader = ImageReader.newInstance(w, h, PixelFormat.RGBA_8888, 2)
        virtualDisplay = mediaProjection?.createVirtualDisplay(
            "Capture", w, h, density.toInt(),
            DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
            imageReader?.surface, null, null
        )
    }

    private fun startDetectionLoop() {
        mainHandler.post(object : Runnable {
            override fun run() {
                executor.execute { captureAndDetect() }
                mainHandler.postDelayed(this, 100)
            }
        })
    }

    private fun captureAndDetect() {
        val image = imageReader?.acquireLatestImage() ?: return
        try {
            val planes = image.planes
            val buffer = planes[0].buffer
            val w = image.width; val h = image.height
            val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
            bitmap.copyPixelsFromBuffer(buffer)

            var bestX = -1f; var bestY = -1f; var bestScore = 0
            for (y in 0 until h step 4) {
                for (x in 0 until w step 4) {
                    val p = bitmap.getPixel(x, y)
                    val r = Color.red(p); val g = Color.green(p); val b = Color.blue(p)
                    if (Math.abs(r - 200) < 45 && Math.abs(g - 50) < 45 && Math.abs(b - 50) < 45) {
                        val cx = w/2f; val cy = h/2f
                        val dist = Math.hypot((x - cx).toDouble(), (y - cy).toDouble())
                        val score = (1000 - dist).toInt()
                        if (score > bestScore) { bestScore = score; bestX = x.toFloat(); bestY = y.toFloat() }
                    }
                }
            }

            if (bestX >= 0 && bestY >= 0) {
                targetX = bestX; targetY = bestY
                val gesture = GestureService.instance
                if (gesture != null) {
                    val sw = resources.displayMetrics.widthPixels.toFloat()
                    val sh = resources.displayMetrics.heightPixels.toFloat()
                    val cx = sw/2f; val cy = sh/2f
                    val dx = bestX - cx; val dy = bestY - cy
                    if (Math.abs(dx) > 30 || Math.abs(dy) > 30) {
                        gesture.performSwipe(cx, cy, cx + dx*0.3f, cy + dy*0.3f, 200L)
                    }
                }
            } else { targetX = -1f; targetY = -1f }

            bitmap.recycle()
        } finally { image.close() }
    }

    override fun onDestroy() {
        super.onDestroy()
        mainHandler.removeCallbacksAndMessages(null)
        virtualDisplay?.release()
        mediaProjection?.stop()
        imageReader?.close()
        if (::overlayView.isInitialized) windowManager.removeView(overlayView)
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

// ===== 3. GestureService =====
class GestureService : AccessibilityService() {
    companion object { @Volatile var instance: GestureService? = null }

    override fun onServiceConnected() { super.onServiceConnected(); instance = this }
    override fun onAccessibilityEvent(event: android.view.accessibility.AccessibilityEvent?) {}
    override fun onInterrupt() {}

    fun performSwipe(startX: Float, startY: Float, endX: Float, endY: Float, duration: Long) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.N) return
        val path = Path().apply { moveTo(startX, startY); lineTo(endX, endY) }
        val gesture = GestureDescription.Builder()
            .addStroke(GestureDescription.StrokeDescription(path, 0, duration))
            .build()
        dispatchGesture(gesture, null, null)
    }

    override fun onDestroy() { instance = null; super.onDestroy() }
}
