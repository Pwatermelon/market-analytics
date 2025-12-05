package com.marketanalytics.app.ui.navigation

import androidx.compose.runtime.*
import androidx.navigation.NavType
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import androidx.navigation.navArgument
import com.marketanalytics.app.ui.screens.*
import com.marketanalytics.app.ui.viewmodel.MainViewModel

sealed class Screen(val route: String) {
    object Auth : Screen("auth")
    object Products : Screen("products")
    object ProductDetail : Screen("product/{productId}") {
        fun createRoute(productId: Int) = "product/$productId"
    }
    object AddProduct : Screen("add_product")
    object Analytics : Screen("analytics/{productId}/{productName}") {
        fun createRoute(productId: Int, productName: String) = 
            "analytics/$productId/${java.net.URLEncoder.encode(productName, "UTF-8")}"
    }
    object Settings : Screen("settings")
}

@Composable
fun AppNavigation(viewModel: MainViewModel) {
    val navController = rememberNavController()
    
    val isLoggedIn by viewModel.isLoggedIn.collectAsState()
    val currentUser by viewModel.currentUser.collectAsState()
    val authState by viewModel.authState.collectAsState()
    val products by viewModel.products.collectAsState()
    val selectedProduct by viewModel.selectedProduct.collectAsState()
    val createProductState by viewModel.createProductState.collectAsState()
    val parsingState by viewModel.parsingState.collectAsState()
    val reviews by viewModel.reviews.collectAsState()
    val analytics by viewModel.analytics.collectAsState()
    val summary by viewModel.summary.collectAsState()
    val analyzeState by viewModel.analyzeState.collectAsState()
    val apiUrl by viewModel.apiUrl.collectAsState()
    
    // Navigate based on auth state
    LaunchedEffect(isLoggedIn) {
        if (isLoggedIn) {
            if (navController.currentDestination?.route == Screen.Auth.route) {
                navController.navigate(Screen.Products.route) {
                    popUpTo(Screen.Auth.route) { inclusive = true }
                }
            }
        } else {
            navController.navigate(Screen.Auth.route) {
                popUpTo(0) { inclusive = true }
            }
        }
    }
    
    NavHost(
        navController = navController,
        startDestination = if (isLoggedIn) Screen.Products.route else Screen.Auth.route
    ) {
        // Auth screen
        composable(Screen.Auth.route) {
            AuthScreen(
                authState = authState,
                onLogin = { email, password ->
                    viewModel.login(email, password)
                },
                onRegister = { email, username, password ->
                    viewModel.register(email, username, password)
                },
                onClearAuthState = {
                    viewModel.clearAuthState()
                },
                onNavigateToSettings = {
                    navController.navigate(Screen.Settings.route)
                }
            )
        }
        
        // Products list
        composable(Screen.Products.route) {
            ProductsScreen(
                products = products,
                currentUser = currentUser,
                onLoadProducts = { viewModel.loadProducts() },
                onProductClick = { productId ->
                    viewModel.clearProductStates()
                    navController.navigate(Screen.ProductDetail.createRoute(productId))
                },
                onAddProduct = {
                    navController.navigate(Screen.AddProduct.route)
                },
                onSettings = {
                    navController.navigate(Screen.Settings.route)
                },
                onLogout = {
                    viewModel.logout()
                }
            )
        }
        
        // Product detail
        composable(
            route = Screen.ProductDetail.route,
            arguments = listOf(navArgument("productId") { type = NavType.IntType })
        ) { backStackEntry ->
            val productId = backStackEntry.arguments?.getInt("productId") ?: return@composable
            
            ProductDetailScreen(
                productId = productId,
                product = selectedProduct,
                reviews = reviews,
                parsingState = parsingState,
                onLoadProduct = { viewModel.loadProduct(productId) },
                onLoadReviews = { viewModel.loadReviews(productId) },
                onParse = { viewModel.parseProduct(productId) },
                onNavigateToAnalytics = {
                    val productName = (selectedProduct as? com.marketanalytics.app.data.model.ApiResult.Success)
                        ?.data?.name ?: "Товар"
                    navController.navigate(Screen.Analytics.createRoute(productId, productName))
                },
                onDelete = {
                    viewModel.deleteProduct(productId)
                    navController.popBackStack()
                },
                onBack = {
                    viewModel.clearProductStates()
                    navController.popBackStack()
                }
            )
        }
        
        // Add product
        composable(Screen.AddProduct.route) {
            AddProductScreen(
                createState = createProductState,
                onCreateProduct = { name, url ->
                    viewModel.createProduct(name, url)
                },
                onClearState = {
                    viewModel.clearCreateProductState()
                },
                onBack = {
                    navController.popBackStack()
                },
                onSuccess = {
                    viewModel.loadProducts()
                    navController.popBackStack()
                }
            )
        }
        
        // Analytics
        composable(
            route = Screen.Analytics.route,
            arguments = listOf(
                navArgument("productId") { type = NavType.IntType },
                navArgument("productName") { type = NavType.StringType }
            )
        ) { backStackEntry ->
            val productId = backStackEntry.arguments?.getInt("productId") ?: return@composable
            val productName = java.net.URLDecoder.decode(
                backStackEntry.arguments?.getString("productName") ?: "Товар",
                "UTF-8"
            )
            
            AnalyticsScreen(
                productId = productId,
                productName = productName,
                analytics = analytics,
                summary = summary,
                analyzeState = analyzeState,
                onLoadAnalytics = { viewModel.loadAnalytics(productId) },
                onLoadSummary = { viewModel.loadSummary(productId) },
                onAnalyze = { viewModel.analyzeProduct(productId) },
                onBack = {
                    viewModel.clearAnalytics()
                    viewModel.clearSummary()
                    viewModel.clearAnalyzeState()
                    navController.popBackStack()
                }
            )
        }
        
        // Settings
        composable(Screen.Settings.route) {
            SettingsScreen(
                apiUrl = apiUrl,
                isLoggedIn = isLoggedIn,
                currentUser = currentUser,
                onUpdateApiUrl = { url ->
                    viewModel.updateApiUrl(url)
                },
                onLogout = {
                    viewModel.logout()
                    navController.navigate(Screen.Auth.route) {
                        popUpTo(0) { inclusive = true }
                    }
                },
                onBack = {
                    navController.popBackStack()
                }
            )
        }
    }
}
