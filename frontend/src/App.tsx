import React, { useState } from 'react';

type Product = {
  title: string;
  price: string;
  img: string;
  link: string;
  product_id: string;
  source: string;
};

type Review = {
  text: string;
  stars: number;
};

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const App: React.FC = () => {
  const [query, setQuery] = useState('');
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(false);
  const [reviews, setReviews] = useState<Record<string, Review[]>>({});
  const [loadingReviews, setLoadingReviews] = useState<string | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setProducts([]);
    setReviews({});
    try {
      const res = await fetch(`${API_URL}/search?q=${encodeURIComponent(query)}`);
      const data = await res.json();
      setProducts(data.products || []);
    } catch {
      setProducts([]);
    }
    setLoading(false);
  };

  const handleLoadReviews = async (product_id: string, source: string) => {
    setLoadingReviews(product_id);
    try {
      const res = await fetch(`${API_URL}/reviews?product_id=${product_id}&source=${source}`);
      const data = await res.json();
      setReviews(prev => ({ ...prev, [product_id]: data.reviews || [] }));
    } catch {
      setReviews(prev => ({ ...prev, [product_id]: [] }));
    }
    setLoadingReviews(null);
  };

  return (
    <div style={{ maxWidth: 800, margin: '40px auto', fontFamily: 'sans-serif' }}>
      <h1>Market Analytics: Wildberries & Яндекс.Маркет</h1>
      <form onSubmit={handleSearch} style={{ marginBottom: 24 }}>
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Поиск товаров..."
          style={{ padding: 8, width: 300, fontSize: 16 }}
        />
        <button type="submit" style={{ padding: 8, marginLeft: 8, fontSize: 16 }}>Искать</button>
      </form>
      {loading && <div>Загрузка...</div>}
      <div>
        {products.map((p, idx) => (
          <div key={idx} style={{ display: 'flex', marginBottom: 24, border: '1px solid #eee', borderRadius: 8, padding: 16 }}>
            <img src={p.img} alt={p.title} style={{ width: 120, height: 120, objectFit: 'contain', marginRight: 24 }} />
            <div style={{ flex: 1 }}>
              <a href={p.link} target="_blank" rel="noopener noreferrer" style={{ fontSize: 18, fontWeight: 600 }}>{p.title}</a>
              <div style={{ fontSize: 16, color: '#a600a6', margin: '8px 0' }}>{p.price}</div>
              <div style={{ marginBottom: 8 }}>
                <span style={{ padding: '2px 8px', borderRadius: 6, background: p.source === 'wb' ? '#a600a6' : '#ffdb4d', color: p.source === 'wb' ? '#fff' : '#222', fontSize: 13 }}>
                  {p.source === 'wb' ? 'Wildberries' : 'Яндекс.Маркет'}
                </span>
              </div>
              <div>
                <button
                  onClick={() => handleLoadReviews(p.product_id, p.source)}
                  disabled={loadingReviews === p.product_id}
                  style={{ padding: 6, fontSize: 15, marginBottom: 8 }}
                >
                  {loadingReviews === p.product_id ? 'Загрузка отзывов...' : 'Показать отзывы'}
                </button>
                {reviews[p.product_id] && (
                  <ul style={{ marginTop: 8 }}>
                    {reviews[p.product_id].length === 0 && <li>Нет отзывов</li>}
                    {reviews[p.product_id].map((r, i) => (
                      <li key={i} style={{ marginBottom: 8 }}>
                        <span style={{ color: '#f39c12', fontWeight: 600 }}>{'★'.repeat(r.stars)}{'☆'.repeat(5 - r.stars)}</span>
                        <span style={{ marginLeft: 8 }}>{r.text}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App; 