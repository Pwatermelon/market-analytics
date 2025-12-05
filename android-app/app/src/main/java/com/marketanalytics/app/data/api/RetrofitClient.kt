package com.marketanalytics.app.data.api

import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {
    private var baseUrl: String = "http://10.0.2.2:8000/" // Default for emulator (api-gateway)
    private var authToken: String? = null
    private var retrofit: Retrofit? = null
    private var apiService: ApiService? = null
    
    fun setBaseUrl(url: String) {
        val formattedUrl = if (url.endsWith("/")) url else "$url/"
        if (baseUrl != formattedUrl) {
            baseUrl = formattedUrl
            retrofit = null
            apiService = null
        }
    }
    
    fun setAuthToken(token: String?) {
        if (authToken != token) {
            authToken = token
            retrofit = null
            apiService = null
        }
    }
    
    fun getAuthToken(): String? = authToken
    
    fun clearAuth() {
        authToken = null
        retrofit = null
        apiService = null
    }
    
    private fun createOkHttpClient(): OkHttpClient {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BODY
        }
        
        val authInterceptor = Interceptor { chain ->
            val originalRequest = chain.request()
            val requestBuilder = originalRequest.newBuilder()
            
            // Добавляем JWT токен если есть
            authToken?.let { token ->
                requestBuilder.addHeader("Authorization", "Bearer $token")
            }
            
            requestBuilder
                .addHeader("Content-Type", "application/json")
                .addHeader("Accept", "application/json")
            
            chain.proceed(requestBuilder.build())
        }
        
        return OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(loggingInterceptor)
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build()
    }
    
    private fun getRetrofit(): Retrofit {
        if (retrofit == null) {
            retrofit = Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(createOkHttpClient())
                .addConverterFactory(GsonConverterFactory.create())
                .build()
        }
        return retrofit!!
    }
    
    fun getApiService(): ApiService {
        if (apiService == null) {
            apiService = getRetrofit().create(ApiService::class.java)
        }
        return apiService!!
    }
}
