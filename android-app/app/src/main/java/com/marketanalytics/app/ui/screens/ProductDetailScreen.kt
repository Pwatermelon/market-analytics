package com.marketanalytics.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.marketanalytics.app.data.model.*
import com.marketanalytics.app.ui.theme.*
import java.text.SimpleDateFormat
import java.util.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ProductDetailScreen(
    productId: Int,
    product: ApiResult<Product>?,
    reviews: ApiResult<List<Review>>?,
    parsingState: ApiResult<ParseResult>?,
    onLoadProduct: () -> Unit,
    onLoadReviews: () -> Unit,
    onParse: () -> Unit,
    onNavigateToAnalytics: () -> Unit,
    onDelete: () -> Unit,
    onBack: () -> Unit
) {
    var showDeleteDialog by remember { mutableStateOf(false) }
    
    // Load data on start
    LaunchedEffect(productId) {
        onLoadProduct()
        onLoadReviews()
    }
    
    // Delete confirmation dialog
    if (showDeleteDialog) {
        AlertDialog(
            onDismissRequest = { showDeleteDialog = false },
            title = { Text("Удалить товар?", color = IceWhite) },
            text = { 
                Text(
                    "Товар и все его отзывы будут удалены. Это действие нельзя отменить.", 
                    color = IceWhite.copy(alpha = 0.7f)
                ) 
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        showDeleteDialog = false
                        onDelete()
                    },
                    colors = ButtonDefaults.textButtonColors(contentColor = CoralRed)
                ) {
                    Text("Удалить")
                }
            },
            dismissButton = {
                TextButton(
                    onClick = { showDeleteDialog = false },
                    colors = ButtonDefaults.textButtonColors(contentColor = IceWhite)
                ) {
                    Text("Отмена")
                }
            },
            containerColor = SurfaceCard,
            shape = RoundedCornerShape(20.dp)
        )
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    when (product) {
                        is ApiResult.Success -> {
                            Column {
                                Text(
                                    text = product.data.name,
                                    style = MaterialTheme.typography.titleMedium,
                                    maxLines = 1,
                                    overflow = TextOverflow.Ellipsis,
                                    color = IceWhite
                                )
                                Row(
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    MarketplaceChip(marketplace = product.data.marketplace)
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        text = "${product.data.reviewCount} отзывов",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = IceWhite.copy(alpha = 0.6f)
                                    )
                                }
                            }
                        }
                        else -> {
                            Text("Загрузка...", color = IceWhite)
                        }
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(
                            imageVector = Icons.Default.ArrowBack,
                            contentDescription = "Назад",
                            tint = IceWhite
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { showDeleteDialog = true }) {
                        Icon(
                            imageVector = Icons.Default.Delete,
                            contentDescription = "Удалить",
                            tint = CoralRed.copy(alpha = 0.8f)
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DeepNavy
                )
            )
        },
        containerColor = DeepNavy
    ) { padding ->
        when (product) {
            is ApiResult.Loading -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = ElectricCyan)
                }
            }
            is ApiResult.Error -> {
                Column(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding)
                        .padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    Icon(
                        imageVector = Icons.Default.Error,
                        contentDescription = null,
                        tint = CoralRed,
                        modifier = Modifier.size(64.dp)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        text = product.message,
                        color = IceWhite
                    )
                    Spacer(modifier = Modifier.height(24.dp))
                    Button(
                        onClick = onLoadProduct,
                        colors = ButtonDefaults.buttonColors(containerColor = ElectricCyan)
                    ) {
                        Text("Повторить", color = DeepNavy)
                    }
                }
            }
            is ApiResult.Success -> {
                ProductDetailContent(
                    product = product.data,
                    reviews = reviews,
                    parsingState = parsingState,
                    onParse = onParse,
                    onNavigateToAnalytics = onNavigateToAnalytics,
                    modifier = Modifier.padding(padding)
                )
            }
            null -> {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(padding),
                    contentAlignment = Alignment.Center
                ) {
                    CircularProgressIndicator(color = ElectricCyan)
                }
            }
        }
    }
}

