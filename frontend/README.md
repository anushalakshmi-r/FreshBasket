# FreshBasket storefront

The React/Vite storefront reads categories, brands, and products from the Django catalogue API. Product prices, stock, categories, brands, and image URLs come from API responses; cart and wishlist state remain in the browser.

## Run locally

1. Make sure the Django API is running at `http://127.0.0.1:8000`.
2. For a direct backend connection, set `VITE_API_URL` in `.env.local` to the backend API root, including `/api` (for example, `http://127.0.0.1:8000/api`). If unset, Vite proxies `/api` requests to the local backend.
3. From this directory, install dependencies if needed and start Vite:

   ```powershell
   npm install
   npm run dev
   ```

Vite serves the app at `http://localhost:5173`. Restart Vite after changing an environment file.

The app uses:

- `GET /api/categories/`
- `GET /api/brands/`
- `GET /api/products/` (20-item pages)

Product search and filters use the backend's `search`, `category`, `subcategory`, `brand`, `min_price`, `max_price`, `in_stock`, `featured`, `bestseller`, `ordering`, and `page` query parameters.

Run `npm run build` and `npm run lint` to validate the frontend.
