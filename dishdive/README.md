# DishDive Flutter Client

This is the Flutter front-end for DishDive. It consumes a Go Fiber API and displays restaurant, dish, favorites and review features. For backend & Python pipeline setup see root `../README.md`.

## Prerequisites

Ensure you have:

- Flutter SDK (stable) – run `flutter doctor` to verify
- Android Studio (for Android) and/or Xcode (for iOS)
- Go backend running locally or access to deployed API

## Install Dependencies

```bash
flutter pub get
```

## Run (Local Backend)

If Go server runs at `localhost:8080`, on Android emulator use:

```bash
flutter run --dart-define=BACKEND_BASE=http://10.0.2.2:8080
```

Physical device (after `adb reverse tcp:8080 tcp:8080`):

```bash
flutter run --dart-define=BACKEND_BASE=http://localhost:8080
```

## Run (Deployed Backend)

```bash
flutter run --dart-define=BACKEND_BASE=http://dishdive.sit.kmutt.ac.th:3000
```

Release builds default to deployed host if not overridden.

## Build Release APK

```bash
flutter build apk --release
adb install -r build/app/outputs/flutter-apk/app-release.apk
```

Override backend during build:

```bash
flutter build apk --release --dart-define=BACKEND_BASE=http://10.0.2.2:8080
```

Note: Overriding is optional; only do this if you specifically want a release build targeting a non-default backend.

### Shrinking / Obfuscation

Shrinking (R8 minify/resource shrink) is currently **disabled** in the release build to avoid missing Play Core classes errors. To re-enable for smaller APKs later:

1. In `android/app/build.gradle.kts` set:
   ```kotlin
   isMinifyEnabled = true
   isShrinkResources = true
   proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
   ```
2. Add dependency if dynamic feature classes are needed:
   ```kotlin
   implementation("com.google.android.play:core:1.10.3")
   ```
3. Add keep rules for Play Core (in `proguard-rules.pro`):
   ```
   -keep class com.google.android.play.core.splitinstall.** { *; }
   -keep class com.google.android.play.core.splitcompat.** { *; }
   -keep class com.google.android.play.core.tasks.** { *; }
   ```
4. Rebuild: `flutter build apk --release` and verify no R8 missing class errors.

## Submission Keystore (Optional for Grading)

Generate a dedicated signing key so the APK works anywhere and you can restrict Google Maps API key by package + SHA‑1.

1. Generate keystore:
   ```bash
   keytool -genkeypair -v -storetype PKCS12 -alias submission -keyalg RSA -keysize 2048 -validity 365 \
     -keystore android/app/keystore/submission.keystore
   ```
2. Add Gradle properties (global or in `android/gradle.properties`):
   ```properties
   SUBMISSION_STORE_FILE=keystore/submission.keystore
   SUBMISSION_STORE_PASSWORD=yourStorePass
   SUBMISSION_KEY_ALIAS=submission
   SUBMISSION_KEY_PASSWORD=yourKeyPass
   # Tip: You can also use an absolute path on Windows, e.g.
   # SUBMISSION_STORE_FILE=C:\\Users\\User\\Desktop\\DishDive\\dishdive\\android\\app\\keystore\\submission.keystore
   ```
3. Build:
   ```bash
   flutter build apk --release
   ```
4. Get SHA‑1:
   ```bash
   cd android
   ./gradlew signingReport
   ```
   Copy SHA1 for `submissionRelease` (or `release`). Use with package name `com.example.dishdive` in Google Cloud Console Android app restriction.
5. Distribute `app-release.apk` – reviewer does not need the keystore.

Rotate / delete this key after submission if not needed further.

## Update Google Maps API Key Restriction

Set restriction type: Android apps

- Package name: `com.example.dishdive`
- SHA‑1: from signingReport (submission keystore)

If you later change the applicationId (package), update both Play config and Maps restriction.

## Troubleshooting

| Problem                                  | Suggestion                                                                 |
| ---------------------------------------- | -------------------------------------------------------------------------- |
| Emulator cannot reach local server       | Use `10.0.2.2` or `adb reverse` on device.                                 |
| Review button missing for favorites dish | Ensure you pulled latest code (DishPage fallback fetch).                   |
| Images not showing                       | Verify MinIO object name matches DB `image_link` extension.                |
| Maps key not working                     | Confirm correct SHA‑1 (gradlew signingReport) not pairing RSA fingerprint. |

## Lint / Analyze

```bash
flutter analyze
```

Non-critical info warnings may appear; fix gradually.

## Tests

Run widget tests:

```bash
flutter test
```

## Next Steps

- Add iOS signing process documentation
- Introduce flavors for dev / submission / prod
- Migrate hard-coded colors into theme definitions
