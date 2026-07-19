package com.example.nativebenchmarkapp

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.view.Choreographer
import android.view.Gravity
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.LinearInterpolator
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

private const val BOX_COUNT = 15
private const val MEASUREMENT_DURATION_MS = 60_000L
private const val BASE_ANIM_X_MS     = 1200L
private const val BASE_ANIM_Y_MS     = 900L
private const val BASE_ANIM_SCALE_MS = 1500L
private const val BASE_ANIM_ROT_MS   = 2000L
private const val ANIM_STEP_MS       = 50L
private const val TRANSLATE_X_DP = 50f
private const val TRANSLATE_Y_DP = 40f
private val BOX_COLORS = intArrayOf(
    0xFFE53935.toInt(),
    0xFF1E88E5.toInt(),
    0xFF43A047.toInt(),
    0xFFFB8C00.toInt(),
    0xFF8E24AA.toInt(),
    0xFF00ACC1.toInt(),
)

private val S3_COLOR_HEADING = 0xFF1A1A2E.toInt()

private enum class S3TestStatus { IDLE, RUNNING, FINISHED, STOPPED }

class Scenario3Activity : AppCompatActivity() {
    private lateinit var tvStatusLabel: TextView
    private lateinit var tvRenderFps: TextView
    private lateinit var tvMeasuredDuration: TextView
    private lateinit var btnStartTest: Button
    private lateinit var btnStop: Button
    private lateinit var btnBackToMenu: Button
    private lateinit var gridContainer: LinearLayout
    private var status = S3TestStatus.IDLE
    private var measurementStart = 0L
    private val mainHandler = Handler(Looper.getMainLooper())
    private var finishRunnable: Runnable? = null
    private val boxViews     = mutableListOf<View>()
    private val animatorSets = mutableListOf<AnimatorSet>()
    private var fpsActive     = false
    private var fpsFrameCount = 0
    private var fpsTickRunnable: Runnable? = null