@Composable
private fun ProductDetailContent(
    product: Product,
    reviews: ApiResult<List<Review>>?,
    parsingState: ApiResult<ParseResult>?,
    onParse: () -> Unit,
    onNavigateToAnalytics: () -> Unit,
    modifier: Modifier = Modifier
) {
    LazyColumn(
        modifier = modifier.fillMaxSize(),
        contentPadding = PaddingValues(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Action buttons
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                // Parse button
                Button(
                    onClick = onParse,
                    modifier = Modifier.weight(1f),
                    enabled = product.parsingStatus != "parsing" && parsingState !is ApiResult.Loading,
                    colors = ButtonDefaults.buttonColors(
                        containerColor = ElectricCyan,
                        disabledContainerColor = ElectricCyan.copy(alpha = 0.3f)
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    if (parsingState is ApiResult.Loading || product.parsingStatus == "parsing") {
                        CircularProgressIndicator(
                            modifier = Modifier.size(20.dp),
                            color = DeepNavy,
                            strokeWidth = 2.dp
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Парсинг...", color = DeepNavy)
                    } else {
                        Icon(
                            Icons.Default.Download,
                            contentDescription = null,
                            tint = DeepNavy,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Парсить отзывы", color = DeepNavy, fontWeight = FontWeight.Bold)
                    }
                }
                
                // Analytics button
                Button(
                    onClick = onNavigateToAnalytics,
                    modifier = Modifier.weight(1f),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = NeonPurple
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Icon(
                        Icons.Default.Analytics,
                        contentDescription = null,
                        tint = IceWhite,
                        modifier = Modifier.size(20.dp)
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Аналитика", color = IceWhite, fontWeight = FontWeight.Bold)
                }
            }
        }
        
        // Parsing result
        when (val parsing = parsingState) {
            is ApiResult.Loading -> {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(containerColor = SurfaceCard)
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(20.dp),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            CircularProgressIndicator(
                                color = ElectricCyan,
                                modifier = Modifier.size(24.dp),
                                strokeWidth = 2.dp
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = "Парсинг отзывов...",
                                color = IceWhite
                            )
                        }
                    }
                }
            }
            is ApiResult.Success -> {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = MintGreen.copy(alpha = 0.15f)
                        )
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.CheckCircle,
                                contentDescription = null,
                                tint = MintGreen
                            )
                            Column {
                                Text(
                                    text = parsing.data.message,
                                    style = MaterialTheme.typography.bodyMedium,
                                    fontWeight = FontWeight.Medium,
                                    color = MintGreen
                                )
                                Text(
                                    text = "Новых: ${parsing.data.newReviews} | Всего: ${parsing.data.parsedCount}",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MintGreen.copy(alpha = 0.8f)
                                )
                            }
                        }
                    }
                }
            }
            is ApiResult.Error -> {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        shape = RoundedCornerShape(16.dp),
                        colors = CardDefaults.cardColors(
                            containerColor = CoralRed.copy(alpha = 0.15f)
                        )
                    ) {
                        Row(
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(16.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                imageVector = Icons.Default.Error,
                                contentDescription = null,
                                tint = CoralRed
                            )
                            Text(
                                text = parsing.message,
                                style = MaterialTheme.typography.bodyMedium,
                                color = CoralRed
                            )
                        }
                    }
                }
            }
            null -> { /* No parsing state */ }
        }
        
        // Reviews header
        item {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "Отзывы",
                    style = MaterialTheme.typography.titleLarge,
                    fontWeight = FontWeight.Bold,
                    color = IceWhite
                )
                Text(
                    text = "${product.reviewCount}",
                    style = MaterialTheme.typography.titleMedium,
                    color = ElectricCyan,
                    fontWeight = FontWeight.Bold
                )
            }
        }
        
        // Reviews list
        when (reviews) {
            is ApiResult.Loading -> {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(32.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(color = ElectricCyan)
                    }
                }
            }
            is ApiResult.Error -> {
                item {
                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = CoralRed.copy(alpha = 0.1f)
                        ),
                        shape = RoundedCornerShape(12.dp)
                    ) {
                        Text(
                            text = reviews.message,
                            modifier = Modifier.padding(16.dp),
                            color = CoralRed
                        )
                    }
                }
            }
            is ApiResult.Success -> {
                if (reviews.data.isEmpty()) {
                    item {
                        Card(
                            modifier = Modifier.fillMaxWidth(),
                            colors = CardDefaults.cardColors(containerColor = SurfaceCard),
                            shape = RoundedCornerShape(16.dp)
                        ) {
                            Column(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(32.dp),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Icon(
                                    imageVector = Icons.Default.Comment,
                                    contentDescription = null,
                                    tint = IceWhite.copy(alpha = 0.3f),
                                    modifier = Modifier.size(48.dp)
                                )
                                Spacer(modifier = Modifier.height(12.dp))
                                Text(
                                    text = "Отзывов пока нет",
                                    style = MaterialTheme.typography.bodyLarge,
                                    color = IceWhite.copy(alpha = 0.5f)
                                )
                                Text(
                                    text = "Нажмите \"Парсить отзывы\" для загрузки",
                                    style = MaterialTheme.typography.bodySmall,
                                    color = IceWhite.copy(alpha = 0.3f)
                                )
                            }
                        }
                    }
                } else {
                    items(reviews.data) { review ->
                        ReviewCard(review = review)
                    }
                }
            }
            null -> {
                item {
                    Box(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(32.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(color = ElectricCyan)
                    }
                }
            }
        }
        
        // Bottom spacer
        item {
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
private fun ReviewCard(review: Review) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = SurfaceCard)
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp)
        ) {
            // Header: Author, Rating, Date
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // Avatar
                    Box(
                        modifier = Modifier
                            .size(36.dp)
                            .clip(CircleShape)
                            .background(
                                Brush.linearGradient(
                                    colors = listOf(ElectricCyan, NeonPurple)
                                )
                            ),
                        contentAlignment = Alignment.Center
                    ) {
                        Text(
                            text = (review.author?.firstOrNull() ?: '?').uppercase(),
                            color = IceWhite,
                            fontWeight = FontWeight.Bold
                        )
                    }
                    
                    Column {
                        Text(
                            text = review.author ?: "Аноним",
                            style = MaterialTheme.typography.bodyMedium,
                            fontWeight = FontWeight.Medium,
                            color = IceWhite
                        )
                        Text(
                            text = formatDate(review.date),
                            style = MaterialTheme.typography.bodySmall,
                            color = IceWhite.copy(alpha = 0.5f)
                        )
                    }
                }
                
                // Rating
                review.rating?.let { rating ->
                    Row(
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(2.dp)
                    ) {
                        repeat(5) { index ->
                            Icon(
                                imageVector = if (index < rating) Icons.Default.Star else Icons.Default.StarBorder,
                                contentDescription = null,
                                tint = if (index < rating) SunnyYellow else IceWhite.copy(alpha = 0.3f),
                                modifier = Modifier.size(16.dp)
                            )
                        }
                    }
                }
            }
            
            Spacer(modifier = Modifier.height(12.dp))
            
            // Review text
            Text(
                text = review.text,
                style = MaterialTheme.typography.bodyMedium,
                color = IceWhite.copy(alpha = 0.9f),
                lineHeight = 22.sp
            )
            
            // Sentiment badge if analyzed
            review.sentimentLabel?.let { label ->
                Spacer(modifier = Modifier.height(12.dp))
                SentimentBadge(
                    label = label,
                    sentiment = review.sentiment
                )
            }
        }
    }
}

