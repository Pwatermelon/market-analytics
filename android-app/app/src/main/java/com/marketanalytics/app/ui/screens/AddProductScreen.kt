package com.marketanalytics.app.ui.screens

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusDirection
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import com.marketanalytics.app.data.model.ApiResult
import com.marketanalytics.app.data.model.Product
import com.marketanalytics.app.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AddProductScreen(
    createState: ApiResult<Product>?,
    onCreateProduct: (name: String, url: String) -> Unit,
    onClearState: () -> Unit,
    onBack: () -> Unit,
    onSuccess: () -> Unit
) {
    var name by remember { mutableStateOf("") }
    var url by remember { mutableStateOf("") }
    var showError by remember { mutableStateOf(false) }
    var errorMessage by remember { mutableStateOf("") }
    
    val focusManager = LocalFocusManager.current
    val isLoading = createState is ApiResult.Loading
    
    // Handle result
    LaunchedEffect(createState) {
        when (createState) {
            is ApiResult.Success -> {
                onClearState()
                onSuccess()
            }
            is ApiResult.Error -> {
                errorMessage = createState.message
                showError = true
            }
            else -> {
                showError = false
            }
        }
    }
    
    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "Добавить товар",
                        color = IceWhite,
                        fontWeight = FontWeight.Bold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = {
                        onClearState()
                        onBack()
                    }) {
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
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            verticalArrangement = Arrangement.spacedBy(24.dp)
        ) {
            // Info card
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(
                    containerColor = ElectricCyan.copy(alpha = 0.1f)
                ),
                shape = RoundedCornerShape(16.dp)
            ) {
                Row(
                    modifier = Modifier.padding(16.dp),
                    verticalAlignment = Alignment.Top
                ) {
                    Icon(
                        imageVector = Icons.Default.Info,
                        contentDescription = null,
                        tint = ElectricCyan,
                        modifier = Modifier.size(24.dp)
                    )
                    Spacer(modifier = Modifier.width(12.dp))
                    Column {
                        Text(
                            text = "Поддерживаемые маркетплейсы",
                            style = MaterialTheme.typography.titleSmall,
                            fontWeight = FontWeight.SemiBold,
                            color = ElectricCyan
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = "• Wildberries\n• Ozon\n• Яндекс Маркет",
                            style = MaterialTheme.typography.bodySmall,
                            color = IceWhite.copy(alpha = 0.7f)
                        )
                    }
                }
            }
            
            // Error card
            if (showError) {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = CoralRed.copy(alpha = 0.15f)
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Row(
                        modifier = Modifier.padding(16.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = Icons.Default.Error,
                            contentDescription = null,
                            tint = CoralRed
                        )
                        Spacer(modifier = Modifier.width(12.dp))
                        Text(
                            text = errorMessage,
                            color = CoralRed,
                            style = MaterialTheme.typography.bodyMedium
                        )
                    }
                }
            }
            
            // Name field
            OutlinedTextField(
                value = name,
                onValueChange = { name = it },
                label = { Text("Название товара") },
                placeholder = { Text("Например: iPhone 15 Pro Max") },
                leadingIcon = {
                    Icon(
                        Icons.Default.ShoppingBag,
                        contentDescription = null,
                        tint = ElectricCyan
                    )
                },
                modifier = Modifier.fillMaxWidth(),
                singleLine = true,
                keyboardOptions = KeyboardOptions(
                    imeAction = ImeAction.Next
                ),
                keyboardActions = KeyboardActions(
                    onNext = { focusManager.moveFocus(FocusDirection.Down) }
                ),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = IceWhite,
                    unfocusedTextColor = IceWhite,
                    focusedContainerColor = SurfaceCard,
                    unfocusedContainerColor = SurfaceCard,
                    focusedBorderColor = ElectricCyan,
                    unfocusedBorderColor = IceWhite.copy(alpha = 0.3f),
                    focusedLabelColor = ElectricCyan,
                    unfocusedLabelColor = IceWhite.copy(alpha = 0.6f),
                    cursorColor = ElectricCyan,
                    focusedPlaceholderColor = IceWhite.copy(alpha = 0.4f),
                    unfocusedPlaceholderColor = IceWhite.copy(alpha = 0.3f)
                ),
                shape = RoundedCornerShape(12.dp)
            )
            
            // URL field
            OutlinedTextField(
                value = url,
                onValueChange = { url = it },
                label = { Text("Ссылка на товар") },
                placeholder = { Text("https://www.wildberries.ru/...") },
                leadingIcon = {
                    Icon(
                        Icons.Default.Link,
                        contentDescription = null,
                        tint = ElectricCyan
                    )
                },
                modifier = Modifier.fillMaxWidth(),
                singleLine = false,
                maxLines = 3,
                keyboardOptions = KeyboardOptions(
                    keyboardType = KeyboardType.Uri,
                    imeAction = ImeAction.Done
                ),
                keyboardActions = KeyboardActions(
                    onDone = {
                        focusManager.clearFocus()
                        if (name.isNotBlank() && url.isNotBlank()) {
                            onCreateProduct(name, url)
                        }
                    }
                ),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedTextColor = IceWhite,
                    unfocusedTextColor = IceWhite,
                    focusedContainerColor = SurfaceCard,
                    unfocusedContainerColor = SurfaceCard,
                    focusedBorderColor = ElectricCyan,
                    unfocusedBorderColor = IceWhite.copy(alpha = 0.3f),
                    focusedLabelColor = ElectricCyan,
                    unfocusedLabelColor = IceWhite.copy(alpha = 0.6f),
                    cursorColor = ElectricCyan,
                    focusedPlaceholderColor = IceWhite.copy(alpha = 0.4f),
                    unfocusedPlaceholderColor = IceWhite.copy(alpha = 0.3f)
                ),
                shape = RoundedCornerShape(12.dp)
            )
            
            Spacer(modifier = Modifier.weight(1f))
            
            // Submit button
            Button(
                onClick = {
                    focusManager.clearFocus()
                    if (name.isNotBlank() && url.isNotBlank()) {
                        onCreateProduct(name, url)
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(56.dp),
                enabled = !isLoading && name.isNotBlank() && url.isNotBlank(),
                colors = ButtonDefaults.buttonColors(
                    containerColor = ElectricCyan,
                    disabledContainerColor = ElectricCyan.copy(alpha = 0.3f)
                ),
                shape = RoundedCornerShape(12.dp)
            ) {
                if (isLoading) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(24.dp),
                        color = DeepNavy,
                        strokeWidth = 2.dp
                    )
                } else {
                    Icon(
                        Icons.Default.Add,
                        contentDescription = null,
                        tint = DeepNavy
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text(
                        "Добавить товар",
                        color = DeepNavy,
                        fontWeight = FontWeight.Bold
                    )
                }
            }
            
            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}
