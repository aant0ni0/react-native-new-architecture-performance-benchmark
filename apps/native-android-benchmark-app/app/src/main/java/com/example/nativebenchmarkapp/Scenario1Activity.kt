package com.example.nativebenchmarkapp

import android.content.res.ColorStateList
import android.graphics.Typeface
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.view.Choreographer
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.DividerItemDecoration
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.google.android.material.card.MaterialCardView
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin
private const val ITEM_COUNT = 20
private val INTERVAL_OPTIONS = intArrayOf(1000, 200, 100, 50)
private const val WARMUP_DURATION_MS = 10_000L
private const val MEASUREMENT_DURATION_MS = 60_000L

private val COLOR_HEADING  = 0xFF1A1A2E.toInt()
private val COLOR_LABEL    = 0xFF555555.toInt()
private val COLOR_INCREASE = 0xFF00AA00.toInt()
private val COLOR_DECREASE = 0xFFCC0000.toInt()
private val COLOR_NEUTRAL  = 0xFF888888.toInt()
private data class DataItem(
    val id: Int,
    val name: String,
    val baseValue: Double,
    val currentValue: Double,
    val changePercent: Double,
    val previousValue: Double
)
private enum class TestStatus { IDLE, RUNNING, FINISHED, STOPPED }
private data class Metrics(
    val avgLatency: Double,
    val minLatency: Long,
    val maxLatency: Long,
    val p50Latency: Long,
    val p95Latency: Long,
    val p99Latency: Long,
    val latencySamples: Int,
    val totalUpdates: Int,
    val measuredDurationMs: Long,
    val stoppedEarly: Boolean
)
private fun percentile(sorted: List<Long>, p: Int): Long {
    if (sorted.isEmpty()) return 0L
    val idx = ((p / 100.0) * sorted.size).toInt().coerceIn(0, sorted.size - 1)
    return sorted[idx]
}
private fun generateInitialData(): List<DataItem> =
    List(ITEM_COUNT) { i ->
        val baseValue = 100.0 + i * 5.0
        DataItem(
            id = i,
            name = "ITEM_${(i + 1).toString().padStart(2, '0')}",
            baseValue = baseValue,
            currentValue = baseValue,
            changePercent = 0.0,
            previousValue = baseValue
        )
    }
private fun computeNewValue(baseValue: Double, t: Int, i: Int): Double =
    baseValue +
        4.0 * sin(t / 8.0 + i * 0.7) +
        1.5 * cos(t / 5.0 + i * 0.35)
