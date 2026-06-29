// ===== AllInOne.kt =====
// FILE DUY NHẤT: Chứa MainActivity, OverlayService, GestureService
// Có menu thu gọn: ban đầu chỉ 1 nút "Hiển thị menu", bấm vào sẽ hiện toàn bộ cài đặt
// Gồm: bật/tắt Aimbot, ESP, thanh kéo độ nhạy, kích thước vòng tròn, nút START màu xanh, nút STOP màu đỏ

package com.your.overlayapp

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.GestureDescription
import android.app.*
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.graphics.*
import android.hardware.display.DisplayManager
import android.hardware.display.VirtualDisplay
import android.media.ImageReader
import android.media.projection.MediaProjection
import android.media.projection.MediaProjectionManager
import android.os.*
import android.provider.Settings
import android.view.*
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.NotificationCompat
import java.util.concurrent.Executors

// ============================================================
// 1. MainActivity – Menu thu gọn với 1 nút bấm
// ============================================================
class MainActivity : AppCompatActivity() {

    private lateinit var prefs: SharedPreferences
    private lateinit var rootLayout: LinearLayout
    private var menuExpanded = false

    companion object {
        const val REQUEST_OVERLAY = 1
        const val REQUEST_PROJECTION = 2
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = getSharedPreferences("AimbotSettings", Context.MODE_PRIVATE)

        // Tạo root layout (dạng cuộn)
        val scroll = ScrollView(this)
        rootLayout = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(64, 64, 64, 64)
        }
        scroll.addView(rootLayout)

        // Ban đầu chỉ hiển thị nút mở menu
        showExpandButton()

