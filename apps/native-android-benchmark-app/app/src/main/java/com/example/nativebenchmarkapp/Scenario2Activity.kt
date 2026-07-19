package com.example.nativebenchmarkapp

import android.graphics.Typeface
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.SystemClock
import android.text.SpannableString
import android.text.Spanned
import android.text.style.ForegroundColorSpan
import android.text.style.StyleSpan
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
private const val ITEM_COUNT_S2 = 1000
private const val MEASUREMENT_DURATION_S2_MS = 60_000L
private const val SCROLL_STEP_DP = 200
private const val SCROLL_TICK_MS = 16L
private val S2_COLOR_HEADING = 0xFF1A1A2E.toInt()
private data class ScrollItem(
    val id: Int,
    val name: String,
    val subtitle: String,
    val value: Double,
    val status: String
)
private enum class S2TestStatus { IDLE, RUNNING, FINISHED, STOPPED }
private fun generateScrollData(): List<ScrollItem> =
    List(ITEM_COUNT_S2) { i ->
        ScrollItem(
            id       = i,
            name     = "ITEM_${(i + 1).toString().padStart(4, '0')}",
            subtitle = if (i % 2 == 0) "Category A" else "Category B",
            value    = 100.0 + i * 0.75,
            status   = if (i % 2 == 0) "ACTIVE" else "INACTIVE"
        )
    }