private fun labelValue(label: String, value: String): SpannableString {
    val full = "$label$value"
    val ss = SpannableString(full)
    val start = label.length
    ss.setSpan(StyleSpan(Typeface.BOLD), start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    ss.setSpan(ForegroundColorSpan(COLOR_HEADING), start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    return ss
}

private class DataAdapter : RecyclerView.Adapter<DataAdapter.ViewHolder>() {

    private var items: List<DataItem> = generateInitialData()
    fun updateData(newItems: List<DataItem>) {
        items = newItems
        for (i in newItems.indices) {
            notifyItemChanged(i)
        }
    }
    fun resetData() {
        items = generateInitialData()
        notifyDataSetChanged()
    }
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_data, parent, false)
        return ViewHolder(view)
    }
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        private val tvName: TextView   = view.findViewById(R.id.tvItemName)
        private val tvValue: TextView  = view.findViewById(R.id.tvItemValue)
        private val tvChange: TextView = view.findViewById(R.id.tvItemChange)
        fun bind(item: DataItem) {
            val color = when {
                item.currentValue > item.previousValue -> COLOR_INCREASE
                item.currentValue < item.previousValue -> COLOR_DECREASE
                else -> COLOR_NEUTRAL
            }
            val sign = if (item.changePercent >= 0) "+" else ""

            tvName.text = item.name
            tvValue.text = "%.2f".format(item.currentValue)
            tvValue.setTextColor(color)
            tvChange.text = "$sign${"%.2f".format(item.changePercent)}%"
            tvChange.setTextColor(color)
        }
    }
}
class Scenario1Activity : AppCompatActivity() {
    private lateinit var tvStatusLabel: TextView
    private lateinit var tvIntervalLabel: TextView
    private lateinit var tvUpdateCountLabel: TextView
    private lateinit var btnStart: Button
    private lateinit var btnStop: Button
    private lateinit var btnBackToMenu: Button
    private lateinit var intervalButtons: List<Pair<Int, Button>>
    private lateinit var metricsCard: MaterialCardView
    private lateinit var tvMetricsTitle: TextView
    private lateinit var tvAvgLatency: TextView
    private lateinit var tvMinLatency: TextView
    private lateinit var tvMaxLatency: TextView
    private lateinit var tvP50Latency: TextView
    private lateinit var tvP95Latency: TextView
    private lateinit var tvP99Latency: TextView
    private lateinit var tvLatencySamples: TextView
    private lateinit var tvTotalUpdates: TextView
    private lateinit var tvMeasuredDuration: TextView
    private lateinit var recyclerView: RecyclerView
    private lateinit var dataAdapter: DataAdapter
    private var status = TestStatus.IDLE
    private var selectedInterval = 100
    private var isWarmup = false
    private var updateCount = 0
    private var updateIndex = 0
    private var measurementStart = 0L
    private var currentData: List<DataItem> = generateInitialData()
    private val latencySamples = mutableListOf<Long>()
    private var dataGeneratedAt = 0L
    private var pendingLatencySeq = 0
    private var lastRecordedSeq = 0
    private val mainHandler = Handler(Looper.getMainLooper())
    private var schedulerActive = false
    private var schedulerRunnable: Runnable? = null
    private var warmupRunnable: Runnable? = null
    private var finishRunnable: Runnable? = null
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_scenario1)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main_s1)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }

        bindViews()
        setupClickListeners()
        refreshUI()
    }
    override fun onDestroy() {
        super.onDestroy()
        clearTimers()
    }
    private fun bindViews() {
        tvStatusLabel      = findViewById(R.id.tvStatusLabel)
        tvIntervalLabel    = findViewById(R.id.tvIntervalLabel)
        tvUpdateCountLabel = findViewById(R.id.tvUpdateCountLabel)
        btnStart           = findViewById(R.id.btnStart)
        btnStop            = findViewById(R.id.btnStop)
        btnBackToMenu      = findViewById(R.id.btnBackToMenu)
        metricsCard        = findViewById(R.id.metricsCard)
        tvMetricsTitle     = findViewById(R.id.tvMetricsTitle)
        tvAvgLatency       = findViewById(R.id.tvAvgLatency)
        tvMinLatency       = findViewById(R.id.tvMinLatency)
        tvMaxLatency       = findViewById(R.id.tvMaxLatency)
        tvP50Latency       = findViewById(R.id.tvP50Latency)
        tvP95Latency       = findViewById(R.id.tvP95Latency)
        tvP99Latency       = findViewById(R.id.tvP99Latency)
        tvLatencySamples   = findViewById(R.id.tvLatencySamples)
        tvTotalUpdates     = findViewById(R.id.tvTotalUpdates)
        tvMeasuredDuration = findViewById(R.id.tvMeasuredDuration)

        recyclerView = findViewById(R.id.recyclerView)
        dataAdapter  = DataAdapter()
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = dataAdapter
        recyclerView.itemAnimator = null
        recyclerView.addItemDecoration(
            DividerItemDecoration(this, DividerItemDecoration.VERTICAL)
        )
        intervalButtons = listOf(
            1000 to findViewById(R.id.btn1000ms),
            200  to findViewById(R.id.btn200ms),
            100  to findViewById(R.id.btn100ms),
            50   to findViewById(R.id.btn50ms)
        )
    }
    private fun setupClickListeners() {
        btnStart.setOnClickListener      { startTest() }
        btnStop.setOnClickListener       { stopTest() }
        btnBackToMenu.setOnClickListener { finish() }

        for ((interval, button) in intervalButtons) {
            button.setOnClickListener {
                if (status != TestStatus.RUNNING) {
                    selectedInterval = interval
                    refreshUI()
                }
            }
        }
    }
    private fun startTest() {
        if (status == TestStatus.RUNNING) return

        updateIndex = 0
        updateCount = 0
        latencySamples.clear()
        dataGeneratedAt = 0L
        pendingLatencySeq = 0
        lastRecordedSeq = 0
        measurementStart = 0L
        isWarmup = true
        status = TestStatus.RUNNING
        currentData = generateInitialData()

        dataAdapter.resetData()
        refreshUI()

        schedulerActive = true
        val interval = selectedInterval.toLong()
        val startedAt = SystemClock.uptimeMillis()
        var tick = 1L

        val schedule = object : Runnable {
            override fun run() {
                if (!schedulerActive) return
                performUpdate()
                val next = max(0L, startedAt + tick * interval - SystemClock.uptimeMillis())
                tick++
                schedulerRunnable = this
                mainHandler.postDelayed(this, next)
            }
        }
        schedulerRunnable = schedule
        mainHandler.postDelayed(schedule, interval)
        warmupRunnable = Runnable {
            isWarmup = false
            measurementStart = SystemClock.uptimeMillis()
            refreshUI()
        }.also { mainHandler.postDelayed(it, WARMUP_DURATION_MS) }

        finishRunnable = Runnable {
            finishTest()
        }.also { mainHandler.postDelayed(it, WARMUP_DURATION_MS + MEASUREMENT_DURATION_MS) }
    }
    private fun stopTest() {
        if (status != TestStatus.RUNNING) return
        clearTimers()
        isWarmup = false
        status = TestStatus.STOPPED
        finalizeMetrics(stoppedEarly = true)
        refreshUI()
    }
    private fun finishTest() {
        clearTimers()
        isWarmup = false
        status = TestStatus.FINISHED
        finalizeMetrics(stoppedEarly = false)
        refreshUI()
    }
    private fun clearTimers() {
        schedulerActive = false
        schedulerRunnable?.let { mainHandler.removeCallbacks(it) }
        schedulerRunnable = null
        warmupRunnable?.let { mainHandler.removeCallbacks(it) }
        warmupRunnable = null
        finishRunnable?.let { mainHandler.removeCallbacks(it) }
        finishRunnable = null
    }
    private fun performUpdate() {
        if (status != TestStatus.RUNNING) return

        val t = updateIndex

        val newData = currentData.map { item ->
            val newValue = computeNewValue(item.baseValue, t, item.id)
            val changePercent = (newValue - item.baseValue) / item.baseValue * 100.0
            item.copy(
                previousValue = item.currentValue,
                currentValue = newValue,
                changePercent = changePercent
            )
        }

        if (!isWarmup) {
            dataGeneratedAt = SystemClock.uptimeMillis()
            pendingLatencySeq++
        }

        currentData = newData
        dataAdapter.updateData(newData)

        updateIndex++

        if (!isWarmup) {
            updateCount++
            tvUpdateCountLabel.text = labelValue("Updates: ", updateCount.toString())
            val capturedSeq = pendingLatencySeq
            val capturedAt  = dataGeneratedAt

            Choreographer.getInstance().postFrameCallback { _ ->
                if (status == TestStatus.RUNNING &&
                    !isWarmup &&
                    capturedAt > 0L &&
                    capturedSeq > lastRecordedSeq
                ) {
                    val latency = SystemClock.uptimeMillis() - capturedAt
                    latencySamples.add(latency)
                    lastRecordedSeq = capturedSeq
                }
            }
        }
    }
    private fun finalizeMetrics(stoppedEarly: Boolean) {
        val measuredDurationMs =
            if (measurementStart > 0L) SystemClock.uptimeMillis() - measurementStart else 0L

        val avg = if (latencySamples.isNotEmpty())
            latencySamples.sum().toDouble() / latencySamples.size else 0.0
        val min = if (latencySamples.isNotEmpty()) latencySamples.min() else 0L
        val max = if (latencySamples.isNotEmpty()) latencySamples.max() else 0L
        val sorted = latencySamples.sorted()
        val p50 = percentile(sorted, 50)
        val p95 = percentile(sorted, 95)
        val p99 = percentile(sorted, 99)

        showMetrics(
            Metrics(
                avgLatency         = avg,
                minLatency         = min,
                maxLatency         = max,
                p50Latency         = p50,
                p95Latency         = p95,
                p99Latency         = p99,
                latencySamples     = latencySamples.size,
                totalUpdates       = updateCount,
                measuredDurationMs = measuredDurationMs,
                stoppedEarly       = stoppedEarly
            )
        )
    }
    private fun showMetrics(m: Metrics) {
        tvMetricsTitle.text     = if (m.stoppedEarly) "Results (stopped early)" else "Results"
        tvAvgLatency.text       = labelValue("Avg Latency: ",       "%.2f ms".format(m.avgLatency))
        tvMinLatency.text       = labelValue("Min Latency: ",       "${m.minLatency} ms")
        tvMaxLatency.text       = labelValue("Max Latency: ",       "${m.maxLatency} ms")
        tvP50Latency.text       = labelValue("p50 Latency: ",       "${m.p50Latency} ms")
        tvP95Latency.text       = labelValue("p95 Latency: ",       "${m.p95Latency} ms")
        tvP99Latency.text       = labelValue("p99 Latency: ",       "${m.p99Latency} ms")
        tvLatencySamples.text   = labelValue("Latency Samples: ",   "${m.latencySamples}")
        tvTotalUpdates.text     = labelValue("Total Updates: ",     "${m.totalUpdates}")
        tvMeasuredDuration.text = labelValue("Measured Duration: ", "${m.measuredDurationMs} ms")
        metricsCard.visibility  = View.VISIBLE
    }
    private fun refreshUI() {
        val isRunning = status == TestStatus.RUNNING

        val statusLabel = when {
            isRunning && isWarmup     -> "Running (Warmup)"
            status == TestStatus.IDLE     -> "Idle"
            status == TestStatus.RUNNING  -> "Running"
            status == TestStatus.FINISHED -> "Finished"
            status == TestStatus.STOPPED  -> "Stopped"
            else -> status.name
        }
        tvStatusLabel.text      = labelValue("Status: ",   statusLabel)
        tvIntervalLabel.text    = labelValue("Interval: ", "$selectedInterval ms")
        tvUpdateCountLabel.text = labelValue("Updates: ",  "$updateCount")

        btnStart.isEnabled = !isRunning
        btnStart.alpha     = if (isRunning) 0.38f else 1.0f
        btnStop.isEnabled  = isRunning
        btnStop.alpha      = if (!isRunning) 0.38f else 1.0f
        btnBackToMenu.isEnabled = !isRunning
        btnBackToMenu.alpha     = if (isRunning) 0.38f else 1.0f

        for ((interval, button) in intervalButtons) {
            val selected = interval == selectedInterval
            button.isEnabled = !isRunning
            button.alpha     = if (isRunning) 0.38f else 1.0f
            if (selected) {
                button.backgroundTintList = ColorStateList.valueOf(0xFF1A1A2E.toInt())
                button.setTextColor(0xFFFFFFFF.toInt())
            } else {
                button.backgroundTintList = ColorStateList.valueOf(0xFFEEEEEE.toInt())
                button.setTextColor(0xFF444444.toInt())
            }
        }
        if (status == TestStatus.IDLE || (isRunning && updateCount == 0)) {
            metricsCard.visibility = View.GONE
        }
    }
}

