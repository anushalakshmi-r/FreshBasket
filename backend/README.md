# FreshBasket backend

The Django REST API lives in `backend/`; it uses the Python environment and `.env` file in the project root.
The settings intentionally load `FreshBasket/.env` (not `backend/.env`). Django 5.2 is pinned to support the installed MySQL 8.0 server.

## Local setup

1. Copy `.env.example` to `.env` if `.env` does not already exist. Set `DJANGO_SECRET_KEY` to a long random value and enter your MySQL username/password in `.env`. Do not share or commit `.env`.
2. Create the database with an account that has permission to create databases. In MySQL Workbench, open a SQL tab and run:

   ```sql
   CREATE DATABASE freshbasket_db
     CHARACTER SET utf8mb4
     COLLATE utf8mb4_unicode_ci;
   ```

   Alternatively, connect in a MySQL terminal with `mysql -u <your_mysql_user> -p` and run the same SQL. The `-p` option prompts for the password without putting it in the command.
3. From the project root, activate the environment and apply migrations:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   python backend\manage.py migrate
   ```

4. Start the API:

   ```powershell
   python backend\manage.py runserver 127.0.0.1:8000
   ```

The API root is `http://127.0.0.1:8000/api/`; its database-aware health check is `http://127.0.0.1:8000/api/health/`.

## Customer authentication

Authentication uses Django's built-in `User` model and a one-to-one customer profile. The profile stores a normalized, database-unique email address and phone number; registration creates an opaque username internally so existing Django authentication migrations remain compatible.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/accounts/csrf/` | Set a CSRF cookie and return a request token |
| `POST` | `/api/accounts/register/` | Register a customer and start a session |
| `POST` | `/api/accounts/login/` | Sign in with email and password |
| `POST` | `/api/accounts/token/refresh/` | Rotate the HttpOnly refresh cookie and return a new access token |
| `GET` | `/api/accounts/profile/` | Get the authenticated customer's profile |
| `PATCH` | `/api/accounts/profile/` | Update the authenticated customer's profile |
| `POST` | `/api/accounts/logout/` | Blacklist the refresh token and clear its cookie |

Registration accepts `first_name`, `last_name`, `email`, `phone_number`, `password`, and `confirm_password`. Registration and login responses return a short-lived access token and the current customer's profile; the refresh token is only set in an HttpOnly cookie. Access tokens expire after 10 minutes, and refresh tokens expire after 7 days and rotate on use. Logout uses the SimpleJWT blacklist app.

Browser clients must send `credentials: "include"` for account requests. Before each POST/PATCH, request `/api/accounts/csrf/` and send its `csrf_token` response value in the `X-CSRFToken` header. This response also includes `refresh_cookie_present`; clients can use it to avoid an unnecessary refresh request when no session cookie exists. Send the access token as `Authorization: Bearer <access-token>` for profile requests. Keep access tokens in memory rather than persistent browser storage; never store passwords. The Vite development server proxies `/api/accounts/` to Django so refresh cookies stay same-origin and are not treated as third-party cookies. Production deployments should likewise reverse-proxy the account API through the frontend origin. The development CORS and CSRF allowlists include `http://localhost:5173` for other cross-origin API access.

The profile response contains only the signed-in customer's own fields:

```json
{
  "id": 1,
  "first_name": "Asha",
  "last_name": "Customer",
  "email": "asha@example.test",
  "phone_number": "+919876543210",
  "created_at": "2026-11-20T08:00:00Z",
  "updated_at": "2026-11-20T08:00:00Z"
}
```

The example is illustrative, not a real customer record.

## Customer cart and wishlist

