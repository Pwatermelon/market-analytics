package com.marketanalytics.app.data.repository

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class SettingsRepository(private val context: Context) {
    
    companion object {
        private val API_URL_KEY = stringPreferencesKey("api_url")
        private val AUTH_TOKEN_KEY = stringPreferencesKey("auth_token")
        private val USER_ID_KEY = intPreferencesKey("user_id")
        private val USERNAME_KEY = stringPreferencesKey("username")
        private val USER_EMAIL_KEY = stringPreferencesKey("user_email")
        
        const val DEFAULT_API_URL = "http://10.0.2.2:8000" // api-gateway через эмулятор
    }
    
    // API URL
    val apiUrl: Flow<String> = context.dataStore.data.map { preferences ->
        preferences[API_URL_KEY] ?: DEFAULT_API_URL
    }
    
    suspend fun getApiUrl(): String {
        return context.dataStore.data.first()[API_URL_KEY] ?: DEFAULT_API_URL
    }
    
    suspend fun setApiUrl(url: String) {
        context.dataStore.edit { preferences ->
            preferences[API_URL_KEY] = url
        }
    }
    
    // Auth Token
    val authToken: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[AUTH_TOKEN_KEY]
    }
    
    suspend fun getAuthToken(): String? {
        return context.dataStore.data.first()[AUTH_TOKEN_KEY]
    }
    
    suspend fun setAuthToken(token: String?) {
        context.dataStore.edit { preferences ->
            if (token != null) {
                preferences[AUTH_TOKEN_KEY] = token
            } else {
                preferences.remove(AUTH_TOKEN_KEY)
            }
        }
    }
    
    // User ID
    val userId: Flow<Int?> = context.dataStore.data.map { preferences ->
        preferences[USER_ID_KEY]
    }
    
    suspend fun getUserId(): Int? {
        return context.dataStore.data.first()[USER_ID_KEY]
    }
    
    suspend fun setUserId(id: Int?) {
        context.dataStore.edit { preferences ->
            if (id != null) {
                preferences[USER_ID_KEY] = id
            } else {
                preferences.remove(USER_ID_KEY)
            }
        }
    }
    
    // Username
    val username: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[USERNAME_KEY]
    }
    
    suspend fun getUsername(): String? {
        return context.dataStore.data.first()[USERNAME_KEY]
    }
    
    suspend fun setUsername(name: String?) {
        context.dataStore.edit { preferences ->
            if (name != null) {
                preferences[USERNAME_KEY] = name
            } else {
                preferences.remove(USERNAME_KEY)
            }
        }
    }
    
    // User Email
    val userEmail: Flow<String?> = context.dataStore.data.map { preferences ->
        preferences[USER_EMAIL_KEY]
    }
    
    suspend fun setUserEmail(email: String?) {
        context.dataStore.edit { preferences ->
            if (email != null) {
                preferences[USER_EMAIL_KEY] = email
            } else {
                preferences.remove(USER_EMAIL_KEY)
            }
        }
    }
    
    // Is Logged In
    val isLoggedIn: Flow<Boolean> = context.dataStore.data.map { preferences ->
        preferences[AUTH_TOKEN_KEY] != null
    }
    
    suspend fun isLoggedIn(): Boolean {
        return context.dataStore.data.first()[AUTH_TOKEN_KEY] != null
    }
    
    // Save Auth Data
    suspend fun saveAuthData(token: String, userId: Int, username: String, email: String? = null) {
        context.dataStore.edit { preferences ->
            preferences[AUTH_TOKEN_KEY] = token
            preferences[USER_ID_KEY] = userId
            preferences[USERNAME_KEY] = username
            email?.let { preferences[USER_EMAIL_KEY] = it }
        }
    }
    
    // Logout
    suspend fun logout() {
        context.dataStore.edit { preferences ->
            preferences.remove(AUTH_TOKEN_KEY)
            preferences.remove(USER_ID_KEY)
            preferences.remove(USERNAME_KEY)
            preferences.remove(USER_EMAIL_KEY)
        }
    }
    
    // Clear all settings
    suspend fun clearAll() {
        context.dataStore.edit { preferences ->
            preferences.clear()
        }
    }
}
