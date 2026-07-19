package com.example.nativebenchmarkapp

import android.graphics.Typeface
import android.os.Bundle
import android.os.SystemClock
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.view.View
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

private const val OPERATION_COUNT = 10_000
private val S4_COLOR_HEADING = 0xFF1A1A2E.toInt()

private enum class S4TestStatus { IDLE, RUNNING, FINISHED }

class Scenario4Activity : AppCompatActivity() {

    private lateinit var tvStatusLabel:      TextView
    private lateinit var tvMeasuredDuration: TextView
    private lateinit var tvOpsPerSec:        TextView
    private lateinit var btnStartTest:       Button
    private lateinit var btnStop:            Button
    private lateinit var btnBackToMenu:      Button

    private var status = S4TestStatus.IDLE
    private var lastAccumulatedResult = 0

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_scenario4)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main_s4)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        bindViews()
        setupClickListeners()
        refreshUI()
    }

    private fun bindViews() {
        tvStatusLabel      = findViewById(R.id.tvS4StatusLabel)
        tvMeasuredDuration = findViewById(R.id.tvS4MeasuredDuration)
        tvOpsPerSec        = findViewById(R.id.tvS4OpsPerSec)
        btnStartTest       = findViewById(R.id.btnS4StartTest)
        btnStop            = findViewById(R.id.btnS4Stop)
        btnBackToMenu      = findViewById(R.id.btnS4BackToMenu)
    }

    private fun setupClickListeners() {
        btnStartTest.setOnClickListener  { startTest() }
        btnBackToMenu.setOnClickListener { finish() }
    }
    private fun increment(value: Int): Int = value + 1

    private fun startTest() {
        if (status == S4TestStatus.RUNNING) return

        status = S4TestStatus.RUNNING
        refreshUI()
        val startMs = SystemClock.uptimeMillis()
        var acc = 0
        for (i in 0 until OPERATION_COUNT) {
            acc += increment(i)
        }
        val durationMs = SystemClock.uptimeMillis() - startMs
        lastAccumulatedResult = acc

        val opsPerSec = if (durationMs > 0) (OPERATION_COUNT * 1000L / durationMs) else Long.MAX_VALUE

        tvMeasuredDuration.text = s4LabelValue(
            "Measured Duration: ", "$durationMs ms"
        )
        tvMeasuredDuration.visibility = View.VISIBLE

        tvOpsPerSec.text = s4LabelValue(
            "Operations per second: ", "%,d".format(opsPerSec)
        )
        tvOpsPerSec.visibility = View.VISIBLE

        status = S4TestStatus.FINISHED
        refreshUI()
    }

    private fun refreshUI() {
        val isRunning = status == S4TestStatus.RUNNING

        val statusLabel = when (status) {
            S4TestStatus.IDLE     -> "Idle"
            S4TestStatus.RUNNING  -> "Running"
            S4TestStatus.FINISHED -> "Finished"
        }
        tvStatusLabel.text = s4LabelValue("Status: ", statusLabel)

        if (status == S4TestStatus.IDLE) {
            tvMeasuredDuration.visibility = View.GONE
            tvOpsPerSec.visibility        = View.GONE
        }

        btnStartTest.isEnabled  = !isRunning
        btnStartTest.alpha      = if (isRunning) 0.38f else 1.0f
        btnStop.isEnabled       = false
        btnStop.alpha           = 0.38f
        btnBackToMenu.isEnabled = !isRunning
        btnBackToMenu.alpha     = if (isRunning) 0.38f else 1.0f
    }
}

private fun s4LabelValue(label: String, value: String): SpannableString {
    val full = "$label$value"
    val ss   = SpannableString(full)
    val start = label.length
    ss.setSpan(StyleSpan(Typeface.BOLD),              start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    ss.setSpan(ForegroundColorSpan(S4_COLOR_HEADING), start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    return ss
}

