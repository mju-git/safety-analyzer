# Product Safety Analyzer - Frontend

Minimal React web app for the Product Safety Analyzer.

## Features

- Search for products by name or brand
- Select a product from search results
- Analyze product safety
- Display safety score and detailed explanations

## Setup

1. **Install dependencies:**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

   The app will be available at `http://localhost:3000`

3. **Make sure the backend is running:**
   - Backend should be running on `http://localhost:8000`
   - The frontend is configured to proxy API requests

## Usage

1. Enter a product name in the search box (e.g., "milk", "shampoo")
2. Click "Search" or press Enter
3. Select a product from the results
4. View the safety analysis including:
   - Safety score (0-100)
   - Risk level
   - Recommendation
   - Flagged ingredients with details
   - Beneficial ingredients

## API Endpoints Used

- `GET /search/products?q={query}` - Search for products
- `POST /analyze/product` - Analyze a product by ID

## Build for Production

```bash
npm run build
```

The built files will be in the `dist` directory.
