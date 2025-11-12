# ProGuard rules for DishDive Flutter app
# Keep Flutter embedding and prevent stripping of essential classes
-keep class io.flutter.app.** { *; }
-keep class io.flutter.plugin.** { *; }
-keep class io.flutter.plugins.** { *; }
-keep class io.flutter.embedding.** { *; }

# Keep classes referenced by reflection (common with some libs)
-keep class com.google.android.gms.maps.** { *; }
-keep class com.google.firebase.** { *; }
-keep class androidx.lifecycle.** { *; }

# Allow obfuscation of everything else by default
-dontwarn java.lang.invoke.*
-dontwarn org.jetbrains.annotations.**
