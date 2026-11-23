import { ArrowRight, Leaf } from 'lucide-react'
import BrandSection from '../components/BrandSection'
import CategorySection from '../components/CategorySection'
import HeroSection from '../components/HeroSection'
import Newsletter from '../components/Newsletter'
import ProductSection from '../components/ProductSection'
import PromoBanner from '../components/PromoBanner'

const banners = [
  {
    kicker: 'STRAIGHT FROM THE FARM',
    title: 'A brighter kind of fresh.',
    description: 'Colourful produce, grown with care and picked for your table.',
    action: 'Explore vegetables',
    target: 'vegetables',
    theme: 'promo-green',
    image: 'https://images.unsplash.com/photo-1540420773420-3366772f4999?auto=format&fit=crop&w=800&q=85',
  },
  {
    kicker: 'THE EVERYDAY EDIT',
    title: 'Little things, well stocked.',
    description: 'Pantry and home essentials for all the in-between moments.',
    action: 'Shop essentials',
    target: 'household-essentials',
    theme: 'promo-cream',
    image: 'https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=800&q=85',
  },
  {
    kicker: 'A REASON TO GATHER',
    title: 'Make weekends delicious.',
    description: 'A few special finds to make your next meal memorable.',
    action: 'See weekend picks',
    target: 'deals',
    theme: 'promo-yellow',
    image: 'https://images.unsplash.com/photo-1490645935967-10de6ba17061?auto=format&fit=crop&w=800&q=85',
  },
]

export default function Home({
  cart,
  wishlist,
  categories,
  categoriesLoading,
  categoriesError,
  brands,
  brandsLoading,
  brandsError,
  products,
  deals,
  recommendations,
  shelvesLoading,
  shelvesError,
  filters,
  productTitle,
  productDescription,
  emptyTitle,
  emptyMessage,
  resultCount,
  productsLoading,
  productsError,
  loadingMore,
  loadMoreError,
  hasNextPage,
  onSelectCategory,
  onFilterChange,
  onClearFilters,
  onRetryProducts,
  onRetryLoadMore,
  onLoadMore,
  onRetryCategories,
  onRetryBrands,
  onRetryShelves,
  onSelectBrand,
  onAdd,
  onQuantityChange,
  onToggleWishlist,
  cartBusy,
  wishlistBusy,
}) {
  function scrollToProducts() {
    document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' })
  }

  function selectCategory(category) {
    onSelectCategory(category.id)
    requestAnimationFrame(scrollToProducts)
  }

  function runPromo(target) {
    if (target === 'deals') {
      document.getElementById('deals')?.scrollIntoView({ behavior: 'smooth' })
      return
    }

    if (categories.some((category) => category.slug === target)) {
      onSelectCategory(target)
      requestAnimationFrame(scrollToProducts)
    }
  }

  return (
    <main>
      <div id="top" className="page-shell hero-shell">
        <HeroSection onShopNow={scrollToProducts} />
      </div>
      <div className="trust-strip" data-reveal>
        <div className="page-shell trust-strip-inner">
          <span><Leaf size={17} /> Picked fresh, packed thoughtfully</span>
          <span>Good food, no guesswork</span>
          <span>Everyday favourites, a little more considered</span>
        </div>
      </div>
      <CategorySection
        categories={categories}
        loading={categoriesLoading}
        error={categoriesError}
        onRetry={onRetryCategories}
        onSelect={selectCategory}
      />
      <section className="promo-section page-shell" aria-label="FreshBasket promotions" data-reveal>
        <div className="promo-grid">
          {banners.map((banner) => (
            <PromoBanner key={banner.title} banner={banner} onAction={runPromo} />
          ))}
        </div>
      </section>
      <ProductSection
        id="products"
        title={productTitle}
        description={productDescription}
        products={products}
        cart={cart}
        wishlist={wishlist}
        onAdd={onAdd}
        onQuantityChange={onQuantityChange}
        onToggleWishlist={onToggleWishlist}
        cartBusy={cartBusy}
        wishlistBusy={wishlistBusy}
        filters={filters}
        categories={categories}
        brands={brands}
        onFilterChange={onFilterChange}
        onClearFilters={onClearFilters}
        loading={productsLoading}
        error={productsError}
        onRetry={onRetryProducts}
        loadingMore={loadingMore}
        loadMoreError={loadMoreError}
        onRetryLoadMore={onRetryLoadMore}
        canLoadMore={hasNextPage}
        onLoadMore={onLoadMore}
        resultCount={resultCount}
        emptyTitle={emptyTitle}
        emptyMessage={emptyMessage}
      />
      <ProductSection
        id="deals"
        title="A good deal, right on time."
        description="Discounts shown on products in the live catalogue."
        products={deals}
        cart={cart}
        wishlist={wishlist}
        onAdd={onAdd}
        onQuantityChange={onQuantityChange}
        onToggleWishlist={onToggleWishlist}
        cartBusy={cartBusy}
        wishlistBusy={wishlistBusy}
        isDeals
        loading={shelvesLoading}
        error={shelvesError}
        onRetry={onRetryShelves}
      />
      <section className="story-banner page-shell" data-reveal>
        <div className="story-mark"><Leaf size={21} /></div>
        <div>
          <span className="section-kicker">MORE THAN A GROCERY RUN</span>
          <h2>Good food has a way of bringing us together.</h2>
        </div>
        <a className="button button-light" href="#about">A little about us <ArrowRight size={16} /></a>
      </section>
      <ProductSection
        id="recommendations"
        title="A little something for later."
        description="Featured products from the FreshBasket catalogue."
        products={recommendations}
        cart={cart}
        wishlist={wishlist}
        onAdd={onAdd}
        onQuantityChange={onQuantityChange}
        onToggleWishlist={onToggleWishlist}
        cartBusy={cartBusy}
        wishlistBusy={wishlistBusy}
        loading={shelvesLoading}
        error={shelvesError}
        onRetry={onRetryShelves}
      />
      <BrandSection
        brands={brands}
        loading={brandsLoading}
        error={brandsError}
        onRetry={onRetryBrands}
        onSelectBrand={onSelectBrand}
      />
      <Newsletter />
    </main>
  )
}
