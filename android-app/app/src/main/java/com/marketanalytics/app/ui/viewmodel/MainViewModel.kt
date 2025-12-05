package com.marketanalytics.app.ui.viewmodel

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.marketanalytics.app.data.api.RetrofitClient
import com.marketanalytics.app.data.model.*
import com.marketanalytics.app.data.repository.ProductRepository
import com.marketanalytics.app.data.repository.SettingsRepository
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {
    
    private val repository = ProductRepository()
    private val settingsRepository = SettingsRepository(application.applicationContext)
    
    // Auth State
    private val _isLoggedIn = MutableStateFlow(false)
    val isLoggedIn: StateFlow<Boolean> = _isLoggedIn.asStateFlow()
    
    private val _currentUser = MutableStateFlow<String?>(null)
    val currentUser: StateFlow<String?> = _currentUser.asStateFlow()
    
    private val _authState = MutableStateFlow<ApiResult<AuthResponse>?>(null)
    val authState: StateFlow<ApiResult<AuthResponse>?> = _authState.asStateFlow()
    
    // Products State
    private val _products = MutableStateFlow<ApiResult<List<Product>>?>(null)
    val products: StateFlow<ApiResult<List<Product>>?> = _products.asStateFlow()
    
    private val _selectedProduct = MutableStateFlow<ApiResult<Product>?>(null)
    val selectedProduct: StateFlow<ApiResult<Product>?> = _selectedProduct.asStateFlow()
    
    private val _createProductState = MutableStateFlow<ApiResult<Product>?>(null)
    val createProductState: StateFlow<ApiResult<Product>?> = _createProductState.asStateFlow()
    
    private val _parsingState = MutableStateFlow<ApiResult<ParseResult>?>(null)
    val parsingState: StateFlow<ApiResult<ParseResult>?> = _parsingState.asStateFlow()
    
    private val _reviews = MutableStateFlow<ApiResult<List<Review>>?>(null)
    val reviews: StateFlow<ApiResult<List<Review>>?> = _reviews.asStateFlow()
    
    // Analytics State
    private val _analytics = MutableStateFlow<ApiResult<AnalyticsResponse>?>(null)
    val analytics: StateFlow<ApiResult<AnalyticsResponse>?> = _analytics.asStateFlow()
    
    private val _summary = MutableStateFlow<ApiResult<SummaryResponse>?>(null)
    val summary: StateFlow<ApiResult<SummaryResponse>?> = _summary.asStateFlow()
    
    private val _analyzeState = MutableStateFlow<ApiResult<AnalyzeResponse>?>(null)
    val analyzeState: StateFlow<ApiResult<AnalyzeResponse>?> = _analyzeState.asStateFlow()
    
    // Settings
    private val _apiUrl = MutableStateFlow(SettingsRepository.DEFAULT_API_URL)
    val apiUrl: StateFlow<String> = _apiUrl.asStateFlow()
    
    init {
        viewModelScope.launch {
            // Load saved settings
            settingsRepository.apiUrl.collect { url ->
                _apiUrl.value = url
                RetrofitClient.setBaseUrl(url)
            }
        }
        
        viewModelScope.launch {
            // Check if logged in
            settingsRepository.authToken.collect { token ->
                _isLoggedIn.value = token != null
                if (token != null) {
                    RetrofitClient.setAuthToken(token)
                } else {
                    RetrofitClient.clearAuth()
                }
            }
        }
        
        viewModelScope.launch {
            settingsRepository.username.collect { username ->
                _currentUser.value = username
            }
        }
    }
    
    // ==================== AUTH ====================
    
    fun login(email: String, password: String) {
        viewModelScope.launch {
            _authState.value = ApiResult.Loading
            val result = repository.login(email, password)
            _authState.value = result
            
            if (result is ApiResult.Success) {
                settingsRepository.saveAuthData(
                    token = result.data.accessToken,
                    userId = result.data.userId,
                    username = result.data.username,
                    email = email
                )
                RetrofitClient.setAuthToken(result.data.accessToken)
            }
        }
    }
    
    fun register(email: String, username: String, password: String) {
        viewModelScope.launch {
            _authState.value = ApiResult.Loading
            val result = repository.register(email, username, password)
            _authState.value = result
            
            if (result is ApiResult.Success) {
                settingsRepository.saveAuthData(
                    token = result.data.accessToken,
                    userId = result.data.userId,
                    username = result.data.username,
                    email = email
                )
                RetrofitClient.setAuthToken(result.data.accessToken)
            }
        }
    }
    
    fun logout() {
        viewModelScope.launch {
            settingsRepository.logout()
            RetrofitClient.clearAuth()
            _isLoggedIn.value = false
            _currentUser.value = null
            _products.value = null
            _authState.value = null
        }
    }
    
    fun clearAuthState() {
        _authState.value = null
    }
    
    // ==================== PRODUCTS ====================
    
    fun loadProducts() {
        viewModelScope.launch {
            _products.value = ApiResult.Loading
            _products.value = repository.getProducts()
        }
    }
    
    fun loadProduct(id: Int) {
        viewModelScope.launch {
            _selectedProduct.value = ApiResult.Loading
            _selectedProduct.value = repository.getProduct(id)
        }
    }
    
    fun createProduct(name: String, url: String) {
        viewModelScope.launch {
            _createProductState.value = ApiResult.Loading
            _createProductState.value = repository.createProduct(name, url)
        }
    }
    
    fun clearCreateProductState() {
        _createProductState.value = null
    }
    
    fun deleteProduct(id: Int) {
        viewModelScope.launch {
            val result = repository.deleteProduct(id)
            if (result is ApiResult.Success) {
                loadProducts()
            }
        }
    }
    
    fun parseProduct(id: Int) {
        viewModelScope.launch {
            _parsingState.value = ApiResult.Loading
            _parsingState.value = repository.parseProduct(id)
            
            // Reload product and reviews after parsing
            if (_parsingState.value is ApiResult.Success) {
                loadProduct(id)
                loadReviews(id)
            }
        }
    }
    
    fun clearParsingState() {
        _parsingState.value = null
    }
    
    fun loadReviews(productId: Int, limit: Int? = null, offset: Int? = null) {
        viewModelScope.launch {
            _reviews.value = ApiResult.Loading
            _reviews.value = repository.getReviews(productId, limit, offset)
        }
    }
    
    // ==================== ANALYTICS ====================
    
    fun analyzeProduct(productId: Int) {
        viewModelScope.launch {
            _analyzeState.value = ApiResult.Loading
            _analyzeState.value = repository.analyzeProduct(productId)
            
            // Reload analytics after analysis
            if (_analyzeState.value is ApiResult.Success) {
                loadAnalytics(productId)
                loadReviews(productId)
            }
        }
    }
    
    fun clearAnalyzeState() {
        _analyzeState.value = null
    }
    
    fun loadAnalytics(productId: Int, startDate: String? = null, endDate: String? = null) {
        viewModelScope.launch {
            _analytics.value = ApiResult.Loading
            _analytics.value = repository.getAnalytics(productId, startDate, endDate)
        }
    }
    
    fun loadSummary(productId: Int) {
        viewModelScope.launch {
            // Сбрасываем предыдущий результат и показываем загрузку
            _summary.value = ApiResult.Loading
            // Запрашиваем новую суммаризацию
            _summary.value = repository.getSummary(productId)
        }
    }
    
    fun clearSummary() {
        _summary.value = null
    }
    
    fun clearAnalytics() {
        _analytics.value = null
    }
    
    // ==================== SETTINGS ====================
    
    fun updateApiUrl(url: String) {
        viewModelScope.launch {
            settingsRepository.setApiUrl(url)
            RetrofitClient.setBaseUrl(url)
            _apiUrl.value = url
        }
    }
    
    // Clear states when navigating
    fun clearProductStates() {
        _selectedProduct.value = null
        _reviews.value = null
        _parsingState.value = null
        _analytics.value = null
        _summary.value = null
        _analyzeState.value = null
    }
}
