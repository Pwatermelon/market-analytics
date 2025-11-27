import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useAuth } from '../context/AuthContext';
import './ProductDetail.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const ProductDetail = () => {
  const { productId } = useParams();
  const navigate = useNavigate();
  const [product, setProduct] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [summary, setSummary] = useState(null);
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [loadingReviews, setLoadingReviews] = useState(false);
  const { logout } = useAuth();

  useEffect(() => {
    fetchProduct();
    fetchAnalytics();
    fetchReviews();
  }, [productId]);

  const fetchProduct = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/products/${productId}`);
      setProduct(response.data);
    } catch (error) {
      console.error('Ошибка загрузки товара:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/analytics/products/${productId}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Ошибка загрузки аналитики:', error);
    }
  };

  const fetchSummary = async () => {
    setLoadingSummary(true);
    try {
      const response = await axios.get(
        `${API_URL}/api/analytics/products/${productId}/summary`
      );
      setSummary(response.data);
    } catch (error) {
      console.error('Ошибка загрузки суммаризации:', error);
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchReviews = async () => {
    setLoadingReviews(true);
    try {
      const response = await axios.get(
        `${API_URL}/api/products/${productId}/reviews`
      );
      setReviews(response.data);
    } catch (error) {
      console.error('Ошибка загрузки отзывов:', error);
    } finally {
      setLoadingReviews(false);
    }
  };

  const handleParse = async () => {
    try {
      await axios.post(`${API_URL}/api/products/${productId}/parse`);
      alert('Парсинг запущен. Обновите страницу через несколько секунд.');
      setTimeout(() => {
        fetchAnalytics();
        fetchReviews();
        fetchProduct();
      }, 3000);
    } catch (error) {
      alert(error.response?.data?.detail || 'Ошибка парсинга');
    }
  };

  const handleAnalyze = async () => {
    try {
      await axios.post(`${API_URL}/api/analytics/products/${productId}/analyze`);
      alert('Анализ запущен. Обновите страницу через несколько секунд.');
      setTimeout(() => {
        fetchAnalytics();
        fetchReviews();
      }, 3000);
    } catch (error) {
      alert(error.response?.data?.detail || 'Ошибка анализа');
    }
  };

  const handleDelete = async () => {
    if (!window.confirm(`Вы уверены, что хотите удалить товар "${product.name}"? Все отзывы также будут удалены.`)) {
      return;
    }

    try {
      await axios.delete(`${API_URL}/api/products/${productId}`);
      alert('Товар успешно удален');
      navigate('/dashboard');
    } catch (error) {
      alert(error.response?.data?.detail || 'Ошибка удаления товара');
    }
  };

  if (loading) {
    return <div className="loading">Загрузка...</div>;
  }

  if (!product) {
    return <div className="error">Товар не найден</div>;
  }

  // Подготовка данных для графика
  const chartData = analytics?.timeline || [];

  return (
    <div className="product-detail">
      <header className="dashboard-header">
        <h1>Аналитика товара</h1>
        <div className="header-actions">
          <button onClick={() => navigate('/dashboard')} className="btn btn-secondary">
            Назад
          </button>
          <button onClick={logout} className="btn btn-secondary">
            Выйти
          </button>
        </div>
      </header>

      <div className="container">
        <div className="card">
          <h2>{product.name}</h2>
          <p>
            <strong>Маркетплейс:</strong> {product.marketplace}
          </p>
          <p>
            <strong>URL:</strong>{' '}
            <a href={product.url} target="_blank" rel="noopener noreferrer">
              {product.url}
            </a>
          </p>
          <div className="product-actions">
            <button onClick={handleParse} className="btn btn-primary">
              Парсить отзывы
            </button>
            <button onClick={handleAnalyze} className="btn btn-primary">
              Анализировать
            </button>
            <button onClick={handleDelete} className="btn btn-danger">
              Удалить товар
            </button>
          </div>
        </div>

        {analytics && (
          <div className="card">
            <h2>Статистика</h2>
            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-value">{analytics.total_reviews}</div>
                <div className="stat-label">Всего отзывов</div>
              </div>
              <div className="stat-item positive">
                <div className="stat-value">{analytics.positive_count}</div>
                <div className="stat-label">Позитивных</div>
              </div>
              <div className="stat-item negative">
                <div className="stat-value">{analytics.negative_count}</div>
                <div className="stat-label">Негативных</div>
              </div>
              <div className="stat-item neutral">
                <div className="stat-value">{analytics.neutral_count}</div>
                <div className="stat-label">Нейтральных</div>
              </div>
              <div className="stat-item">
                <div className="stat-value">
                  {analytics.average_sentiment.toFixed(3)}
                </div>
                <div className="stat-label">Средняя тональность</div>
              </div>
            </div>
          </div>
        )}

        {chartData.length > 0 && (
          <div className="card">
            <h2>График тональности</h2>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[-1, 1]} />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="sentiment"
                  stroke="#8884d8"
                  strokeWidth={2}
                  name="Тональность"
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="card">
          <h2>Суммаризация отзывов</h2>
          <button
            onClick={fetchSummary}
            className="btn btn-primary"
            disabled={loadingSummary}
          >
            {loadingSummary ? 'Загрузка...' : 'Получить суммаризацию'}
          </button>
          {summary && (
            <div className="summary-content">
              <p>
                <strong>На основе {summary.total_reviews} отзывов:</strong>
              </p>
              <p className="summary-text">{summary.summary}</p>
            </div>
          )}
        </div>

        <div className="card">
          <div className="reviews-header">
            <h2>Отзывы ({reviews.length})</h2>
            <button onClick={fetchReviews} className="btn btn-secondary" disabled={loadingReviews}>
              {loadingReviews ? 'Загрузка...' : 'Обновить'}
            </button>
          </div>
          {loadingReviews ? (
            <div className="loading">Загрузка отзывов...</div>
          ) : reviews.length === 0 ? (
            <div className="no-reviews">Отзывы не найдены. Запустите парсинг отзывов.</div>
          ) : (
            <div className="reviews-list">
              {reviews.map((review) => (
                <div key={review.id} className={`review-item ${review.sentiment_label || ''}`}>
                  <div className="review-header">
                    <div className="review-author">
                      <strong>{review.author || 'Анонимный пользователь'}</strong>
                      {review.rating && (
                        <span className="review-rating">
                          {'⭐'.repeat(review.rating)}
                        </span>
                      )}
                    </div>
                    <div className="review-meta">
                      <span className="review-date">
                        {new Date(review.date).toLocaleDateString('ru-RU')}
                      </span>
                      {review.sentiment_label && (
                        <span className={`sentiment-badge ${review.sentiment_label}`}>
                          {review.sentiment_label === 'positive' && '😊 Позитивный'}
                          {review.sentiment_label === 'negative' && '😞 Негативный'}
                          {review.sentiment_label === 'neutral' && '😐 Нейтральный'}
                          {review.sentiment !== null && review.sentiment !== undefined && (
                            <span className="sentiment-score">
                              {' '}({review.sentiment > 0 ? '+' : ''}{review.sentiment.toFixed(2)})
                            </span>
                          )}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="review-text">{review.text}</div>
                  {review.summary && (
                    <div className="review-summary">
                      <strong>Краткое содержание:</strong> {review.summary}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProductDetail;

