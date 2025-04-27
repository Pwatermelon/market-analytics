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
  InputLabel
} from '@material-ui/core';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [marketplace, setMarketplace] = useState('');
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/search', {
        query,
        marketplace: marketplace || undefined
      });
      setProducts(response.data);
    } catch (error) {
      console.error('Error searching products:', error);
    }
    setLoading(false);
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

      <Grid container spacing={3}>
        {products.map((product) => (
          <Grid item xs={12} sm={6} md={4} key={product.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h2">
                  {product.name}
                </Typography>
                <Typography color="textSecondary">
                  {product.marketplace}
                </Typography>
                <Typography variant="h5" component="p">
                  {product.price} ₽
                </Typography>
                {product.rating && (
                  <Typography variant="body2" color="textSecondary">
                    Рейтинг: {product.rating}
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
    </Container>
  );
}

export default App; 