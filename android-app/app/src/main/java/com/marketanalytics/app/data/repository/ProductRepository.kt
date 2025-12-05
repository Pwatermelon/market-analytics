package com.marketanalytics.app.data.repository

import com.google.gson.Gson
import com.marketanalytics.app.data.api.RetrofitClient
import com.marketanalytics.app.data.model.*
import retrofit2.Response

class ProductRepository {
    
    private val gson = Gson()
    
    private fun <T> handleResponse(response: Response<T>): ApiResult<T> {
        return if (response.isSuccessful) {
            response.body()?.let {
                ApiResult.Success(it)
            } ?: ApiResult.Error("Empty response", response.code())
        } else {
            val errorBody = response.errorBody()?.string()
            val errorMessage = try {
                gson.fromJson(errorBody, ErrorResponse::class.java)?.detail
                    ?: "Error: ${response.code()}"
            } catch (e: Exception) {
                errorBody ?: "Error: ${response.code()}"
            }
            ApiResult.Error(errorMessage, response.code())
        }
    }
    
    // ==================== AUTH ====================
    
    suspend fun login(email: String, password: String): ApiResult<AuthResponse> {
        return try {
            val response = RetrofitClient.getApiService().login(LoginRequest(email, password))
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun register(email: String, username: String, password: String): ApiResult<AuthResponse> {
        return try {
            val response = RetrofitClient.getApiService().register(RegisterRequest(email, username, password))
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    // ==================== PRODUCTS ====================
    
    suspend fun getProducts(): ApiResult<List<Product>> {
        return try {
            val response = RetrofitClient.getApiService().getProducts()
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun getProduct(id: Int): ApiResult<Product> {
        return try {
            val response = RetrofitClient.getApiService().getProduct(id)
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun createProduct(name: String, url: String): ApiResult<Product> {
        return try {
            val response = RetrofitClient.getApiService().createProduct(ProductCreate(name, url))
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun deleteProduct(id: Int): ApiResult<Map<String, String>> {
        return try {
            val response = RetrofitClient.getApiService().deleteProduct(id)
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun parseProduct(id: Int): ApiResult<ParseResult> {
        return try {
            val response = RetrofitClient.getApiService().parseProduct(id)
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun getReviews(productId: Int, limit: Int? = null, offset: Int? = null): ApiResult<List<Review>> {
        return try {
            val response = RetrofitClient.getApiService().getReviews(productId, limit, offset)
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    // ==================== ANALYTICS ====================
    
    suspend fun analyzeProduct(productId: Int): ApiResult<AnalyzeResponse> {
        return try {
            val response = RetrofitClient.getApiService().analyzeProduct(productId)
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun getAnalytics(productId: Int, startDate: String? = null, endDate: String? = null): ApiResult<AnalyticsResponse> {
        return try {
            val response = RetrofitClient.getApiService().getAnalytics(productId, startDate, endDate)
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
    
    suspend fun getSummary(productId: Int): ApiResult<SummaryResponse> {
        return try {
            val response = RetrofitClient.getApiService().getSummary(productId)
            handleResponse(response)
        } catch (e: Exception) {
            ApiResult.Error(e.message ?: "Network error")
        }
    }
}