    private val fpsFrameCallback = object : Choreographer.FrameCallback {
        override fun doFrame(frameTimeNanos: Long) {
            if (!fpsActive) return
            fpsFrameCount++
            Choreographer.getInstance().postFrameCallback(this)
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_scenario3)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main_s3)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        bindViews()
        buildGrid()
        setupClickListeners()
        refreshUI()
    }

    override fun onDestroy() {
        super.onDestroy()
        clearTimers()
        stopAnimations()
        stopFpsMeasurement()
    }

    private fun bindViews() {
        tvStatusLabel      = findViewById(R.id.tvS3StatusLabel)
        tvRenderFps        = findViewById(R.id.tvS3RenderFps)
        tvMeasuredDuration = findViewById(R.id.tvS3MeasuredDuration)
        btnStartTest       = findViewById(R.id.btnStartTest)
        btnStop            = findViewById(R.id.btnS3Stop)
        btnBackToMenu      = findViewById(R.id.btnS3BackToMenu)
        gridContainer      = findViewById(R.id.gridContainer)
    }
    private fun buildGrid() {
        val density     = resources.displayMetrics.density
        val boxSizePx   = (56 * density).toInt()
        val cornerRadPx = 8 * density
        val marginHPx   = (24 * density).toInt()

        for (row in 0 until 5) {
            val rowLayout = LinearLayout(this).apply {
                orientation  = LinearLayout.HORIZONTAL
                gravity      = Gravity.CENTER
                clipChildren = false
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    0,
                    1f,
                )
            }

            for (col in 0 until 3) {
                val i = row * 3 + col
                val drawable = GradientDrawable().apply {
                    setColor(BOX_COLORS[i % BOX_COLORS.size])
                    cornerRadius = cornerRadPx
                }
                val box = View(this).apply {
                    background   = drawable
                    layoutParams = LinearLayout.LayoutParams(boxSizePx, boxSizePx).apply {
                        setMargins(marginHPx, 0, marginHPx, 0)
                    }
                }
                boxViews.add(box)
                rowLayout.addView(box)
            }
            gridContainer.addView(rowLayout)
        }
    }

    private fun setupClickListeners() {
        btnStartTest.setOnClickListener  { startTest() }
        btnStop.setOnClickListener       { stopTest() }
        btnBackToMenu.setOnClickListener { finish() }
    }

    private fun startTest() {
        if (status == S3TestStatus.RUNNING) return

        stopAnimations()

        measurementStart = SystemClock.uptimeMillis()
        status = S3TestStatus.RUNNING
        refreshUI()

        val density      = resources.displayMetrics.density
        val translateXPx = TRANSLATE_X_DP * density
        val translateYPx = TRANSLATE_Y_DP * density
        val easeInOut    = AccelerateDecelerateInterpolator()
        val linear       = LinearInterpolator()
        boxViews.forEachIndexed { i, box ->
            val dX     = BASE_ANIM_X_MS     + i * ANIM_STEP_MS
            val dY     = BASE_ANIM_Y_MS     + i * ANIM_STEP_MS
            val dScale = BASE_ANIM_SCALE_MS + i * ANIM_STEP_MS
            val dRot   = BASE_ANIM_ROT_MS   + i * ANIM_STEP_MS
            val animX = ObjectAnimator.ofFloat(box, "translationX", -translateXPx, translateXPx).apply {
                duration     = dX
                repeatMode   = ValueAnimator.REVERSE
                repeatCount  = ValueAnimator.INFINITE
                interpolator = easeInOut
            }
            val animY = ObjectAnimator.ofFloat(box, "translationY", -translateYPx, translateYPx).apply {
                duration     = dY
                repeatMode   = ValueAnimator.REVERSE
                repeatCount  = ValueAnimator.INFINITE
                interpolator = easeInOut
            }
            val animScaleX = ObjectAnimator.ofFloat(box, "scaleX", 1f, 1.5f).apply {
                duration     = dScale
                repeatMode   = ValueAnimator.REVERSE
                repeatCount  = ValueAnimator.INFINITE
                interpolator = easeInOut
            }
            val animScaleY = ObjectAnimator.ofFloat(box, "scaleY", 1f, 1.5f).apply {
                duration     = dScale
                repeatMode   = ValueAnimator.REVERSE
                repeatCount  = ValueAnimator.INFINITE
                interpolator = easeInOut
            }
            val animRot = ObjectAnimator.ofFloat(box, "rotation", 0f, 360f).apply {
                duration     = dRot
                repeatMode   = ValueAnimator.RESTART
                repeatCount  = ValueAnimator.INFINITE
                interpolator = linear
            }

            val set = AnimatorSet().apply {
                playTogether(animX, animY, animScaleX, animScaleY, animRot)
            }
            animatorSets.add(set)
            set.start()
        }

        startFpsMeasurement()

        finishRunnable = Runnable {
            finishTest(stoppedEarly = false)
        }.also { mainHandler.postDelayed(it, MEASUREMENT_DURATION_MS) }
    }

    private fun stopTest() {
        if (status != S3TestStatus.RUNNING) return
        finishTest(stoppedEarly = true)
    }

    private fun finishTest(stoppedEarly: Boolean) {
        clearTimers()
        stopAnimations()
        stopFpsMeasurement()
        status = if (stoppedEarly) S3TestStatus.STOPPED else S3TestStatus.FINISHED
        val duration = if (measurementStart > 0L) SystemClock.uptimeMillis() - measurementStart else 0L
        tvMeasuredDuration.text = s3LabelValue("Measured Duration: ", "$duration ms")
        tvMeasuredDuration.visibility = View.VISIBLE
        refreshUI()
    }

    private fun stopAnimations() {
        animatorSets.forEach { it.cancel() }
        animatorSets.clear()
        boxViews.forEach { box ->
            box.translationX = 0f
            box.translationY = 0f
            box.scaleX       = 1f
            box.scaleY       = 1f
            box.rotation     = 0f
        }
    }

    private fun clearTimers() {
        finishRunnable?.let { mainHandler.removeCallbacks(it) }
        finishRunnable = null
    }

    private fun startFpsMeasurement() {
        fpsActive = true
        fpsFrameCount = 0
        tvRenderFps.text = s3LabelValue("Render FPS: ", "...")
        tvRenderFps.visibility = View.VISIBLE
        Choreographer.getInstance().postFrameCallback(fpsFrameCallback)
        val tick = object : Runnable {
            override fun run() {
                if (!fpsActive) return
                tvRenderFps.text = s3LabelValue("Render FPS: ", "$fpsFrameCount")
                fpsFrameCount = 0
                mainHandler.postDelayed(this, 1000L)
            }
        }
        fpsTickRunnable = tick
        mainHandler.postDelayed(tick, 1000L)
    }

    private fun stopFpsMeasurement() {
        fpsActive = false
        Choreographer.getInstance().removeFrameCallback(fpsFrameCallback)
        fpsTickRunnable?.let { mainHandler.removeCallbacks(it) }
        fpsTickRunnable = null
    }

    private fun refreshUI() {
        val isRunning = status == S3TestStatus.RUNNING

        val statusLabel = when (status) {
            S3TestStatus.IDLE     -> "Idle"
            S3TestStatus.RUNNING  -> "Running"
            S3TestStatus.FINISHED -> "Finished"
            S3TestStatus.STOPPED  -> "Stopped"
        }
        tvStatusLabel.text = s3LabelValue("Status: ", statusLabel)

        if (status == S3TestStatus.IDLE) {
            tvMeasuredDuration.visibility = View.GONE
            tvRenderFps.visibility = View.GONE
        }

        btnStartTest.isEnabled  = !isRunning
        btnStartTest.alpha      = if (isRunning) 0.38f else 1.0f
        btnStop.isEnabled       = isRunning
        btnStop.alpha           = if (!isRunning) 0.38f else 1.0f
        btnBackToMenu.isEnabled = !isRunning
        btnBackToMenu.alpha     = if (isRunning) 0.38f else 1.0f
    }
}

private fun s3LabelValue(label: String, value: String): SpannableString {
    val full = "$label$value"
    val ss   = SpannableString(full)
    val start = label.length
    ss.setSpan(StyleSpan(Typeface.BOLD),        start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    ss.setSpan(ForegroundColorSpan(S3_COLOR_HEADING), start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    return ss
}

