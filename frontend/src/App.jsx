import { useCallback, useEffect, useRef, useState } from 'react'
import AnnouncementBar from './components/AnnouncementBar'
import CartDrawer from './components/CartDrawer'
import ChatBot from './components/ChatBot'
import Footer from './components/Footer'
import Navbar from './components/Navbar'
import WishlistDrawer from './components/WishlistDrawer'
import { useAuth } from './context/useAuth'
import { getBrands, getCategories, getProducts } from './services/api'
import { useCart } from './hooks/useCart'
import { useWishlist } from './hooks/useWishlist'
import { AccountPage, LoginPage, RegisterPage } from './pages/AuthPages'
import {
  CheckoutPage,
  OrderConfirmationPage,
  OrderDetailPage,
  OrdersPage,
} from './pages/OrdersPages'
import Home from './pages/Home'
import InfoPage from './pages/InfoPage'
import { INFO_PAGE_MAP } from './data/infoPages'

const initialFilters = {
  category: '',
  subcategory: '',
  brand: '',
  min_price: '',
  max_price: '',
  in_stock: '',
  featured: '',
  bestseller: 'true',
  ordering: '',
}

const emptyFilters = Object.fromEntries(
  Object.keys(initialFilters).map((key) => [key, '']),
)

function appendUniqueProducts(current, incoming) {
  const ids = new Set(current.map((product) => product.id))
  return [...current, ...incoming.filter((product) => !ids.has(product.id))]
}

function mergeProductDirectory(current, incoming) {
  const productsById = new Map(current.map((product) => [product.id, product]))
  incoming.forEach((product) => productsById.set(product.id, product))
  return Array.from(productsById.values())
}

function withChatBot(page) {
  return <>{page}<ChatBot /></>
}

