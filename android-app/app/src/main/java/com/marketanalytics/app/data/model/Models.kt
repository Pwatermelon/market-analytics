package com.marketanalytics.app.data.model

import com.google.gson.annotations.SerializedName

// ==================== AUTH ====================

data class LoginRequest(
    val email: String,
    val password: String
)

data class RegisterRequest(
    val email: String,
    val username: String,
    val password: String
)

data class AuthResponse(
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("token_type")
    val tokenType: String,
    @SerializedName("user_id")
    val userId: Int,
    val username: String
)

data class UserInfo(
    @SerializedName("user_id")
    val userId: Int,
    val email: String
)

// ==================== PRODUCTS ====================

data class Product(
    val id: Int,
    @SerializedName("user_id")
    val userId: Int,
    val name: String,
    val url: String,
    val marketplace: String,
    @SerializedName("parsing_status")
    val parsingStatus: String,
    @SerializedName("last_parsed_at")
    val lastParsedAt: String?,
    @SerializedName("review_count")
    val reviewCount: Int,
    @SerializedName("created_at")
    val createdAt: String,
    @SerializedName("updated_at")
    val updatedAt: String
)

data class ProductCreate(
    val name: String,
    val url: String
)

data class Review(
    val id: Int,
    @SerializedName("product_id")
    val productId: Int,
    val author: String?,
    val rating: Int?,
    val text: String,
    val date: String,
    val sentiment: Float?,
    @SerializedName("sentiment_label")
    val sentimentLabel: String?,
    val summary: String?
)

data class ParseResult(
    val message: String,
    @SerializedName("parsed_count")
    val parsedCount: Int,
    @SerializedName("new_reviews")
    val newReviews: Int
)

// ==================== ANALYTICS ====================

data class AnalyticsResponse(
    @SerializedName("product_id")
    val productId: Int,
    @SerializedName("total_reviews")
    val totalReviews: Int,
    @SerializedName("positive_count")
    val positiveCount: Int,
    @SerializedName("negative_count")
    val negativeCount: Int,
    @SerializedName("neutral_count")
    val neutralCount: Int,
    @SerializedName("average_sentiment")
    val averageSentiment: Float,
    val timeline: List<TimelinePoint>
)

data class TimelinePoint(
    val date: String,
    val sentiment: Float,
    val count: Int
)

data class SummaryResponse(
    @SerializedName("product_id")
    val productId: Int,
    val summary: String,
    @SerializedName("total_reviews")
    val totalReviews: Int
)

data class AnalyzeResponse(
    val message: String,
    @SerializedName("analyzed_count")
    val analyzedCount: Int
)

// ==================== API RESULT ====================

sealed class ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>()
    data class Error(val message: String, val code: Int? = null) : ApiResult<Nothing>()
    object Loading : ApiResult<Nothing>()
}

// ==================== ERROR RESPONSE ====================

data class ErrorResponse(
    val detail: String?
)
