import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const PrivateRoute = ({ children }) => {
  const { token, loading } = useAuth();

  if (loading) {
    return <div className="loading">Загрузка...</div>;
  }

  return token ? children : <Navigate to="/login" replace />;
};

export default PrivateRoute;

