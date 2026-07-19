package com.rnbenchmarkapp

import com.facebook.react.bridge.Promise
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.bridge.ReactContextBaseJavaModule
import com.facebook.react.bridge.ReactMethod
import com.facebook.react.bridge.ReadableArray

class CommunicationBenchmarkLegacyModule(reactContext: ReactApplicationContext) :
    ReactContextBaseJavaModule(reactContext) {

    override fun getName(): String = NAME

    @ReactMethod
    fun increment(value: Double, promise: Promise) {
        promise.resolve(value + 1.0)
    }

    @ReactMethod
    fun sumArray(values: ReadableArray, promise: Promise) {
        var sum = 0.0
        for (i in 0 until values.size()) {
            sum += values.getDouble(i)
        }
        promise.resolve(sum)
    }

    companion object {
        const val NAME = "CommunicationBenchmarkLegacy"
    }
}