        setContentView(scroll)
    }

    // Hiển thị nút "Hiển thị menu" (ban đầu)
    private fun showExpandButton() {
        rootLayout.removeAllViews()
        val expandBtn = Button(this).apply {
            text = "📋 HIỂN THỊ MENU & CÀI ĐẶT"
            textSize = 22f
            setBackgroundColor(Color.parseColor("#2196F3"))
            setTextColor(Color.WHITE)
            setPadding(32, 32, 32, 32)
            setOnClickListener {
                showFullMenu()
            }
        }
        rootLayout.addView(expandBtn)
    }

    // Hiển thị toàn bộ menu (thay thế nút ban đầu)
    private fun showFullMenu() {
        if (menuExpanded) return
        menuExpanded = true
        rootLayout.removeAllViews()

        // Tiêu đề
        rootLayout.addView(TextView(this).apply {
            text = "⚙️ CÀI ĐẶT AIMBOT"
            textSize = 28f
            typeface = Typeface.DEFAULT_BOLD
            gravity = Gravity.CENTER
            setPadding(0, 0, 0, 64)
        })

        // ---- Bật/Tắt Aimbot ----
        val aimbotSwitch = Switch(this).apply {
            text = "Kích hoạt Aimbot (tự động kéo)"
            textSize = 18f
            setPadding(0, 24, 0, 24)
            isChecked = prefs.getBoolean("aimbot_enabled", true)
            setOnCheckedChangeListener { _, isChecked ->
                prefs.edit().putBoolean("aimbot_enabled", isChecked).apply()
            }
        }
        rootLayout.addView(aimbotSwitch)

        // ---- Bật/Tắt ESP ----
        val espSwitch = Switch(this).apply {
            text = "Hiển thị ESP (đường chéo + tâm)"
            textSize = 18f
            setPadding(0, 24, 0, 24)
            isChecked = prefs.getBoolean("esp_enabled", true)
            setOnCheckedChangeListener { _, isChecked ->
                prefs.edit().putBoolean("esp_enabled", isChecked).apply()
            }
        }
        rootLayout.addView(espSwitch)

        // ---- Độ nhạy kéo (SeekBar) ----
        rootLayout.addView(TextView(this).apply {
            text = "Tốc độ kéo camera (độ nhạy)"
            textSize = 18f
            setPadding(0, 40, 0, 8)
        })
        val sensitivitySeek = SeekBar(this).apply {
            max = 100
            progress = prefs.getInt("sensitivity", 30)
            setPadding(0, 0, 0, 16)
        }
        val sensValue = TextView(this).apply {
            text = "Giá trị: ${sensitivitySeek.progress}%"
            textSize = 16f
            gravity = Gravity.END
        }
        sensitivitySeek.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                sensValue.text = "Giá trị: $progress%"
                prefs.edit().putInt("sensitivity", progress).apply()
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })
        rootLayout.addView(sensitivitySeek)
        rootLayout.addView(sensValue)

        // ---- Kích thước vòng tròn (đường kính) ----
        rootLayout.addView(TextView(this).apply {
            text = "Đường kính vòng tròn (dp)"
            textSize = 18f
            setPadding(0, 40, 0, 8)
        })
        val radiusSeek = SeekBar(this).apply {
            max = 120
            progress = prefs.getInt("circle_diameter", 60)
            setPadding(0, 0, 0, 16)
        }
        val radiusValue = TextView(this).apply {
            text = "Đường kính: ${radiusSeek.progress} dp"
            textSize = 16f
            gravity = Gravity.END
        }
        radiusSeek.setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
            override fun onProgressChanged(seekBar: SeekBar?, progress: Int, fromUser: Boolean) {
                radiusValue.text = "Đường kính: $progress dp"
                prefs.edit().putInt("circle_diameter", progress).apply()
            }
            override fun onStartTrackingTouch(seekBar: SeekBar?) {}
            override fun onStopTrackingTouch(seekBar: SeekBar?) {}
        })
        rootLayout.addView(radiusSeek)
        rootLayout.addView(radiusValue)

        // ---- Nút START màu xanh ----
        val btnStart = Button(this).apply {
            text = "▶ BẬT OVERLAY (ÁP DỤNG CÀI ĐẶT)"
            textSize = 20f
            setPadding(0, 40, 0, 40)
            setBackgroundColor(Color.parseColor("#4CAF50"))
            setTextColor(Color.WHITE)
            setOnClickListener {
                startAimbotService()
            }
        }
        rootLayout.addView(btnStart)

        // ---- Nút STOP màu đỏ ----
        val btnStop = Button(this).apply {
            text = "■ DỪNG OVERLAY"
            textSize = 20f
            setPadding(0, 40, 0, 40)
            setBackgroundColor(Color.parseColor("#F44336"))
            setTextColor(Color.WHITE)
            setOnClickListener {
                stopService(Intent(this@MainActivity, OverlayService::class.java))
                Toast.makeText(this@MainActivity, "Đã dừng", Toast.LENGTH_SHORT).show()
                updateStatusText()
            }
        }
        rootLayout.addView(btnStop)

        // ---- Trạng thái ----
        val statusText = TextView(this).apply {
            text = "Trạng thái: Chưa kích hoạt"
            textSize = 16f
            gravity = Gravity.CENTER
            setPadding(0, 32, 0, 0)
            setTextColor(Color.GRAY)
            id = View.generateViewId()
        }
        rootLayout.addView(statusText)

        // Cập nhật trạng thái ban đầu
        updateStatusText()

        // ---- Nút "Ẩn menu" (quay lại trạng thái ban đầu) ----
        val hideBtn = Button(this).apply {
            text = "🔙 Ẩn menu"
            textSize = 16f
            setPadding(0, 32, 0, 0)
            setBackgroundColor(Color.parseColor("#9E9E9E"))
            setTextColor(Color.WHITE)
            setOnClickListener {
                menuExpanded = false
                showExpandButton()
            }
        }
        rootLayout.addView(hideBtn)
    }

    // Hàm khởi động service (kiểm tra quyền)
    private fun startAimbotService() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && !Settings.canDrawOverlays(this)) {
            startActivityForResult(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION,
                android.net.Uri.parse("package:$packageName")), REQUEST_OVERLAY)
            return
        }
        if (!isAccessibilityEnabled()) {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
            Toast.makeText(this, "Bật GestureService trong Trợ năng", Toast.LENGTH_LONG).show()
            return
        }
        val pm = getSystemService(MEDIA_PROJECTION_SERVICE) as MediaProjectionManager
        startIntentSenderForResult(pm.createScreenCaptureIntent().intentSender, REQUEST_PROJECTION, null, 0, 0, 0)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        when (requestCode) {
            REQUEST_OVERLAY -> if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M && Settings.canDrawOverlays(this))
                Toast.makeText(this, "Quyền overlay đã cấp, bấm lại BẬT", Toast.LENGTH_SHORT).show()
            REQUEST_PROJECTION -> if (resultCode == RESULT_OK && data != null) {
                OverlayService.projectionIntent = data
                startService(Intent(this, OverlayService::class.java))
                Toast.makeText(this, "Overlay đang chạy", Toast.LENGTH_LONG).show()
                updateStatusText()
            }
        }
    }

    // Kiểm tra Accessibility đã bật chưa
    private fun isAccessibilityEnabled(): Boolean {
        val enabled = Settings.Secure.getString(contentResolver, Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES)
        return enabled?.contains(packageName) == true
    }

    // Cập nhật dòng trạng thái
    private fun updateStatusText() {
        val statusView = findViewById<TextView>(rootLayout.getChildAt(rootLayout.childCount - 2)?.id ?: 0)
        if (statusView != null) {
            if (isServiceRunning(OverlayService::class.java)) {
                statusView.text = "Trạng thái: ĐANG CHẠY"
                statusView.setTextColor(Color.GREEN)
            } else {
                statusView.text = "Trạng thái: Đã dừng"
                statusView.setTextColor(Color.RED)
            }
        }
    }

    private fun isServiceRunning(serviceClass: Class<*>): Boolean {
        val manager = getSystemService(ACTIVITY_SERVICE) as ActivityManager
        for (service in manager.getRunningServices(Int.MAX_VALUE)) {
            if (serviceClass.name == service.service.className) return true
        }
        return false
    }
}