@Composable
private fun SentimentBadge(label: String, sentiment: Float?) {
    val (color, text, icon) = when (label) {
        "positive" -> Triple(MintGreen, "Позитивный", Icons.Default.SentimentSatisfied)
        "negative" -> Triple(CoralRed, "Негативный", Icons.Default.SentimentDissatisfied)
        else -> Triple(SunnyYellow, "Нейтральный", Icons.Default.SentimentNeutral)
    }
    
    Row(
        modifier = Modifier
            .background(color.copy(alpha = 0.15f), RoundedCornerShape(20.dp))
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Icon(
            imageVector = icon,
            contentDescription = null,
            tint = color,
            modifier = Modifier.size(16.dp)
        )
        Text(
            text = text,
            style = MaterialTheme.typography.labelSmall,
            color = color,
            fontWeight = FontWeight.Medium
        )
        sentiment?.let {
            Text(
                text = String.format("%.2f", it),
                style = MaterialTheme.typography.labelSmall,
                color = color.copy(alpha = 0.7f)
            )
        }
    }
}

@Composable
private fun MarketplaceChip(marketplace: String) {
    val color = when (marketplace.lowercase()) {
        "wildberries" -> NeonPurple
        "ozon" -> ElectricCyan
        "yandex_market" -> SunnyYellow
        else -> IceWhite.copy(alpha = 0.5f)
    }
    
    Text(
        text = marketplace.replaceFirstChar { it.uppercase() },
        style = MaterialTheme.typography.labelSmall,
        color = color,
        fontWeight = FontWeight.Medium
    )
}

private fun formatDate(dateString: String): String {
    return try {
        val inputFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.getDefault())
        val outputFormat = SimpleDateFormat("dd MMM yyyy", Locale("ru"))
        val date = inputFormat.parse(dateString)
        date?.let { outputFormat.format(it) } ?: dateString
    } catch (e: Exception) {
        try {
            val inputFormat = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault())
            val outputFormat = SimpleDateFormat("dd MMM yyyy", Locale("ru"))
            val date = inputFormat.parse(dateString)
            date?.let { outputFormat.format(it) } ?: dateString
        } catch (e: Exception) {
            dateString
        }
    }
}
