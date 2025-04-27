import React, { useState } from 'react';
import { 
  Container, 
  TextField, 
  Button, 
  Card, 
  CardContent, 
  Typography, 
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Snackbar
} from '@material-ui/core';
import { Alert } from '@material-ui/lab';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [marketplace, setMarketplace] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Введите поисковый запрос');
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const searchData = {
        query: query.trim(),
        marketplace: marketplace || undefined
      };
      console.log('Sending search request:', searchData);
      
      const response = await axios.post('/api/search', searchData, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      console.log('Received response:', response.data);
      
      if (Array.isArray(response.data)) {
        setProducts(response.data);
        if (response.data.length === 0) {
          setError('Товары не найдены');
        }
      } else {
        console.error('Unexpected response format:', response.data);
        setError('Неверный формат ответа от сервера');
      }
    } catch (error) {
      console.error('Error searching products:', error);
      if (error.response) {
        console.error('Error response:', error.response.data);
        setError(error.response.data.detail || 'Ошибка при поиске товаров');
      } else {
        setError('Ошибка при подключении к серверу');
      }
    }
    setLoading(false);
  };

  const handleCloseError = () => {
    setError(null);
  };

  return (
    <Container maxWidth="lg" style={{ marginTop: '2rem' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Market Analytics
      </Typography>
      
      <Grid container spacing={2} style={{ marginBottom: '2rem' }}>
        <Grid item xs={12} sm={6}>
          <TextField
            fullWidth
            label="Поиск товаров"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                handleSearch();
              }
            }}
          />
        </Grid>
        <Grid item xs={12} sm={4}>
          <FormControl fullWidth>
            <InputLabel>Маркетплейс</InputLabel>
            <Select
              value={marketplace}
              onChange={(e) => setMarketplace(e.target.value)}
            >
              <MenuItem value="">Все</MenuItem>
              <MenuItem value="ozon">Ozon</MenuItem>
              <MenuItem value="wildberries">Wildberries</MenuItem>
              <MenuItem value="goldapple">Золотое яблоко</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <Button
            fullWidth
            variant="contained"
            color="primary"
            onClick={handleSearch}
            disabled={loading}
            style={{ height: '100%' }}
          >
            {loading ? 'Поиск...' : 'Найти'}
          </Button>
        </Grid>
      </Grid>

      {products.length === 0 && !loading && (
        <Typography variant="body1" color="textSecondary" align="center">
          Введите поисковый запрос и нажмите "Найти"
        </Typography>
      )}

      <Grid container spacing={3}>
        {products.map((product) => (
          <Grid item xs={12} sm={6} md={4} key={product.id}>
            <Card>
              <CardContent>
                {product.image_url && (
                  <img
                    src={product.image_url}
                    alt={product.name}
                    style={{ width: '100%', maxHeight: 200, objectFit: 'contain', marginBottom: 16 }}
                  />
                )}
                <Typography variant="h6" component="h2" gutterBottom>
                  {product.name}
                </Typography>
                <Chip 
                  label={product.marketplace === 'ozon' ? 'Ozon' : 
                         product.marketplace === 'wildberries' ? 'Wildberries' : 
                         product.marketplace === 'goldapple' ? 'Золотое яблоко' : 
                         product.marketplace}
                  color="primary"
                  size="small"
                  style={{ marginBottom: '1rem' }}
                />
                <Typography variant="h5" component="p" gutterBottom>
                  {product.price} ₽
                </Typography>
                {product.rating && (
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    Рейтинг: {product.rating}
                  </Typography>
                )}
                {product.description && (
                  <Typography variant="body2" color="textSecondary" gutterBottom>
                    {product.description}
                  </Typography>
                )}
                <Button
                  variant="contained"
                  color="primary"
                  href={product.url}
                  target="_blank"
                  style={{ marginTop: '1rem' }}
                >
                  Открыть
                </Button>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Snackbar open={!!error} autoHideDuration={6000} onClose={handleCloseError}>
        <Alert onClose={handleCloseError} severity="error">
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default App; 