Cart and wishlist records are stored in MySQL and are scoped to the authenticated customer. All endpoints below require the existing JWT access token in the `Authorization: Bearer <access-token>` header. The Vite development server proxies these paths to Django so authenticated requests use the same origin as the refresh-cookie flow.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/cart/` | Get or create the customer's cart |
| `POST` | `/api/cart/add/` | Add a product or increase its existing quantity |
| `PATCH` | `/api/cart/items/<id>/` | Set a cart item's quantity |
| `DELETE` | `/api/cart/items/<id>/` | Remove an item from the customer's cart |
| `DELETE` | `/api/cart/clear/` | Remove all items from the customer's cart |
| `GET` | `/api/wishlist/` | Get or create the customer's wishlist |
| `POST` | `/api/wishlist/add/` | Save a product to the wishlist |
| `DELETE` | `/api/wishlist/items/<id>/` | Remove a wishlist item |
| `DELETE` | `/api/wishlist/remove-product/<product_id>/` | Remove a product from the wishlist |

Add requests use `{"product_id": 12, "quantity": 2}` for the cart and `{"product_id": 12}` for the wishlist. Cart quantities must be positive, the product must be active, and requested quantities cannot exceed current available stock. Prices, totals, stock, and customer ownership are read or enforced by the backend; clients cannot submit them as authoritative values. Duplicate cart additions increase the existing row, and duplicate wishlist additions are idempotent.

A cart response includes backend-calculated item subtotals and total:

```json
{
  "id": 1,
  "items": [
    {
      "id": 8,
      "product": {
        "id": 12,
        "name": "Example grocery",
        "slug": "example-grocery",
        "sku": "FB-DEMO-012",
        "image_url": "",
        "brand_name": "",
        "pack_size": "1 pack",
        "selling_price": "10.00",
        "mrp": "12.00",
        "discount_percentage": "16.67",
        "available_stock": 5,
        "in_stock": true,
        "is_active": true
      },
      "quantity": 2,
      "item_subtotal": "20.00"
    }
  ],
  "item_count": 2,
  "total": "20.00",
  "created_at": "2026-11-20T08:00:00Z",
  "updated_at": "2026-11-20T08:00:00Z"
}
```

Wishlist responses use the same product detail object in each item, without quantity or subtotal. Example IDs, prices, stock, and timestamps above are illustrative only. After changing models, apply the cart migration with `python manage.py migrate` from `backend/`; run the focused endpoint tests with `python manage.py test cart`.

## Delivery addresses, checkout, and orders

Delivery addresses and orders belong to the authenticated customer. Send the existing JWT access token as `Authorization: Bearer <access-token>`; the Vite proxy forwards these API paths to Django.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` / `POST` | `/api/accounts/addresses/` | List or save the current customer's addresses |
| `GET` / `PATCH` / `DELETE` | `/api/accounts/addresses/<id>/` | Retrieve, update, or delete an owned address |
| `POST` | `/api/accounts/addresses/<id>/set-default/` | Set an owned address as default |
| `GET` | `/api/orders/checkout/` | Preview the current basket using current catalogue prices |
| `POST` | `/api/orders/checkout/` | Place an order from the current basket |
| `GET` | `/api/orders/` | List the signed-in customer's orders |
| `GET` | `/api/orders/<order_number>/` | Retrieve one of the customer's orders |
| `POST` | `/api/orders/<order_number>/cancel/` | Cancel an eligible order and restore its stock |
| `PATCH` | `/api/orders/<order_number>/status/` | Staff-only order status transition |

Checkout accepts only the saved address ID, payment method (`cod` or `online`), and optional customer notes. Product prices, totals, stock, and customer ownership are always read or checked on the server. Delivery is free for a subtotal of ₹499 or more; otherwise, a ₹40 delivery fee applies. There are no checkout discounts in this phase.

The order and each line item retain the delivery address, product name, SKU, image URL, unit price, quantity, and line total as order-time snapshots. Both payment methods start with payment status `pending`; selecting online does not charge a payment method or imply successful payment. Available inventory is deducted in the same database transaction that creates the order, for COD and online-pending orders alike. Cancelling an order in `pending` or `confirmed` restores the deducted stock exactly once; later statuses cannot be cancelled by the customer. Phase 9 must not deduct this stock again.

Staff can advance statuses only through the staff-only status endpoint along the sequence `pending` → `confirmed` → `processing` → `shipped` → `delivered`. Order totals, payment status, snapshots, and line items are read-only in Django admin. Address postal codes are validated as six-digit Indian PIN codes.

After adding these models, apply the new migrations with `python manage.py migrate` from `backend/`. Run the address and order API tests with `python manage.py test accounts.tests.CustomerAddressApiTests orders`.

## Razorpay payments

Online orders use Razorpay in INR. COD remains independent. Inventory is deducted during checkout for both methods; payment success does not deduct it again. Payment amounts always come from the saved order total, not from browser input.

Configure these values in the project-root `.env` file (never in a `VITE_*` variable or frontend file):

```dotenv
RAZORPAY_KEY_ID=rzp_test_your_key_id
RAZORPAY_KEY_SECRET=your_razorpay_key_secret
RAZORPAY_WEBHOOK_SECRET=your_razorpay_webhook_secret
```