export default function App() {
  const { logout, user, isAuthenticated } = useAuth()
  const {
    cart,
    cartData,
    cartItems,
    itemCount,
    isLoading: cartLoading,
    isMutating: cartBusy,
    error: cartError,
    addItem,
    updateQuantity,
    removeItem,
    clear: clearCart,
    refresh: refreshCart,
    clearLocal: clearCartLocal,
  } = useCart()
  const {
    wishlist,
    wishlistItems,
    isLoading: wishlistLoading,
    isMutating: wishlistBusy,
    error: wishlistError,
    toggleWishlist,
    refresh: refreshWishlist,
    clearLocal: clearWishlistLocal,
  } = useWishlist()
  const [pathname, setPathname] = useState(() => window.location.pathname.replace(/\/+$/, '') || '/')
  const [routeMessage, setRouteMessage] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [debouncedSearch, setDebouncedSearch] = useState('')
  const [filters, setFilters] = useState(initialFilters)
  const [categories, setCategories] = useState([])
  const [categoriesLoading, setCategoriesLoading] = useState(true)
  const [categoriesError, setCategoriesError] = useState('')
  const [brands, setBrands] = useState([])
  const [brandsLoading, setBrandsLoading] = useState(true)
  const [brandsError, setBrandsError] = useState('')
  const [products, setProducts] = useState([])
  const [productDirectory, setProductDirectory] = useState([])
  const [resultCount, setResultCount] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [hasNextPage, setHasNextPage] = useState(false)
  const [productsLoading, setProductsLoading] = useState(true)
  const [productsError, setProductsError] = useState('')
  const [productsRetry, setProductsRetry] = useState(0)
  const [loadingMore, setLoadingMore] = useState(false)
  const [loadMoreError, setLoadMoreError] = useState('')
  const [deals, setDeals] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [shelvesLoading, setShelvesLoading] = useState(true)
  const [shelvesError, setShelvesError] = useState('')
  const [shelvesRetry, setShelvesRetry] = useState(0)
  const [metaRetry, setMetaRetry] = useState(0)
  const [activePanel, setActivePanel] = useState('')
  const [notice, setNotice] = useState('')
  const requestVersion = useRef(0)
  const loadMoreController = useRef(null)
  const isStorefront = !(
    ['/login', '/register', '/account', '/checkout', '/orders'].includes(pathname)
    || pathname.startsWith('/orders/')
    || pathname.startsWith('/order-confirmation/')
  )

  useEffect(() => {
    function syncPathname() {
      setPathname(window.location.pathname.replace(/\/+$/, '') || '/')
    }

    window.addEventListener('popstate', syncPathname)
    return () => window.removeEventListener('popstate', syncPathname)
  }, [])

  const navigate = useCallback((path) => {
    const nextPath = path.replace(/\/+$/, '') || '/'
    if (window.location.pathname !== nextPath) window.history.pushState({}, '', nextPath)
    setPathname(nextPath)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  const handleAuthSuccess = useCallback((message) => {
    setRouteMessage(message)
    navigate('/account')
  }, [navigate])

  const handleLogout = useCallback(async () => {
    clearCartLocal()
    clearWishlistLocal()
    try {
      await logout()
      setNotice('You have signed out.')
    } catch (error) {
      setNotice(`You are signed out on this device. ${error.message}`)
    }
    navigate('/')
  }, [clearCartLocal, clearWishlistLocal, logout, navigate])

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      const nextSearch = searchQuery.trim()
      if (nextSearch !== debouncedSearch) {
        setProductsLoading(true)
        setProductsError('')
        setLoadMoreError('')
        setLoadingMore(false)
        setDebouncedSearch(nextSearch)
      }
    }, 350)
    return () => window.clearTimeout(timeout)
  }, [searchQuery, debouncedSearch])

  useEffect(() => {
    if (!isStorefront) return undefined

    const controller = new AbortController()

    getCategories({ signal: controller.signal })
      .then(setCategories)
      .catch((error) => {
        if (error.name !== 'AbortError') setCategoriesError(error.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setCategoriesLoading(false)
      })

    getBrands({ signal: controller.signal })
      .then(setBrands)
      .catch((error) => {
        if (error.name !== 'AbortError') setBrandsError(error.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setBrandsLoading(false)
      })

    return () => controller.abort()
  }, [isStorefront, metaRetry])

  useEffect(() => {
    if (!isStorefront) return undefined

    const controller = new AbortController()
    const version = ++requestVersion.current
    loadMoreController.current?.abort()
    const requestFilters = debouncedSearch ? { ...filters, bestseller: '' } : filters

    getProducts({ ...requestFilters, search: debouncedSearch, page: 1 }, { signal: controller.signal })
      .then((response) => {
        if (version !== requestVersion.current) return
        setProducts(response.results)
        setProductDirectory((current) => mergeProductDirectory(current, response.results))
        setResultCount(response.count)
        setCurrentPage(1)
        setHasNextPage(Boolean(response.next))
      })
      .catch((error) => {
        if (error.name !== 'AbortError' && version === requestVersion.current) {
          setProductsError(error.message)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted && version === requestVersion.current) {
          setProductsLoading(false)
        }
      })

    return () => controller.abort()
  }, [filters, debouncedSearch, isStorefront, productsRetry])

  useEffect(() => {
    if (!isStorefront) return undefined

    const controller = new AbortController()

    Promise.all([
      getProducts({ page: 1 }, { signal: controller.signal }),
      getProducts({ featured: 'true', page: 1 }, { signal: controller.signal }),
    ])
      .then(([catalogue, featured]) => {
        if (controller.signal.aborted) return
        const discountedProducts = catalogue.results
          .filter((product) => product.discount > 0)
          .slice(0, 8)
        setDeals(discountedProducts)
        setRecommendations(featured.results)
        setProductDirectory((current) => mergeProductDirectory(
          current,
          [...catalogue.results, ...featured.results],
        ))
      })
      .catch((error) => {
        if (error.name !== 'AbortError') setShelvesError(error.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setShelvesLoading(false)
      })

    return () => controller.abort()
  }, [isStorefront, shelvesRetry])

  useEffect(() => {
    if (!notice) return undefined

    const timeout = window.setTimeout(() => setNotice(''), 2800)
    return () => window.clearTimeout(timeout)
  }, [notice])

  function prepareProductsRequest() {
    setProductsLoading(true)
    setProductsError('')
    setLoadMoreError('')
    setLoadingMore(false)
    loadMoreController.current?.abort()
  }

  function retryMeta() {
    setCategoriesLoading(true)
    setBrandsLoading(true)
    setCategoriesError('')
    setBrandsError('')
    setMetaRetry((value) => value + 1)
  }

  function retryShelves() {
    setShelvesLoading(true)
    setShelvesError('')
    setShelvesRetry((value) => value + 1)
  }

  async function handleAdd(productId) {
    if (!isAuthenticated) {
      setNotice('Sign in to save products to your basket.')
      navigate('/login')
      return
    }
    const product = productDirectory.find((item) => item.id === productId)
    if (product && !product.inStock) {
      setNotice('This product is currently out of stock.')
      return
    }

    try {
      await addItem(productId)
      setNotice(`${product?.name ?? 'Product'} added to your basket.`)
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function handleQuantityChange(productId, quantity) {
    try {
      await updateQuantity(productId, quantity)
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function handleRemoveCartItem(productId) {
    try {
      await removeItem(productId)
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function handleClearCart() {
    try {
      await clearCart()
      setNotice('Your basket has been cleared.')
    } catch (error) {
      setNotice(error.message)
    }
  }

  async function handleToggleWishlist(productId) {
    if (!isAuthenticated) {
      setNotice('Sign in to save products to your wishlist.')
      navigate('/login')
      return
    }
    try {
      await toggleWishlist(productId)
    } catch (error) {
      setNotice(error.message)
    }
  }

  function handleSignIn() {
    setActivePanel('')
    navigate('/login')
  }

  function handleSearch(query) {
    const trimmedQuery = query.trim()
    setSearchQuery(query)
    if (trimmedQuery) {
      if (pathname !== '/') navigate('/')
      requestAnimationFrame(() => document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' }))
    }
  }

  function handleSelectCategory(categoryId) {
    if (!categories.some((category) => category.id === categoryId)) return
    prepareProductsRequest()
    setSearchQuery('')
    setDebouncedSearch('')
    setFilters((current) => ({
      ...current,
      category: categoryId,
      subcategory: '',
      bestseller: '',
    }))
  }

  function handleFilterChange(name, value) {
    prepareProductsRequest()
    setFilters((current) => ({
      ...current,
      [name]: value,
      ...(name === 'category' ? { subcategory: '' } : {}),
    }))
  }

  function clearFilters() {
    prepareProductsRequest()
    setSearchQuery('')
    setDebouncedSearch('')
    setFilters(emptyFilters)
    requestAnimationFrame(() => document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' }))
  }

  function retryProducts() {
    prepareProductsRequest()
    setProductsRetry((value) => value + 1)
  }

  function loadMore() {
    if (!hasNextPage || loadingMore) return
    const version = requestVersion.current
    const controller = new AbortController()
    loadMoreController.current?.abort()
    loadMoreController.current = controller
    setLoadingMore(true)
    setLoadMoreError('')

    getProducts({
      ...filters,
      search: debouncedSearch,
      page: currentPage + 1,
    }, { signal: controller.signal })
      .then((response) => {
        if (version !== requestVersion.current) return
        setProducts((current) => appendUniqueProducts(current, response.results))
        setProductDirectory((current) => mergeProductDirectory(current, response.results))
        setCurrentPage((page) => page + 1)
        setHasNextPage(Boolean(response.next))
      })
      .catch((error) => {
        if (error.name !== 'AbortError' && version === requestVersion.current) {
          setLoadMoreError(error.message)
        }
      })
      .finally(() => {
        if (version === requestVersion.current) setLoadingMore(false)
      })
  }

  const onlyBestSellers = filters.bestseller === 'true'
    && !Object.entries(filters).some(([key, value]) => key !== 'bestseller' && value)
    && !debouncedSearch
  const categoryName = categories.find((category) => category.slug === filters.category)?.name
  const productTitle = debouncedSearch
    ? `Fresh finds for “${debouncedSearch}”`
    : categoryName
      ? `Shop ${categoryName.toLowerCase()}`
      : onlyBestSellers
        ? 'A few favourites, picked for you'
        : 'Fresh picks from our catalogue'
  const productDescription = debouncedSearch
    ? 'Search results from the FreshBasket catalogue.'
    : categoryName
      ? 'Explore products from this category, straight from the catalogue.'
      : 'Everyday goodness, from our shelves to your kitchen.'
  const emptyTitle = debouncedSearch
    ? 'No search results found'
    : filters.category
      ? 'No products in this category yet'
      : 'No products match these filters'
  const emptyMessage = debouncedSearch
    ? 'Try another product name, brand, SKU or category.'
    : 'Try clearing a filter or exploring another category.'

  const infoSlug = INFO_PAGE_MAP[pathname] || (pathname.startsWith('/info/') ? pathname.slice('/info/'.length) : null)

  if (pathname === '/login') {
    return withChatBot(<LoginPage onNavigate={navigate} onSuccess={handleAuthSuccess} />)
  }

  if (pathname === '/register') {
    return withChatBot(<RegisterPage onNavigate={navigate} onSuccess={handleAuthSuccess} />)
  }

  if (pathname === '/account') {
    return withChatBot(
      <>
    <AccountPage
      message={routeMessage}
      onNavigate={navigate}
      onLogout={handleLogout}
    />
      </>,
    )
  }

  if (pathname === '/checkout') {
    return withChatBot(
      <>
      <CheckoutPage
        onNavigate={navigate}
        onOrderPlaced={refreshCart}
      />
      </>,
    )
  }

  if (pathname === '/orders' || pathname === '/track-order') {
    return withChatBot(<OrdersPage onNavigate={navigate} />)
  }

  if (pathname.startsWith('/order-confirmation/')) {
    const orderNumber = decodeURIComponent(pathname.slice('/order-confirmation/'.length))
    return withChatBot(<OrderConfirmationPage orderNumber={orderNumber} onNavigate={navigate} />)
  }

  if (pathname.startsWith('/orders/')) {
    const orderNumber = decodeURIComponent(pathname.slice('/orders/'.length))
    return withChatBot(<OrderDetailPage orderNumber={orderNumber} onNavigate={navigate} />)
  }

  return (
    <>
      <AnnouncementBar />
      <Navbar
        cartCount={itemCount}
        wishlistCount={wishlist.size}
        searchQuery={searchQuery}
        onQueryChange={setSearchQuery}
        onCartClick={() => setActivePanel('cart')}
        onWishlistClick={() => setActivePanel('wishlist')}
        onSearch={handleSearch}
        onMessage={setNotice}
        user={user}
        onNavigate={navigate}
        onLogout={handleLogout}
      />
      {infoSlug ? (
        <InfoPage slug={infoSlug} onNavigate={navigate} />
      ) : (
        <Home
          cart={cart}
          wishlist={wishlist}
          categories={categories}
          categoriesLoading={categoriesLoading}
          categoriesError={categoriesError}
          brands={brands}
          brandsLoading={brandsLoading}
          brandsError={brandsError}
          products={products}
          deals={deals}
          recommendations={recommendations}
          shelvesLoading={shelvesLoading}
          shelvesError={shelvesError}
          filters={filters}
          productTitle={productTitle}
          productDescription={productDescription}
          emptyTitle={emptyTitle}
          emptyMessage={emptyMessage}
          resultCount={resultCount}
          productsLoading={productsLoading}
          productsError={productsError}
          loadingMore={loadingMore}
          loadMoreError={loadMoreError}
          hasNextPage={hasNextPage}
          onSelectCategory={handleSelectCategory}
          onFilterChange={handleFilterChange}
          onClearFilters={clearFilters}
          onRetryProducts={retryProducts}
          onRetryLoadMore={loadMore}
          onLoadMore={loadMore}
          onRetryCategories={retryMeta}
          onRetryBrands={retryMeta}
          onRetryShelves={retryShelves}
          onSelectBrand={(brand) => {
            prepareProductsRequest()
            setFilters((current) => ({ ...current, brand, bestseller: '' }))
            requestAnimationFrame(() => document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' }))
          }}
          onAdd={handleAdd}
          onQuantityChange={handleQuantityChange}
          onToggleWishlist={handleToggleWishlist}
          cartBusy={cartBusy}
          wishlistBusy={wishlistBusy}
        />
      )}
      <Footer onNavigate={navigate} />
      <CartDrawer
        open={activePanel === 'cart'}
        onClose={() => setActivePanel('')}
        cartItems={cartItems}
        cartData={cartData}
        isAuthenticated={isAuthenticated}
        isLoading={cartLoading}
        isBusy={cartBusy}
        error={cartError}
        onRetry={refreshCart}
        onSignIn={handleSignIn}
        onClear={handleClearCart}
        onCheckout={() => {
          setActivePanel('')
          navigate('/checkout')
        }}
        onQuantityChange={handleQuantityChange}
        onRemove={handleRemoveCartItem}
      />
      <WishlistDrawer
        open={activePanel === 'wishlist'}
        onClose={() => setActivePanel('')}
        wishlistItems={wishlistItems}
        isAuthenticated={isAuthenticated}
        isLoading={wishlistLoading}
        isBusy={wishlistBusy}
        error={wishlistError}
        onRetry={refreshWishlist}
        onSignIn={handleSignIn}
        onAdd={handleAdd}
        onToggleWishlist={handleToggleWishlist}
      />
      <ChatBot />
      {notice && <div className="toast-message" role="status">{notice}</div>}
    </>
  )
}
