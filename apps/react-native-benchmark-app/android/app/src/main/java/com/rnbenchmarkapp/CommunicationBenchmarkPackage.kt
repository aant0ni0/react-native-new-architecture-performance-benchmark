package com.rnbenchmarkapp

import com.facebook.react.TurboReactPackage
import com.facebook.react.bridge.NativeModule
import com.facebook.react.bridge.ReactApplicationContext
import com.facebook.react.module.model.ReactModuleInfo
import com.facebook.react.module.model.ReactModuleInfoProvider

class CommunicationBenchmarkPackage : TurboReactPackage() {

    override fun getModule(name: String, context: ReactApplicationContext): NativeModule? =
        if (name == CommunicationBenchmarkModule.NAME) CommunicationBenchmarkModule(context)
        else null

    override fun getReactModuleInfoProvider() = ReactModuleInfoProvider {
        mapOf(
            CommunicationBenchmarkModule.NAME to ReactModuleInfo(
                CommunicationBenchmarkModule.NAME,
                CommunicationBenchmarkModule.NAME,
                false,
                false,
                false,
                BuildConfig.IS_NEW_ARCHITECTURE_ENABLED,
            )
        )
    }
}

