package com.marketanalytics.app.ui.screens

import androidx.compose.animation.*
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.marketanalytics.app.data.model.*
import com.marketanalytics.app.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AnalyticsScreen(
    productId: Int,
    productName: String,
    analytics: ApiResult<AnalyticsResponse>?,
    summary: ApiResult<SummaryResponse>?,
    analyzeState: ApiResult<AnalyzeResponse>?,
    onLoadAnalytics: () -> Unit,
    onLoadSummary: () -> Unit,
    onAnalyze: () -> Unit,
    onBack: () -> Unit
) {
    // Load analytics on start
    LaunchedEffect(productId) {
        onLoadAnalytics()
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = "Аналитика",
                            style = MaterialTheme.typography.titleMedium,
                            color = IceWhite
                        )
                        Text(
                            text = productName,
                            style = MaterialTheme.typography.bodySmall,
                            color = IceWhite.copy(alpha = 0.7f),
                            maxLines = 1,
                            overflow = TextOverflow.Ellipsis
                        )
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
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DeepNavy
                )
            )
        },
        containerColor = DeepNavy
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            when (analytics) {
                is ApiResult.Loading -> {
                    Box(
                        modifier = Modifier.fillMaxSize(),
                        contentAlignment = Alignment.Center
                    ) {
                        CircularProgressIndicator(color = ElectricCyan)
                    }
                }
                is ApiResult.Error -> {
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
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
                            text = analytics.message,
                            color = IceWhite,
                            textAlign = TextAlign.Center
                        )
                        Spacer(modifier = Modifier.height(24.dp))
                        
                        // Analyze button if no data
                        Button(
                            onClick = onAnalyze,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = ElectricCyan
                            ),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Icon(Icons.Default.Psychology, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Запустить анализ", color = DeepNavy)
                        }
                    }
                }
                is ApiResult.Success -> {
                    AnalyticsContent(
                        analytics = analytics.data,
                        summary = summary,
                        analyzeState = analyzeState,
                        onLoadSummary = onLoadSummary,
                        onAnalyze = onAnalyze
                    )
                }
                null -> {
                    // Initial state - show analyze button
                    Column(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(24.dp),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Icon(
                            imageVector = Icons.Default.Analytics,
                            contentDescription = null,
                            tint = ElectricCyan.copy(alpha = 0.5f),
                            modifier = Modifier.size(80.dp)
                        )
                        Spacer(modifier = Modifier.height(24.dp))
                        Text(
                            text = "Нет данных аналитики",
                            style = MaterialTheme.typography.titleMedium,
                            color = IceWhite
                        )
                        Text(
                            text = "Сначала запустите анализ отзывов",
                            style = MaterialTheme.typography.bodyMedium,
                            color = IceWhite.copy(alpha = 0.7f)
                        )
                        Spacer(modifier = Modifier.height(24.dp))
                        Button(
                            onClick = onAnalyze,
                            colors = ButtonDefaults.buttonColors(
                                containerColor = ElectricCyan
                            ),
                            shape = RoundedCornerShape(12.dp)
                        ) {
                            Icon(Icons.Default.Psychology, contentDescription = null, tint = DeepNavy)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Запустить анализ", color = DeepNavy, fontWeight = FontWeight.Bold)
                        }
                    }
                }
            }
            
            // Loading overlay for analyze
            if (analyzeState is ApiResult.Loading) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .background(DeepNavy.copy(alpha = 0.8f)),
                    contentAlignment = Alignment.Center
                ) {
                    Card(
                        shape = RoundedCornerShape(20.dp),
                        colors = CardDefaults.cardColors(containerColor = SurfaceCard)
                    ) {
                        Column(
                            modifier = Modifier.padding(32.dp),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            CircularProgressIndicator(color = ElectricCyan)
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "Анализ отзывов...",
                                color = IceWhite,
                                fontWeight = FontWeight.Medium
                            )
                            Text(
                                text = "Это может занять несколько минут",
                                style = MaterialTheme.typography.bodySmall,
                                color = IceWhite.copy(alpha = 0.7f)
                            )
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun AnalyticsContent(
    analytics: AnalyticsResponse,
    summary: ApiResult<SummaryResponse>?,
    analyzeState: ApiResult<AnalyzeResponse>?,
    onLoadSummary: () -> Unit,
    onAnalyze: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(16.dp)
    ) {
        // Stats cards row
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatCard(
                title = "Всего",
                value = analytics.totalReviews.toString(),
                icon = Icons.Default.Comment,
                color = ElectricCyan,
                modifier = Modifier.weight(1f)
            )
            StatCard(
                title = "Позитив",
                value = analytics.positiveCount.toString(),
                icon = Icons.Default.ThumbUp,
                color = MintGreen,
                modifier = Modifier.weight(1f)
            )
        }
        
        Spacer(modifier = Modifier.height(12.dp))
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatCard(
                title = "Негатив",
                value = analytics.negativeCount.toString(),
                icon = Icons.Default.ThumbDown,
                color = CoralRed,
                modifier = Modifier.weight(1f)
            )
            StatCard(
                title = "Нейтрально",
                value = analytics.neutralCount.toString(),
                icon = Icons.Default.Remove,
                color = SunnyYellow,
                modifier = Modifier.weight(1f)
            )
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Sentiment distribution
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = SurfaceCard)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text(
                    text = "Распределение тональности",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.SemiBold,
                    color = IceWhite
                )
                
                Spacer(modifier = Modifier.height(20.dp))
                
                // Sentiment bar
                val total = analytics.totalReviews.toFloat().coerceAtLeast(1f)
                val positivePercent = analytics.positiveCount / total
                val neutralPercent = analytics.neutralCount / total
                val negativePercent = analytics.negativeCount / total
                
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(32.dp)
                        .clip(RoundedCornerShape(16.dp))
                ) {
                    if (positivePercent > 0) {
                        Box(
                            modifier = Modifier
                                .weight(positivePercent.coerceAtLeast(0.01f))
                                .fillMaxHeight()
                                .background(MintGreen)
                        )
                    }
                    if (neutralPercent > 0) {
                        Box(
                            modifier = Modifier
                                .weight(neutralPercent.coerceAtLeast(0.01f))
                                .fillMaxHeight()
                                .background(SunnyYellow)
                        )
                    }
                    if (negativePercent > 0) {
                        Box(
                            modifier = Modifier
                                .weight(negativePercent.coerceAtLeast(0.01f))
                                .fillMaxHeight()
                                .background(CoralRed)
                        )
                    }
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Legend
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceEvenly
                ) {
                    LegendItem(
                        color = MintGreen,
                        label = "Позитив",
                        percent = (positivePercent * 100).toInt()
                    )
                    LegendItem(
                        color = SunnyYellow,
                        label = "Нейтрально",
                        percent = (neutralPercent * 100).toInt()
                    )
                    LegendItem(
                        color = CoralRed,
                        label = "Негатив",
                        percent = (negativePercent * 100).toInt()
                    )
                }
                
                Spacer(modifier = Modifier.height(16.dp))
                
                // Average sentiment
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.Center,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Средняя тональность: ",
                        style = MaterialTheme.typography.bodyMedium,
                        color = IceWhite.copy(alpha = 0.7f)
                    )
                    val sentimentColor = when {
                        analytics.averageSentiment > 0.3 -> MintGreen
                        analytics.averageSentiment < -0.3 -> CoralRed
                        else -> SunnyYellow
                    }
                    Text(
                        text = String.format("%.2f", analytics.averageSentiment),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = sentimentColor
                    )
                }
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Timeline chart
        if (analytics.timeline.isNotEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(containerColor = SurfaceCard)
            ) {
                Column(modifier = Modifier.padding(20.dp)) {
                    Text(
                        text = "Динамика тональности",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = IceWhite
                    )
                    
                    Spacer(modifier = Modifier.height(20.dp))
                    
                    SentimentChart(
                        timeline = analytics.timeline,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(200.dp)
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(24.dp))
        }
        
        // Summary section
        Card(
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = SurfaceCard)
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(
                        text = "Суммаризация отзывов",
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = IceWhite
                    )
                    
                    // Кнопка генерации/перегенерации (недоступна во время загрузки)
                    TextButton(
                        onClick = onLoadSummary,
                        enabled = summary !is ApiResult.Loading,
                        colors = ButtonDefaults.textButtonColors(
                            contentColor = ElectricCyan,
                            disabledContentColor = ElectricCyan.copy(alpha = 0.4f)
                        )
                    ) {
                        Icon(
                            imageVector = if (summary is ApiResult.Success) Icons.Default.Refresh else Icons.Default.AutoAwesome,
                            contentDescription = null,
                            modifier = Modifier.size(18.dp)
                        )
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(if (summary is ApiResult.Success) "Обновить" else "Сгенерировать")
                    }
                }
                
                Spacer(modifier = Modifier.height(12.dp))
                
                when (summary) {
                    is ApiResult.Loading -> {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            CircularProgressIndicator(
                                modifier = Modifier.size(24.dp),
                                color = ElectricCyan,
                                strokeWidth = 2.dp
                            )
                            Spacer(modifier = Modifier.width(12.dp))
                            Text(
                                text = "Генерация суммаризации...",
                                color = IceWhite.copy(alpha = 0.7f),
                                style = MaterialTheme.typography.bodyMedium
                            )
                        }
                    }
                    is ApiResult.Success -> {
                        Text(
                            text = summary.data.summary,
                            style = MaterialTheme.typography.bodyMedium,
                            color = IceWhite.copy(alpha = 0.9f),
                            lineHeight = 24.sp
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "На основе ${summary.data.totalReviews} отзывов",
                            style = MaterialTheme.typography.bodySmall,
                            color = IceWhite.copy(alpha = 0.5f)
                        )
                    }
                    is ApiResult.Error -> {
                        Row(
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Icon(
                                Icons.Default.Warning,
                                contentDescription = null,
                                tint = SunnyYellow,
                                modifier = Modifier.size(20.dp)
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = summary.message,
                                style = MaterialTheme.typography.bodyMedium,
                                color = SunnyYellow
                            )
                        }
                    }
                    null -> {
                        Text(
                            text = "Нажмите \"Сгенерировать\" для создания краткого содержания всех отзывов с помощью AI",
                            style = MaterialTheme.typography.bodyMedium,
                            color = IceWhite.copy(alpha = 0.5f)
                        )
                    }
                }
            }
        }
        
        Spacer(modifier = Modifier.height(24.dp))
        
        // Re-analyze button
        OutlinedButton(
            onClick = onAnalyze,
            modifier = Modifier.fillMaxWidth(),
            shape = RoundedCornerShape(12.dp),
            colors = ButtonDefaults.outlinedButtonColors(
                contentColor = ElectricCyan
            )
        ) {
            Icon(Icons.Default.Refresh, contentDescription = null)
            Spacer(modifier = Modifier.width(8.dp))
            Text("Повторить анализ")
        }
        
        Spacer(modifier = Modifier.height(32.dp))
    }
}

