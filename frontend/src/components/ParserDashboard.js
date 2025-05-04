import React, { useState } from 'react';
import {
  Box,
  TextField,
  Button,
  Card,
  CardContent,
  Typography,
  Grid,
  Snackbar,
  Alert,
  CircularProgress,
  Tabs,
  Tab,
} from '@mui/material';
import ReviewAnalysis from './ReviewAnalysis';

const ParserDashboard = () => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [activeTab, setActiveTab] = useState(0);
  const [reviewAnalysis, setReviewAnalysis] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setNotification({
        open: true,
        message: 'Пожалуйста, введите поисковый запрос',
        severity: 'warning',
      });
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/parse', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (!response.ok) {
        throw new Error('Ошибка при выполнении запроса');
      }

      const data = await response.json();
      setResults(data.results || []);
      setNotification({
        open: true,
        message: 'Поиск успешно завершен',
        severity: 'success',
      });
    } catch (err) {
      setError(err.message);
      setNotification({
        open: true,
        message: `Ошибка: ${err.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleProductSelect = async (product) => {
    setSelectedProduct(product);
    setActiveTab(1); // Переключаемся на вкладку с анализом
    setLoading(true);
    
    try {
      const response = await fetch(`/api/analyze-reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          product_url: product.url,
          marketplace: product.marketplace 
        }),
      });

      if (!response.ok) {
        throw new Error('Ошибка при анализе отзывов');
      }

      const analysisData = await response.json();
      setReviewAnalysis(analysisData);
    } catch (err) {
      setNotification({
        open: true,
        message: `Ошибка при анализе отзывов: ${err.message}`,
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleCloseNotification = () => {
    setNotification({ ...notification, open: false });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Анализ товаров
      </Typography>

      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2}>
          <Grid item xs={12} sm={9}>
            <TextField
              fullWidth
              label="Введите название товара"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
          </Grid>
          <Grid item xs={12} sm={3}>
            <Button
              fullWidth
              variant="contained"
              onClick={handleSearch}
              disabled={loading}
              sx={{ height: '56px' }}
            >
              {loading ? <CircularProgress size={24} /> : 'Поиск'}
            </Button>
          </Grid>
        </Grid>
      </Box>

      {selectedProduct && (
        <Box sx={{ mb: 3 }}>
          <Tabs value={activeTab} onChange={handleTabChange}>
            <Tab label="Результаты поиска" />
            <Tab label="Анализ отзывов" />
          </Tabs>
        </Box>
      )}

      {activeTab === 0 && (
        <Grid container spacing={2}>
          {results.map((product, index) => (
            <Grid item xs={12} sm={6} md={4} key={index}>
              <Card 
                sx={{ 
                  cursor: 'pointer',
                  '&:hover': { boxShadow: 6 }
                }}
                onClick={() => handleProductSelect(product)}
              >
                <CardContent>
                  {/* Фото товара */}
                  {product.photo || product.image_url ? (
                    <Box sx={{ mb: 1, textAlign: 'center' }}>
                      <img
                        src={product.photo || product.image_url}
                        alt={product.title || product.name}
                        style={{ maxWidth: '100%', maxHeight: 160, objectFit: 'contain' }}
                      />
                    </Box>
                  ) : null}
                  <Typography variant="h6" gutterBottom noWrap>
                    {product.title || product.name}
                  </Typography>
                  <Typography color="text.secondary">
                    Цена: {product.price} ₽
                  </Typography>
                  <Typography color="text.secondary">
                    Рейтинг: {product.rating}
                  </Typography>
                  {product.seller && (
                    <Typography color="text.secondary">
                      Продавец: {product.seller}
                    </Typography>
                  )}
                  <Typography 
                    variant="body2" 
                    color="primary" 
                    component="a" 
                    href={product.url} 
                    target="_blank"
                    onClick={(e) => e.stopPropagation()}
                  >
                    Открыть на сайте
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {activeTab === 1 && selectedProduct && (
        <Box>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              {/* Фото товара */}
              {selectedProduct.photo || selectedProduct.image_url ? (
                <Box sx={{ mb: 2, textAlign: 'center' }}>
                  <img
                    src={selectedProduct.photo || selectedProduct.image_url}
                    alt={selectedProduct.title || selectedProduct.name}
                    style={{ maxWidth: 220, maxHeight: 220, objectFit: 'contain' }}
                  />
                </Box>
              ) : null}
              <Typography variant="h6">{selectedProduct.title || selectedProduct.name}</Typography>
              <Typography color="text.secondary">
                Маркетплейс: {selectedProduct.marketplace}
              </Typography>
              <Typography color="text.secondary">
                Цена: {selectedProduct.price} ₽
              </Typography>
              <Typography color="text.secondary">
                Рейтинг: {selectedProduct.rating}
              </Typography>
              {selectedProduct.seller && (
                <Typography color="text.secondary">
                  Продавец: {selectedProduct.seller}
                </Typography>
              )}
              <Typography 
                variant="body2" 
                color="primary" 
                component="a" 
                href={selectedProduct.url} 
                target="_blank"
                onClick={(e) => e.stopPropagation()}
              >
                Открыть на сайте
              </Typography>
            </CardContent>
          </Card>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <ReviewAnalysis analysis={reviewAnalysis} />
          )}
        </Box>
      )}

      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleCloseNotification}
      >
        <Alert
          onClose={handleCloseNotification}
          severity={notification.severity}
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ParserDashboard; 