Use the test-mode key ID and secret from the Razorpay Dashboard while developing. Do not paste credentials into chat or commit `.env`; `.env.example` contains placeholders only. If the variables are missing, checkout still creates the order, reports that payment is unavailable, and allows COD orders to continue.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `POST` | `/api/payments/create-order/` | Create/reuse a Razorpay order for an owned FreshBasket online order |
| `POST` | `/api/payments/verify/` | Verify the checkout signature and fetch authoritative payment status |
| `POST` | `/api/payments/webhook/` | Verify the raw-body webhook signature and process gateway events idempotently |
| `GET` | `/api/payments/order/<order_number>/` | Read payment status and retry eligibility for an owned order |

The React app receives only the public key ID and gateway order ID. Django verifies checkout signatures, fetches the payment from Razorpay, and marks an order paid only after a captured payment is confirmed. Webhooks use `X-Razorpay-Signature` and the configured webhook secret; event IDs prevent duplicate processing. Captures arriving after cancellation or after another successful payment are recorded as requiring refund/reconciliation and do not change the order back to paid. Staff must reconcile those cases in Razorpay.

For webhook testing, configure the Razorpay Dashboard to send `payment.authorized`, `payment.captured`, and `payment.failed` to `/api/payments/webhook/` on a reachable HTTPS environment. Do not use a real payment during automated tests; the backend payment tests mock Razorpay. Run:

```powershell
python backend\manage.py migrate
python backend\manage.py test payments
cd frontend
npm run build
npm run lint
```

## Product catalogue

The public catalogue API is mounted at `/api/catalog/`. It does not require customer authentication.

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/catalog/` | Catalogue endpoint index |
| `GET` | `/api/catalog/categories/` | Active categories with their active subcategories |
| `GET` | `/api/catalog/subcategories/` | Active subcategories; optionally filter with `?category=vegetables` |
| `GET` | `/api/catalog/brands/` | Active brands |
| `GET` | `/api/catalog/products/` | Active products, 20 per page |
| `GET` | `/api/catalog/products/<slug>/` | One active product by slug |

Product listing filters accept category, subcategory, and brand slugs or names, plus the following query parameters:

- `search`: search product name, SKU, description, brand, category, or subcategory.
- `category`, `subcategory`, `brand`: match a slug or name.
- `min_price`, `max_price`: inclusive selling-price bounds in INR.
- `in_stock`, `featured`, `bestseller`: `true`/`false` (also accepts `1`/`0` and `yes`/`no`).
- `ordering`: `name`, `selling_price`, `mrp`, or `created_at`; prefix a field with `-` for descending order.

For example:

```text
GET /api/catalog/products/?search=rice&category=rice-pulses&min_price=100&max_price=500&in_stock=true&ordering=selling_price
GET /api/catalog/products/?page=2
```

Product-list responses use this paginated shape; money and percentage values are decimal strings:

```json
{
  "count": 520,
  "next": "http://127.0.0.1:8000/api/catalog/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "sku": "FB-04-001",
      "name": "Sona Masoori Rice",
      "slug": "sona-masoori-rice-fb-04-001",
      "category": {"id": 4, "name": "Rice & Pulses", "slug": "rice-pulses"},
      "subcategory": {"id": 13, "name": "Rice", "slug": "rice"},
      "brand": {"id": 1, "name": "India Gate", "slug": "india-gate", "logo_url": ""},
      "description": "Indicative demo listing.",
      "short_description": "Everyday pantry staple.",
      "unit": "kg",
      "pack_size": "1 kg",
      "mrp": "100.00",
      "selling_price": "85.00",
      "discount_percentage": "15.00",
      "dietary_type": "vegetarian",
      "images": [
        {
          "id": 1,
          "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c",
          "alt_text": "Sona Masoori Rice",
          "is_primary": true
        }
      ],
      "stock_quantity": 25,
      "reserved_quantity": 0,
      "available_quantity": 25,
      "in_stock": true,
      "is_featured": true,
      "is_bestseller": true,
      "created_at": "2026-11-20T08:00:00Z",
      "updated_at": "2026-11-20T08:00:00Z"
    }
  ]
}
```

The response above illustrates the JSON shape; its IDs, prices, timestamps, stock, and page count are examples, not verified live catalogue values.

## Seeding and importing sample catalogue data

Run commands from the `backend/` directory:

```powershell
python manage.py migrate
python manage.py seed_categories
python manage.py import_products --file catalog/data/products.csv
```

`seed_categories` creates the 20 categories and their subcategories idempotently. The checked-in CSV contains 520 distinct sample products distributed across those categories. Product prices and stock are illustrative demo data, not current market quotes or verified availability. Importing uses SKU as the product key, creates missing inventory records without resetting existing stock on re-import, and upserts each product image by product and image URL. Invalid rows are reported with CSV line numbers; valid rows are committed, and the command exits with an error if any rows fail.