@Composable
private fun StatCard(
    title: String,
    value: String,
    icon: androidx.compose.ui.graphics.vector.ImageVector,
    color: Color,
    modifier: Modifier = Modifier
) {
    Card(
        modifier = modifier,
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(
            containerColor = color.copy(alpha = 0.15f)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxWidth()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Icon(
                imageVector = icon,
                contentDescription = null,
                tint = color,
                modifier = Modifier.size(28.dp)
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = value,
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold,
                color = color
            )
            Text(
                text = title,
                style = MaterialTheme.typography.bodySmall,
                color = IceWhite.copy(alpha = 0.7f)
            )
        }
    }
}

@Composable
private fun LegendItem(color: Color, label: String, percent: Int) {
    Row(
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(
            modifier = Modifier
                .size(12.dp)
                .clip(CircleShape)
                .background(color)
        )
        Spacer(modifier = Modifier.width(6.dp))
        Text(
            text = "$label ($percent%)",
            style = MaterialTheme.typography.bodySmall,
            color = IceWhite.copy(alpha = 0.7f)
        )
    }
}

@Composable
private fun SentimentChart(
    timeline: List<TimelinePoint>,
    modifier: Modifier = Modifier
) {
    if (timeline.isEmpty()) return
    
    // Форматирование дат для отображения
    val formattedDates = remember(timeline) {
        timeline.map { point ->
            try {
                val parts = point.date.split("-")
                if (parts.size >= 3) {
                    "${parts[2]}.${parts[1]}" // DD.MM
                } else {
                    point.date
                }
            } catch (e: Exception) {
                point.date
            }
        }
    }
    
    Column(modifier = modifier) {
        // График
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f)
        ) {
            val width = size.width
            val height = size.height
            val paddingLeft = 10f
            val paddingRight = 10f
            val paddingTop = 20f
            val paddingBottom = 10f
            
            val chartWidth = width - paddingLeft - paddingRight
            val chartHeight = height - paddingTop - paddingBottom
            
            // Find min and max sentiment for scaling
            val minSentiment = timeline.minOfOrNull { it.sentiment } ?: -1f
            val maxSentiment = timeline.maxOfOrNull { it.sentiment } ?: 1f
            val sentimentRange = (maxSentiment - minSentiment).coerceAtLeast(0.1f)
            
            // Draw zero line if in range
            if (minSentiment <= 0 && maxSentiment >= 0) {
                val zeroY = paddingTop + chartHeight * (maxSentiment / sentimentRange)
                drawLine(
                    color = Color.White.copy(alpha = 0.2f),
                    start = Offset(paddingLeft, zeroY),
                    end = Offset(width - paddingRight, zeroY),
                    strokeWidth = 1f
                )
            }
            
            // Create path for the line
            val path = Path()
            val points = mutableListOf<Offset>()
            
            timeline.forEachIndexed { index, point ->
                val x = paddingLeft + (chartWidth * index / (timeline.size - 1).coerceAtLeast(1))
                val normalizedSentiment = (point.sentiment - minSentiment) / sentimentRange
                val y = paddingTop + chartHeight * (1 - normalizedSentiment)
                
                points.add(Offset(x, y))
                
                if (index == 0) {
                    path.moveTo(x, y)
                } else {
                    path.lineTo(x, y)
                }
            }
            
            // Draw gradient fill under the line
            if (points.isNotEmpty()) {
                val fillPath = Path().apply {
                    addPath(path)
                    lineTo(points.last().x, height - paddingBottom)
                    lineTo(paddingLeft, height - paddingBottom)
                    close()
                }
                
                drawPath(
                    path = fillPath,
                    brush = Brush.verticalGradient(
                        colors = listOf(
                            ElectricCyan.copy(alpha = 0.3f),
                            ElectricCyan.copy(alpha = 0.0f)
                        )
                    )
                )
            }
            
            // Draw the line
            drawPath(
                path = path,
                color = ElectricCyan,
                style = Stroke(width = 3f, cap = StrokeCap.Round)
            )
            
            // Draw points
            points.forEach { point ->
                drawCircle(
                    color = ElectricCyan,
                    radius = 6f,
                    center = point
                )
                drawCircle(
                    color = DeepNavy,
                    radius = 3f,
                    center = point
                )
            }
        }
        
        // Ось X с датами
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 4.dp),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            // Показываем максимум 5-7 дат для читаемости
            val step = when {
                formattedDates.size <= 5 -> 1
                formattedDates.size <= 10 -> 2
                formattedDates.size <= 20 -> 4
                else -> formattedDates.size / 5
            }
            
            formattedDates.forEachIndexed { index, date ->
                if (index == 0 || index == formattedDates.lastIndex || index % step == 0) {
                    Text(
                        text = date,
                        style = MaterialTheme.typography.labelSmall,
                        color = IceWhite.copy(alpha = 0.5f),
                        fontSize = 10.sp
                    )
                }
            }
        }
    }
}