// ============================================================
// 2. OverlayService – Vẽ overlay + chụp màn hình + aimbot
// ============================================================
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

    // Các biến cài đặt (đọc từ SharedPreferences)
    private var aimbotEnabled = true
    private var espEnabled = true
    private var sensitivity = 0.3f
    private var circleDiameter = 60f * density

    companion object {
        var projectionIntent: Intent? = null
        const val CHANNEL_ID = "overlay_channel"
        const val NOTIF_ID = 1
    }

    override fun onCreate() {
        super.onCreate()
        // Đọc cài đặt từ SharedPreferences
        val prefs = getSharedPreferences("AimbotSettings", Context.MODE_PRIVATE)
        aimbotEnabled = prefs.getBoolean("aimbot_enabled", true)
        espEnabled = prefs.getBoolean("esp_enabled", true)
        sensitivity = prefs.getInt("sensitivity", 30) / 100f
        circleDiameter = prefs.getInt("circle_diameter", 60).toFloat() * density

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

                if (espEnabled) {
                    // 2 đường chéo
                    canvas?.drawLine(0f, 0f, w, h, linePaint)
                    canvas?.drawLine(0f, h, w, 0f, linePaint)
                    // Tâm
                    canvas?.drawCircle(cx, cy, 10f, dotPaint)
                    // Vòng tròn (đường kính theo cài đặt)
                    canvas?.drawCircle(cx, cy, circleDiameter/2f, circlePaint)
                }

                if (aimbotEnabled && targetX >= 0 && targetY >= 0) {
                    canvas?.drawCircle(targetX, targetY, 20f, aimPaint)
                }
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
                    // Màu đỏ đặc trưng (có thể điều chỉnh)
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
                if (gesture != null && aimbotEnabled) {
                    val sw = resources.displayMetrics.widthPixels.toFloat()
                    val sh = resources.displayMetrics.heightPixels.toFloat()
                    val cx = sw/2f; val cy = sh/2f
                    val dx = bestX - cx; val dy = bestY - cy
                    if (Math.abs(dx) > 30 || Math.abs(dy) > 30) {
                        val endX = cx + dx * sensitivity
                        val endY = cy + dy * sensitivity
                        gesture.performSwipe(cx, cy, endX, endY, 200L)
                    }
                }
            } else {
                targetX = -1f; targetY = -1f
            }

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

// ============================================================
// 3. GestureService – Gửi cử chỉ kéo (swipe)
// ============================================================
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
