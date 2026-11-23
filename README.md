# FreshBasket

FreshBasket is a React/Vite grocery storefront backed by Django REST Framework. The existing catalogue, cart, wishlist, address book, COD checkout, Razorpay test checkout, authentication, order history, inventory checks, and responsive motion system are preserved on `feature/final-requirements`.

## Stack and layout

- `frontend/`: React, Vite, Lucide icons, CSS motion system.
- `backend/`: Django REST Framework apps for accounts, catalogue, cart, orders, payments, and reviews.
- SQLite is used automatically when no database variables are present; local MySQL and Render `DATABASE_URL` remain supported.

## Local setup

1. Create and activate a Python environment, then install `requirements.txt`.
2. Copy `.env.example` to `.env` and set a strong `DJANGO_SECRET_KEY`.
3. Configure either `DATABASE_URL` or the `DB_*` MySQL variables.
4. Run `cd backend; python manage.py migrate; python manage.py runserver`.
5. Run `cd frontend; npm install; npm run dev`.

## Environment variables

Required in deployment: `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, and either `DATABASE_URL` or `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

Razorpay remains test-only: set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` to `rzp_test_*` credentials and never expose the secret to Vercel. Password reset email uses `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`, `DEFAULT_FROM_EMAIL`, `PASSWORD_RESET_TIMEOUT`, and `FRONTEND_URL`. The console backend is safe for local development.

## API additions

- `POST /api/accounts/password-reset/` and `POST /api/accounts/password-reset/confirm/`
- `GET|POST /api/reviews/products/<product_id>/`, `PATCH|DELETE /api/reviews/<review_id>/`
- Admin-only `GET /api/admin/dashboard/`
- Admin-only CRUD: `/api/admin/categories/`, `/api/admin/products/`, `/api/admin/coupons/`
- Order responses now include `status_history`; valid delivery states include `packed` and `out_for_delivery`.

The Django admin at `/admin/` remains available for complete product image, inventory, user, order, category, coupon, and review management. Create an administrator with `python manage.py createsuperuser`.

## Testing

Use an isolated SQLite database in CI or local verification:

```powershell
$env:USE_SQLITE_FOR_TESTS='1'
python backend/manage.py check
python backend/manage.py makemigrations --check --dry-run
python backend/manage.py test accounts catalog orders payments reviews
cd frontend; npm run lint; npm run build
```

## Safe deployment and rollback

The branch is based on production commit `e487281`; merge it only after reviewing migration `backend/orders/migrations/0002_coupon_order_coupon_code_alter_order_order_status_and_more.py` and `backend/reviews/migrations/0001_initial.py`. Take a provider-native database backup before running `migrate` in Render. Add new environment variables in Render/Vercel first, deploy the backend, run migrations, then deploy the frontend. Keep the current API URL `https://freshbasket-backend-emtv.onrender.com/api`.

Rollback: stop promotion, redeploy the previous `e487281` build, and restore the pre-migration database backup if the new schema must be removed. Do not use destructive migration commands against production.

Suggested merge commands:

```bash
git fetch origin
git checkout main
git pull --ff-only origin main
git merge --no-ff feature/final-requirements
git push origin main
```

This branch does not perform a production deployment, alter production credentials, or apply production migrations.