private fun s2LabelValue(label: String, value: String): SpannableString {
    val full = "$label$value"
    val ss = SpannableString(full)
    val start = label.length
    ss.setSpan(StyleSpan(Typeface.BOLD), start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    ss.setSpan(ForegroundColorSpan(S2_COLOR_HEADING), start, full.length, Spanned.SPAN_EXCLUSIVE_EXCLUSIVE)
    return ss
}
private class ScrollAdapter(private val items: List<ScrollItem>) :
    RecyclerView.Adapter<ScrollAdapter.ViewHolder>() {
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val view = LayoutInflater.from(parent.context)
            .inflate(R.layout.item_scroll, parent, false)
        return ViewHolder(view)
    }
    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        holder.bind(items[position])
    }

    override fun getItemCount(): Int = items.size

    class ViewHolder(view: View) : RecyclerView.ViewHolder(view) {
        private val tvName: TextView     = view.findViewById(R.id.tvScrollItemName)
        private val tvSubtitle: TextView = view.findViewById(R.id.tvScrollItemSubtitle)
        private val tvValue: TextView    = view.findViewById(R.id.tvScrollItemValue)
        private val tvStatus: TextView   = view.findViewById(R.id.tvScrollItemStatus)
        fun bind(item: ScrollItem) {
            tvName.text     = item.name
            tvSubtitle.text = item.subtitle
            tvValue.text    = "%.2f".format(item.value)
            tvStatus.text   = item.status
            tvStatus.setTextColor(
                if (item.status == "ACTIVE") 0xFF00AA00.toInt() else 0xFF888888.toInt()
            )
        }
    }
}
class Scenario2Activity : AppCompatActivity() {
    private lateinit var tvStatusLabel: TextView
    private lateinit var tvScrollCycles: TextView
    private lateinit var tvMeasuredDuration: TextView
    private lateinit var btnStartScroll: Button
    private lateinit var btnStop: Button
    private lateinit var btnBackToMenu: Button
    private lateinit var recyclerView: RecyclerView
    private var status = S2TestStatus.IDLE
    private var scrollCycles = 0
    private var measurementStart = 0L
    private var scrollLoopActive = false
    private var justReset = true
    private var scrollStepPx = 0
    private val mainHandler = Handler(Looper.getMainLooper())
    private var scrollTickRunnable: Runnable? = null
    private var finishRunnable: Runnable? = null
    private val scrollData = generateScrollData()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_scenario2)

        ViewCompat.setOnApplyWindowInsetsListener(findViewById(R.id.main_s2)) { v, insets ->
            val systemBars = insets.getInsets(WindowInsetsCompat.Type.systemBars())
            v.setPadding(systemBars.left, systemBars.top, systemBars.right, systemBars.bottom)
            insets
        }
        scrollStepPx = (SCROLL_STEP_DP * resources.displayMetrics.density).toInt()

        bindViews()
        setupClickListeners()
        refreshUI()
    }
    override fun onDestroy() {
        super.onDestroy()
        clearTimers()
    }
    private fun bindViews() {
        tvStatusLabel      = findViewById(R.id.tvS2StatusLabel)
        tvScrollCycles     = findViewById(R.id.tvS2ScrollCycles)
        tvMeasuredDuration = findViewById(R.id.tvS2MeasuredDuration)
        btnStartScroll     = findViewById(R.id.btnStartScroll)
        btnStop            = findViewById(R.id.btnS2Stop)
        btnBackToMenu      = findViewById(R.id.btnS2BackToMenu)

        recyclerView = findViewById(R.id.recyclerViewScroll)
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = ScrollAdapter(scrollData)
        recyclerView.itemAnimator = null
    }
    private fun setupClickListeners() {
        btnStartScroll.setOnClickListener { startTest() }
        btnStop.setOnClickListener        { stopTest() }
        btnBackToMenu.setOnClickListener  { finish() }
    }
    private fun startTest() {
        if (status == S2TestStatus.RUNNING) return

        scrollCycles = 0
        measurementStart = SystemClock.uptimeMillis()
        justReset = true
        status = S2TestStatus.RUNNING

        (recyclerView.layoutManager as LinearLayoutManager).scrollToPositionWithOffset(0, 0)

        refreshUI()

        scrollLoopActive = true
        val startedAt = SystemClock.uptimeMillis()
        var tick = 1L

        val scrollTick = object : Runnable {
            override fun run() {
                if (!scrollLoopActive) return
                if (!justReset && !recyclerView.canScrollVertically(1)) {
                    scrollCycles++
                    tvScrollCycles.text = s2LabelValue("Scroll Cycles: ", "$scrollCycles")
                    (recyclerView.layoutManager as LinearLayoutManager)
                        .scrollToPositionWithOffset(0, 0)
                    justReset = true
                } else {
                    recyclerView.scrollBy(0, scrollStepPx)
                    justReset = false
                }

                val next = maxOf(0L, startedAt + tick * SCROLL_TICK_MS - SystemClock.uptimeMillis())
                tick++
                scrollTickRunnable = this
                mainHandler.postDelayed(this, next)
            }
        }
        scrollTickRunnable = scrollTick
        mainHandler.postDelayed(scrollTick, SCROLL_TICK_MS)

        finishRunnable = Runnable {
            finishTest(stoppedEarly = false)
        }.also { mainHandler.postDelayed(it, MEASUREMENT_DURATION_S2_MS) }
    }
    private fun stopTest() {
        if (status != S2TestStatus.RUNNING) return
        finishTest(stoppedEarly = true)
    }
    private fun finishTest(stoppedEarly: Boolean) {
        clearTimers()
        status = if (stoppedEarly) S2TestStatus.STOPPED else S2TestStatus.FINISHED
        val duration = if (measurementStart > 0L) SystemClock.uptimeMillis() - measurementStart else 0L
        tvMeasuredDuration.text = s2LabelValue("Measured Duration: ", "$duration ms")
        tvMeasuredDuration.visibility = View.VISIBLE
        refreshUI()
    }
    private fun clearTimers() {
        scrollLoopActive = false
        scrollTickRunnable?.let { mainHandler.removeCallbacks(it) }
        scrollTickRunnable = null
        finishRunnable?.let { mainHandler.removeCallbacks(it) }
        finishRunnable = null
    }
    private fun refreshUI() {
        val isRunning = status == S2TestStatus.RUNNING

        val statusLabel = when (status) {
            S2TestStatus.IDLE     -> "Idle"
            S2TestStatus.RUNNING  -> "Running"
            S2TestStatus.FINISHED -> "Finished"
            S2TestStatus.STOPPED  -> "Stopped"
        }
        tvStatusLabel.text  = s2LabelValue("Status: ", statusLabel)
        tvScrollCycles.text = s2LabelValue("Scroll Cycles: ", "$scrollCycles")

        if (status == S2TestStatus.IDLE) {
            tvMeasuredDuration.visibility = View.GONE
        }

        btnStartScroll.isEnabled = !isRunning
        btnStartScroll.alpha     = if (isRunning) 0.38f else 1.0f
        btnStop.isEnabled        = isRunning
        btnStop.alpha            = if (!isRunning) 0.38f else 1.0f
        btnBackToMenu.isEnabled  = !isRunning
        btnBackToMenu.alpha      = if (isRunning) 0.38f else 1.0f
    }
}

