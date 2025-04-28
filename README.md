# Market Analytics Service

A microservice-based system for collecting and analyzing product data from various marketplaces.

## Architecture

The system consists of the following components:

1. **Parser Services** - Individual FastAPI services for each marketplace:
   - Ozon Parser (`parsers/ozon/`)
   - Gold Apple Parser (`parsers/goldapple/`)
   - Wildberries Parser (`parsers/wildberries/`)
   - Yandex Market Parser (`parsers/yandexmarket/`)

2. **Common Modules** (`parsers/common/`):
   - `browser.py` - BrowserManager for handling Playwright browser automation
   - `parser.py` - Base parser classes and marketplace-specific implementations

3. **API Gateway** - Routes requests to appropriate parser services
4. **Frontend** - Web interface for interacting with the system

## Features

- Automated product data collection from multiple marketplaces
- Browser automation using Playwright for reliable data extraction
- Anti-bot detection evasion with random User-Agents and browser fingerprinting
- Rate limiting and request delays
- Detailed logging for debugging
- Health check endpoints
- Docker containerization
- Image loading and processing for product listings

## Setup

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Run individual services:
```bash
# Run Ozon parser
cd parsers/ozon
uvicorn main:app --host 0.0.0.0 --port 8001

# Run Gold Apple parser
cd parsers/goldapple
uvicorn main:app --host 0.0.0.0 --port 8003

# Run Wildberries parser
cd parsers/wildberries
uvicorn main:app --host 0.0.0.0 --port 8002

# Run Yandex Market parser
cd parsers/yandexmarket
uvicorn main:app --host 0.0.0.0 --port 8004

# Run API Gateway
cd api-gateway
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Docker Setup

1. Build and start all services:
```bash
docker-compose up --build
```

2. Access the services:
- Frontend: http://localhost:3000
- API Gateway: http://localhost:8000
- Ozon Parser: http://localhost:8001
- Gold Apple Parser: http://localhost:8003
- Wildberries Parser: http://localhost:8002
- Yandex Market Parser: http://localhost:8004

## API Endpoints

Each parser service exposes the following endpoints:

- `POST /search` - Search for products
  ```json
  {
    "query": "search term"
  }
  ```
- `GET /health` - Health check endpoint

## Development

### Adding a New Marketplace Parser

1. Create a new directory in `parsers/` for your marketplace
2. Implement the parser service using FastAPI
3. Use the common `BrowserManager` for browser automation
4. Implement marketplace-specific parsing logic
5. Add the service to `docker-compose.yml`

### Common Components

- `BrowserManager` - Handles browser automation with Playwright
  - Random User-Agent generation
  - Anti-bot detection evasion
  - Image loading support
  - Proper page scrolling for dynamic content
- `ProductParser` - Base class for marketplace-specific parsers
- Shared utilities for handling requests, parsing responses, and error handling

## Error Handling

The system implements comprehensive error handling:
- Detailed logging of all operations
- Graceful handling of network errors
- Retry mechanisms for failed requests
- Proper cleanup of browser resources

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'common'**
   - Ensure the common modules are properly included in the Docker build
   - Check that the build context in docker-compose.yml is set correctly

2. **Browser automation issues**
   - Verify that Playwright is properly installed
   - Check that the browser is launched with the correct arguments
   - Ensure all dependencies are installed

3. **Image loading issues**
   - Check that the browser is configured to load images
   - Verify that the page is properly scrolled to load all images
   - Ensure image URLs are properly formatted

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 