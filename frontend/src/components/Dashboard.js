import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import './Dashboard.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const Dashboard = () => {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [newProduct, setNewProduct] = useState({ name: '', url: '', marketplace: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/products`);
      setProducts(response.data);
    } catch (error) {
      console.error('Ошибка загрузки товаров:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddProduct = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      await axios.post(`${API_URL}/api/products`, newProduct);
      setSuccess('Товар успешно добавлен');
      setNewProduct({ name: '', url: '', marketplace: '' });
      setShowAddForm(false);
      fetchProducts();
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка добавления товара');
    }
  };

  const handleParse = async (productId) => {
    try {
      await axios.post(`${API_URL}/api/products/${productId}/parse`);
      setSuccess('Парсинг запущен');
      setTimeout(() => fetchProducts(), 2000);
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка парсинга');
    }
  };

  const handleAnalyze = async (productId) => {
    try {
      await axios.post(`${API_URL}/api/analytics/products/${productId}/analyze`);
      setSuccess('Анализ запущен');
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка анализа');
    }
  };

  const handleDelete = async (productId, productName) => {
    if (!window.confirm(`Вы уверены, что хотите удалить товар "${productName}"? Все отзывы также будут удалены.`)) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/products/${productId}`);
      setSuccess('Товар успешно удален');
      fetchProducts();
    } catch (error) {
      setError(error.response?.data?.detail || 'Ошибка удаления товара');
    }
  };

  if (loading) {
    return <div className="loading">Загрузка...</div>;
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Market Analytics</h1>
        <div className="header-actions">
          <span>Привет, {user?.username}</span>
          <button onClick={logout} className="btn btn-secondary">
            Выйти
          </button>
        </div>
      </header>

      <div className="container">
        {error && <div className="error-message">{error}</div>}
        {success && <div className="success-message">{success}</div>}

        <div className="dashboard-actions">
          <button
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn btn-primary"
          >
            {showAddForm ? 'Отмена' : '+ Добавить товар'}
          </button>
        </div>

        {showAddForm && (
          <div className="card">
            <h2>Добавить товар</h2>
            <form onSubmit={handleAddProduct}>
              <div className="form-group">
                <label>Название товара</label>
                <input
                  type="text"
                  value={newProduct.name}
                  onChange={(e) =>
                    setNewProduct({ ...newProduct, name: e.target.value })
                  }
                  required
                />
              </div>
              <div className="form-group">
                <label>URL товара</label>
                <input
                  type="url"
                  value={newProduct.url}
                  onChange={(e) =>
                    setNewProduct({ ...newProduct, url: e.target.value })
                  }
                  required
                  placeholder="https://www.wildberries.ru/catalog/..."
                />
              </div>
              <div className="form-group">
                <label>Маркетплейс</label>
                <select
                  value={newProduct.marketplace}
                  onChange={(e) =>
                    setNewProduct({ ...newProduct, marketplace: e.target.value })
                  }
                >
                  <option value="">Автоопределение</option>
                  <option value="wildberries">Wildberries</option>
                  <option value="ozon">Ozon</option>
                  <option value="yandex-market">Яндекс.Маркет</option>
                </select>
              </div>
              <button type="submit" className="btn btn-primary">
                Добавить
              </button>
            </form>
          </div>
        )}

        <div className="products-grid">
          {products.length === 0 ? (
            <div className="card">
              <p>У вас пока нет товаров. Добавьте первый товар для отслеживания.</p>
            </div>
          ) : (
            products.map((product) => (
              <div key={product.id} className="card product-card">
                <h3>{product.name}</h3>
                <p className="product-meta">
                  <strong>Маркетплейс:</strong> {product.marketplace}
                </p>
                <p className="product-meta">
                  <strong>Добавлен:</strong>{' '}
                  {new Date(product.created_at).toLocaleDateString('ru-RU')}
                </p>
                <div className="product-actions">
                  <button
                    onClick={() => navigate(`/products/${product.id}`)}
                    className="btn btn-primary"
                  >
                    Открыть
                  </button>
                  <button
                    onClick={() => handleParse(product.id)}
                    className="btn btn-secondary"
                  >
                    Парсить
                  </button>
                  <button
                    onClick={() => handleAnalyze(product.id)}
                    className="btn btn-secondary"
                  >
                    Анализировать
                  </button>
                  <button
                    onClick={() => handleDelete(product.id, product.name)}
                    className="btn btn-danger"
                  >
                    Удалить
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

