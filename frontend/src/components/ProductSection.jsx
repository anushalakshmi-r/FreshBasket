import { ArrowRight, LoaderCircle, SearchX } from 'lucide-react'
import ProductCard from './ProductCard'

function ProductFilters({ filters, categories, brands, onChange, onClear }) {
  const subcategories = categories.find((category) => category.slug === filters.category)?.subcategories ?? []

  function update(event) {
    onChange(event.target.name, event.target.value)
  }

  return (
    <form className="catalogue-filters" aria-label="Filter products" onSubmit={(event) => event.preventDefault()}>
      <label className="catalogue-filter">
        <span>Category</span>
        <select name="category" value={filters.category} onChange={update}>
          <option value="">All categories</option>
          {categories.map((category) => (
            <option value={category.slug} key={category.slug}>{category.name}</option>
          ))}
        </select>
      </label>
      <label className="catalogue-filter">
        <span>Subcategory</span>
        <select
          name="subcategory"
          value={filters.subcategory}
          onChange={update}
          disabled={!subcategories.length}
        >
          <option value="">All subcategories</option>
          {subcategories.map((subcategory) => (
            <option value={subcategory.slug} key={subcategory.slug}>{subcategory.name}</option>
          ))}
        </select>
      </label>
      <label className="catalogue-filter">
        <span>Brand</span>
        <select name="brand" value={filters.brand} onChange={update}>
          <option value="">All brands</option>
          {brands.map((brand) => (
            <option value={brand.slug} key={brand.slug}>{brand.name}</option>
          ))}
        </select>
      </label>
      <label className="catalogue-filter">
        <span>Min price (₹)</span>
        <input
          name="min_price"
          type="number"
          min="0"
          step="0.01"
          inputMode="decimal"
          value={filters.min_price}
          onChange={update}
          placeholder="No minimum"
        />
      </label>
      <label className="catalogue-filter">
        <span>Max price (₹)</span>
        <input
          name="max_price"
          type="number"
          min="0"
          step="0.01"
          inputMode="decimal"
          value={filters.max_price}
          onChange={update}
          placeholder="No maximum"
        />
      </label>
      <label className="catalogue-filter">
        <span>Availability</span>
        <select name="in_stock" value={filters.in_stock} onChange={update}>
          <option value="">Any stock status</option>
          <option value="true">In stock</option>
          <option value="false">Out of stock</option>
        </select>
      </label>
      <label className="catalogue-filter">
        <span>Featured</span>
        <select name="featured" value={filters.featured} onChange={update}>
          <option value="">Any</option>
          <option value="true">Featured only</option>
          <option value="false">Not featured</option>
        </select>
      </label>
      <label className="catalogue-filter">
        <span>Best sellers</span>
        <select name="bestseller" value={filters.bestseller} onChange={update}>
          <option value="">All products</option>
          <option value="true">Best sellers only</option>
          <option value="false">Other products</option>
        </select>
      </label>
      <label className="catalogue-filter">
        <span>Sort by</span>
        <select name="ordering" value={filters.ordering} onChange={update}>
          <option value="">Recommended</option>
          <option value="name">Name: A to Z</option>
          <option value="-name">Name: Z to A</option>
          <option value="selling_price">Price: Low to high</option>
          <option value="-selling_price">Price: High to low</option>
          <option value="mrp">MRP: Low to high</option>
          <option value="-mrp">MRP: High to low</option>
          <option value="-created_at">Recently added</option>
        </select>
      </label>
      <button className="filter-clear" type="button" onClick={onClear}>Clear filters</button>
    </form>
  )
}

function LoadingProducts() {
  return (
    <div className="product-grid product-grid-skeleton" aria-label="Loading products" role="status">
      {Array.from({ length: 8 }, (_, index) => (
        <div className="product-skeleton" key={index}>
          <span />
          <div><i /><i /><i /></div>
        </div>
      ))}
    </div>
  )
}

export default function ProductSection({
  id,
  title,
  description,
  products,
  cart,
  wishlist,
  onAdd,
  onQuantityChange,
  onToggleWishlist,
  cartBusy = false,
  wishlistBusy = false,
  isDeals = false,
  action,
  onAction,
  filters,
  categories = [],
  brands = [],
  onFilterChange,
  onClearFilters,
  loading = false,
  error = '',
  onRetry,
  loadingMore = false,
  loadMoreError = '',
  onRetryLoadMore,
  canLoadMore = false,
  onLoadMore,
  resultCount,
  emptyTitle = 'No matching products just yet',
  emptyMessage = 'Try another search or explore all of our fresh picks.',
}) {
  return (
    <section className={`section-block product-section${isDeals ? ' deals-section' : ''}`} id={id}>
      <div className="page-shell">
        <div className="section-heading">
          <div>
            <span className="section-kicker">{isDeals ? 'GOOD FINDS, BETTER PRICES' : 'A FEW OF OUR FAVOURITES'}</span>
            <h2>{title}</h2>
            {description && <p>{description}</p>}
          </div>
          {action && (
            <button className="text-link text-button" type="button" onClick={onAction}>
              {action} <ArrowRight size={16} />
            </button>
          )}
        </div>

        {filters && (
          <ProductFilters
            filters={filters}
            categories={categories}
            brands={brands}
            onChange={onFilterChange}
            onClear={onClearFilters}
          />
        )}

        {loading ? (
          <LoadingProducts />
        ) : error ? (
          <div className="catalogue-message catalogue-error" role="alert">
            <SearchX size={25} aria-hidden="true" />
            <h3>We couldn&apos;t load these products.</h3>
            <p>{error}</p>
            <button className="button button-secondary" type="button" onClick={onRetry}>Retry</button>
          </div>
        ) : products.length ? (
          <>
            {Number.isFinite(resultCount) && (
              <p className="catalogue-result-count" aria-live="polite">
                Showing {products.length} of {resultCount} products
              </p>
            )}
            <div className="product-grid">
              {products.map((product) => (
                <ProductCard
                  key={product.id}
                  product={product}
                  quantity={cart[product.id] ?? 0}
                  isWishlisted={wishlist.has(product.id)}
                  onAdd={onAdd}
                  onQuantityChange={onQuantityChange}
                  onToggleWishlist={onToggleWishlist}
                  cartBusy={cartBusy}
                  wishlistBusy={wishlistBusy}
                />
              ))}
            </div>
            {loadMoreError && (
              <div className="catalogue-message catalogue-error" role="alert">
                <p>{loadMoreError}</p>
                <button className="button button-secondary" type="button" onClick={onRetryLoadMore}>
                  Retry loading more
                </button>
              </div>
            )}
            {canLoadMore && !loadMoreError && (
              <div className="load-more-wrap">
                <button
                  className="button button-secondary load-more-button"
                  type="button"
                  onClick={onLoadMore}
                  disabled={loadingMore}
                >
                  {loadingMore ? <><LoaderCircle className="spin" size={16} /> Loading more…</> : 'Load more products'}
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="empty-products">
            <SearchX size={28} aria-hidden="true" />
            <h3>{emptyTitle}</h3>
            <p>{emptyMessage}</p>
            {onClearFilters && (
              <button className="button button-secondary" type="button" onClick={onClearFilters}>
                Clear filters
              </button>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
