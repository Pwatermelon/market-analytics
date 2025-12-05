# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# Keep Retrofit models
-keepattributes Signature
-keepattributes Exceptions
-keepattributes *Annotation*

# Retrofit
-dontwarn retrofit2.**
-keep class retrofit2.** { *; }

# Gson
-keep class com.marketanalytics.app.data.model.** { *; }

# OkHttp
-dontwarn okhttp3.**
-dontwarn okio.**






