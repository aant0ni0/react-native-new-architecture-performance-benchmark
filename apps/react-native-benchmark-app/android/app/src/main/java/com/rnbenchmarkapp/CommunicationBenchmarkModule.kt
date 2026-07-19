package com.rnbenchmarkapp

import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReadableArray

class CommunicationBenchmarkModule(reactContext: ReactApplicationContext) :
    NativeCommunicationBenchmarkSpec(reactContext) {

    override fun getName(): String = NAME

    override fun increment(value: Double, promise: Promise) {
        promise.resolve(value + 1.0)
    }

    override fun sumArray(values: ReadableArray, promise: Promise) {
        var sum = 0.0
        for (i in 0 until values.size()) {
            sum += values.getDouble(i)
        }
        promise.resolve(sum)
    }

    companion object {
        const val NAME = "CommunicationBenchmark"
    }
}
