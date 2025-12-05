package com.marketanalytics.app.ui.theme

import android.app.Activity
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = ElectricCyan,
    onPrimary = DeepNavy,
    primaryContainer = DarkSlate,
    onPrimaryContainer = ElectricCyan,
    
    secondary = NeonPurple,
    onSecondary = Color.White,
    secondaryContainer = SurfaceCard,
    onSecondaryContainer = NeonPurple,
    
    tertiary = MintGreen,
    onTertiary = DeepNavy,
    tertiaryContainer = SurfaceElevated,
    onTertiaryContainer = MintGreen,
    
    error = CoralRed,
    onError = Color.White,
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    
    background = DeepNavy,
    onBackground = IceWhite,
    
    surface = SurfaceDark,
    onSurface = IceWhite,
    surfaceVariant = SurfaceCard,
    onSurfaceVariant = SteelBlue,
    
    outline = SlateBlue,
    outlineVariant = DarkSlate,
    
    inverseSurface = IceWhite,
    inverseOnSurface = DeepNavy,
    inversePrimary = GradientStart
)

private val LightColorScheme = lightColorScheme(
    primary = GradientStart,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFE8EAFF),
    onPrimaryContainer = GradientStart,
    
    secondary = NeonPurple,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFF3E5F5),
    onSecondaryContainer = NeonPurple,
    
    tertiary = MintGreen,
    onTertiary = Color.White,
    tertiaryContainer = Color(0xFFE8F5E9),
    onTertiaryContainer = Color(0xFF00C853),
    
    error = CoralRed,
    onError = Color.White,
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF93000A),
    
    background = Color(0xFFF8F9FA),
    onBackground = DeepNavy,
    
    surface = Color.White,
    onSurface = DeepNavy,
    surfaceVariant = Color(0xFFF1F3F4),
    onSurfaceVariant = SlateBlue,
    
    outline = SteelBlue,
    outlineVariant = Color(0xFFE0E0E0),
    
    inverseSurface = DeepNavy,
    inverseOnSurface = IceWhite,
    inversePrimary = ElectricCyan
)

@Composable
fun MarketAnalyticsTheme(
    darkTheme: Boolean = true, // По умолчанию темная тема
    content: @Composable () -> Unit
) {
    val colorScheme = if (darkTheme) DarkColorScheme else LightColorScheme
    
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            window.navigationBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
            WindowCompat.getInsetsController(window, view).isAppearanceLightNavigationBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}






