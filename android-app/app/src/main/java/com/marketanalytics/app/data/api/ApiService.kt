package com.marketanalytics.app.data.api

import com.marketanalytics.app.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    // ==================== AUTH ====================
    
    @POST("api/auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<AuthResponse>
    
    @POST("api/auth/login")
    suspend fun login(@Body request: LoginRequest): Response<AuthResponse>
    
    // ==================== PRODUCTS ====================
    
    @GET("api/products")
    suspend fun getProducts(): Response<List<Product>>
    
    @POST("api/products")
    suspend fun createProduct(@Body product: ProductCreate): Response<Product>
    
    @GET("api/products/{id}")
    suspend fun getProduct(@Path("id") id: Int): Response<Product>
    
    @DELETE("api/products/{id}")
    suspend fun deleteProduct(@Path("id") id: Int): Response<Map<String, String>>
    
    @POST("api/products/{id}/parse")
    suspend fun parseProduct(@Path("id") id: Int): Response<ParseResult>
    
    @GET("api/products/{id}/reviews")
    suspend fun getReviews(
        @Path("id") productId: Int,
        @Query("limit") limit: Int? = null,
        @Query("offset") offset: Int? = null
    ): Response<List<Review>>
    
    // ==================== ANALYTICS ====================
    
    @POST("api/analytics/products/{id}/analyze")
    suspend fun analyzeProduct(@Path("id") productId: Int): Response<AnalyzeResponse>
    
    @GET("api/analytics/products/{id}")
    suspend fun getAnalytics(
        @Path("id") productId: Int,
        @Query("start_date") startDate: String? = null,
        @Query("end_date") endDate: String? = null
    ): Response<AnalyticsResponse>
    
    @GET("api/analytics/products/{id}/summary")
    suspend fun getSummary(@Path("id") productId: Int): Response<SummaryResponse>
}
