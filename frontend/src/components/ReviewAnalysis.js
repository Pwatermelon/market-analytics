import React from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Chip,
  Divider,
  Grid,
  List,
  ListItem,
  ListItemText,
  Paper,
} from '@mui/material';

const ReviewAnalysis = ({ analysis }) => {
  if (!analysis) return null;

  const {
    summary,
    sentiment,
    aspects,
    quality_score,
    recommendations,
    total_reviews,
  } = analysis;

  // Функция для определения цвета оценки качества
  const getQualityColor = (score) => {
    if (score >= 80) return 'success.main';
    if (score >= 60) return 'info.main';
    if (score >= 40) return 'warning.main';
    return 'error.main';
  };

  // Функция для форматирования процентов
  const formatPercent = (value) => `${Math.round(value)}%`;

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h5" gutterBottom>
        Анализ отзывов
      </Typography>

      {/* Основные показатели */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Оценка качества
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography
                  variant="h3"
                  sx={{ color: getQualityColor(quality_score) }}
                >
                  {quality_score}
                </Typography>
                <Typography variant="body1" sx={{ ml: 1 }}>
                  / 100
                </Typography>
              </Box>
              <Typography variant="body2" color="text.secondary">
                На основе {total_reviews} отзывов
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Тональность отзывов
              </Typography>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="success.main">
                  Положительные: {formatPercent(sentiment.positive)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={sentiment.positive}
                  color="success"
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="warning.main">
                  Нейтральные: {formatPercent(sentiment.neutral)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={sentiment.neutral}
                  color="warning"
                  sx={{ mb: 1 }}
                />
                <Typography variant="body2" color="error.main">
                  Отрицательные: {formatPercent(sentiment.negative)}
                </Typography>
                <LinearProgress
                  variant="determinate"
                  value={sentiment.negative}
                  color="error"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Краткое содержание */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Краткое содержание отзывов
        </Typography>
        <Typography variant="body1">{summary}</Typography>
      </Paper>

      {/* Аспекты товара */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Анализ по аспектам
          </Typography>
          <Grid container spacing={2}>
            {Object.entries(aspects).map(([aspect, data]) => (
              <Grid item xs={12} sm={6} md={4} key={aspect}>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle1">{aspect}</Typography>
                  <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
                    <Chip
                      label={`👍 ${formatPercent(data.positive)}`}
                      color="success"
                      size="small"
                    />
                    <Chip
                      label={`👎 ${formatPercent(data.negative)}`}
                      color="error"
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    Упоминаний: {data.mentions}
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </CardContent>
      </Card>

      {/* Рекомендации */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Рекомендации
          </Typography>
          <List>
            {recommendations.map((recommendation, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemText primary={recommendation} />
                </ListItem>
                {index < recommendations.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

export default ReviewAnalysis; 