plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

android {
    namespace = "com.example.dishdive"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = "27.0.12077973"

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_11
        targetCompatibility = JavaVersion.VERSION_11
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_11.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.example.dishdive"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    // --- Signing Configs -----------------------------------------------------------
    // We support an optional "submission" keystore so a reviewer/instructor can
    // install & run the APK without rebuilding with a different signature.
    // Configure by adding the following properties (e.g. in gradle.properties OR
    // better: in your ~/.gradle/gradle.properties for personal keys):
    //   SUBMISSION_STORE_FILE=../submission.keystore
    //   SUBMISSION_STORE_PASSWORD=yourStorePass
    //   SUBMISSION_KEY_ALIAS=submission
    //   SUBMISSION_KEY_PASSWORD=yourKeyPass
    // If these are absent we fall back to debug signing for release to keep flows simple.

    signingConfigs {
        // Only create if properties are present
        val submissionStoreFile = project.findProperty("SUBMISSION_STORE_FILE") as String?
        if (submissionStoreFile != null) {
            // Normalize and support legacy values like "app/keystore/..." by stripping leading "app/"
            val normalizedPath = submissionStoreFile
                .replace('\\', '/')
                .removePrefix("app/")
            create("submission") {
                storeFile = file(normalizedPath)
                storePassword = (project.findProperty("SUBMISSION_STORE_PASSWORD") as String?) ?: ""
                keyAlias = (project.findProperty("SUBMISSION_KEY_ALIAS") as String?) ?: "submission"
                keyPassword = (project.findProperty("SUBMISSION_KEY_PASSWORD") as String?) ?: storePassword
            }
        }
    }

    buildTypes {
        release {
            // Prefer submission keystore if configured; else use debug (development convenience)
            val submission = signingConfigs.findByName("submission")
            signingConfig = submission ?: signingConfigs.getByName("debug")

            // For submission simplicity, disable shrinking/obfuscation to avoid R8 missing class issues.
            // If you need smaller APKs later, enable these and ensure Play Core deps/keep rules are present.
            isMinifyEnabled = false
            isShrinkResources = false
        }
        debug {
            // Unchanged
        }
    }
}

flutter {
    source = "../.."
}
