# Submission Keystore

Use this keystore to sign APKs for grading/submission so your Google Maps API key can be safely restricted by package + SHA-1, and the APK works on any device.

## Generate (Windows PowerShell)

If `keytool` is not on PATH, use the one bundled with Android Studio, e.g.:

```powershell
# Adjust path to your Android Studio installation
& "C:\Program Files\Android\Android Studio\jbr\bin\keytool.exe" `
  -genkeypair -v -storetype PKCS12 -alias submission -keyalg RSA -keysize 2048 -validity 365 `
  -keystore "${PSScriptRoot}\submission.keystore"
```

Or if `keytool` is on PATH:

```powershell
keytool -genkeypair -v -storetype PKCS12 -alias submission -keyalg RSA -keysize 2048 -validity 365 `
  -keystore .\submission.keystore
```

When prompted, set a non-sensitive password you can share for class grading.

## Configure Gradle

Add these properties (global in `%USERPROFILE%\.gradle\gradle.properties` preferred, or `../gradle.properties`):

```properties
SUBMISSION_STORE_FILE=keystore/submission.keystore
SUBMISSION_STORE_PASSWORD=yourStorePass
SUBMISSION_KEY_ALIAS=submission
SUBMISSION_KEY_PASSWORD=yourKeyPass
```

The Android Gradle script automatically uses `signingConfigs.submission` for `release` if the properties are present; otherwise it falls back to debug signing.

## Build and Verify SHA-1

```powershell
cd ..  # android/
./gradlew signingReport
```

Copy the SHA1 for the `submissionRelease` (or `release`) variant.

## Set Google Maps API Restriction

- Restriction type: Android apps
- Package name: com.example.dishdive (or your applicationId)
- SHA-1: value from signingReport above

Now share `app-release.apk` with reviewers—they do not need the keystore.
