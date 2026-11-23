import {
  ChevronDown,
  Heart,
  MapPin,
  Menu,
  Search,
  ShoppingBasket,
  UserRound,
  X,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

export default function Navbar({
  cartCount,
  wishlistCount,
  searchQuery,
  onCartClick,
  onWishlistClick,
  onSearch,
  onQueryChange,
  _onMessage,
  user,
  onNavigate,
  onLogout,
}) {
  const [showLocation, setShowLocation] = useState(false);
const [location, setLocation] = useState(localStorage.getItem("deliveryLocation") || "Select location");
const [locationSearch, setLocationSearch] = useState("");

const areas = ["Anna Nagar", "T. Nagar", "Velachery", "OMR", "Tambaram", "Porur", "Adyar", "Chennai", "Kodambakkam", "Mylapore"];

const filteredAreas = areas.filter(a => a.toLowerCase().includes(locationSearch.toLowerCase()));
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const [accountMenuOpen, setAccountMenuOpen] = useState(false)
  const [scrolled, setScrolled] = useState(false)
  const previousCartCount = useRef(cartCount)

  useEffect(() => {
    const updateScrolled = () => setScrolled(window.scrollY > 16)
    updateScrolled()
    window.addEventListener('scroll', updateScrolled, { passive: true })
    return () => window.removeEventListener('scroll', updateScrolled)
  }, [])

  useEffect(() => {
    if (cartCount > previousCartCount.current) {
      document.querySelector('.cart-button')?.classList.remove('cart-bump')
      requestAnimationFrame(() => document.querySelector('.cart-button')?.classList.add('cart-bump'))
    }
    previousCartCount.current = cartCount
  }, [cartCount])

  function submitSearch(event) {
    event.preventDefault()
    onSearch(searchQuery.trim())
    setMobileMenuOpen(false)
  }

  function navigate(event, path) {
    event.preventDefault()
    setMobileMenuOpen(false)
    setAccountMenuOpen(false)
    onNavigate(path)
  }

  return (
    <header className={`site-header${scrolled ? ' is-scrolled' : ''}`}>
      <div className="navbar page-shell">
        <a
          className="brand-lockup"
          href="/"
          onClick={(event) => navigate(event, '/')}
          aria-label="FreshBasket home"
        >
          <span className="brand-mark"><ShoppingBasket size={23} strokeWidth={2.2} /></span>
          <span className="brand-name">fresh<span>basket</span><small>GOOD FOOD, GOOD DAYS</small></span>
        </a>

        <button
          className="location-button"
          type="button"
          onClick={() => setShowLocation(true)}
          aria-label="Choose delivery location"
        >
          <MapPin size={18} aria-hidden="true" />
          <span><small>Delivery location</small><strong>{location}</strong></span>
        </button>

        <form className="search-form" role="search" onSubmit={submitSearch}>
          <Search size={19} aria-hidden="true" />
          <label className="sr-only" htmlFor="site-search">Search groceries</label>
          <input
            id="site-search"
            value={searchQuery}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search fruits, vegetables, pantry..."
          />
          {searchQuery && (
            <button
              className="search-clear"
              type="button"
              onClick={() => {
                onQueryChange('')
                onSearch('')
              }}
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
          <button className="search-submit" type="submit" aria-label="Submit search">
            Search
          </button>
        </form>

        <div className="navbar-actions">
          {user ? (
            <div className="account-dropdown">
              <button
                className="account-button"
                type="button"
                aria-expanded={accountMenuOpen}
                onClick={() => setAccountMenuOpen((open) => !open)}
              >
                <UserRound size={19} aria-hidden="true" />
                <span>{user.first_name || 'My account'}</span>
                <ChevronDown size={14} aria-hidden="true" />
              </button>
              {accountMenuOpen && (
                <div className="account-popover">
                  <a href="/account" onClick={(event) => navigate(event, '/account')}>My account</a>
                  <a href="/orders" onClick={(event) => navigate(event, '/orders')}>My orders</a>
                  <button
                    type="button"
                    onClick={() => {
                      setAccountMenuOpen(false)
                      onLogout()
                    }}
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="guest-actions">
              <a className="account-button" href="/login" onClick={(event) => navigate(event, '/login')}>
                <UserRound size={19} aria-hidden="true" />
                <span>Sign in</span>
              </a>
              <a className="register-link" href="/register" onClick={(event) => navigate(event, '/register')}>
                Join
              </a>
            </div>
          )}
          <button
            className="icon-button wishlist-nav-button"
            type="button"
            onClick={onWishlistClick}
            aria-label={`Open wishlist, ${wishlistCount} saved items`}
          >
            <Heart size={21} aria-hidden="true" />
            {wishlistCount > 0 && <span className="icon-count">{wishlistCount}</span>}
          </button>
          <button
            className="cart-button"
            type="button"
            onClick={onCartClick}
            aria-label={`Open basket, ${cartCount} items`}
          >
            <ShoppingBasket size={20} aria-hidden="true" />
            <span className="cart-label">Basket</span>
            <span className="cart-count">{cartCount}</span>
          </button>
          <a className="track-order-link" href="/track-order" onClick={(event) => navigate(event, '/track-order')}>
            Track Order
          </a>
          <button
            className="mobile-menu-button"
            type="button"
            aria-label={mobileMenuOpen ? 'Close menu' : 'Open menu'}
            aria-expanded={mobileMenuOpen}
            onClick={() => setMobileMenuOpen((open) => !open)}
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>
      </div>

      <div className={`mobile-search page-shell${mobileMenuOpen ? ' is-open' : ''}`}>
        <form className="search-form" role="search" onSubmit={submitSearch}>
          <Search size={19} aria-hidden="true" />
          <label className="sr-only" htmlFor="mobile-site-search">Search groceries</label>
          <input
            id="mobile-site-search"
            value={searchQuery}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search your everyday favourites"
          />
          <button className="search-submit" type="submit">Search</button>
        </form>
      </div>

      <nav className={`nav-links${mobileMenuOpen ? ' is-open' : ''}`} aria-label="Main navigation">
        <div className="page-shell nav-links-inner">
          <a
            href="/#categories"
            onClick={(event) => {
              if (window.location.pathname !== '/') {
                navigate(event, '/')
                setTimeout(() => document.getElementById('categories')?.scrollIntoView({ behavior: 'smooth' }), 100)
              } else {
                setMobileMenuOpen(false)
              }
            }}
          >
            Shop by category
          </a>
          <a
            href="/#products"
            onClick={(event) => {
              if (window.location.pathname !== '/') {
                navigate(event, '/')
                setTimeout(() => document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' }), 100)
              } else {
                setMobileMenuOpen(false)
              }
            }}
          >
            Best sellers
          </a>
          <a
            href="/#deals"
            onClick={(event) => {
              if (window.location.pathname !== '/') {
                navigate(event, '/')
                setTimeout(() => document.getElementById('deals')?.scrollIntoView({ behavior: 'smooth' }), 100)
              } else {
                setMobileMenuOpen(false)
              }
            }}
          >
            Today&apos;s deals
          </a>
          <a href="/our-story" onClick={(event) => navigate(event, '/our-story')}>Our story</a>
          <a href="/track-order" onClick={(event) => navigate(event, '/track-order')}>Track Order</a>
          <button
            className="mobile-account-link"
            type="button"
            onClick={() => {
              setMobileMenuOpen(false)
              onWishlistClick()
            }}
          >
            <Heart size={17} /> Wishlist{wishlistCount ? ` (${wishlistCount})` : ''}
          </button>
          {user ? (
            <>
              <button className="mobile-account-link" type="button" onClick={() => onNavigate('/account')}>
                <UserRound size={17} /> My account
              </button>
              <button className="mobile-account-link" type="button" onClick={() => onNavigate('/orders')}>
                <ShoppingBasket size={17} /> My orders
              </button>
              <button className="mobile-account-link" type="button" onClick={onLogout}>
                Sign out
              </button>
            </>
          ) : (
            <>
              <button className="mobile-account-link" type="button" onClick={() => onNavigate('/login')}>
                <UserRound size={17} /> Sign in
              </button>
              <button className="mobile-account-link" type="button" onClick={() => onNavigate('/register')}>
                Create account
              </button>
            </>
          )}
          {showLocation && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[100]" onClick={() => setShowLocation(false)}>
    <div className="bg-white p-6 rounded-2xl w-[380px] max-w-[90%]" onClick={(e) => e.stopPropagation()}>
      <div className="flex justify-between items-center mb-4">
        <h2 className="font-bold text-lg">Select Delivery Location</h2>
        <button onClick={() => setShowLocation(false)} className="text-xl">✕</button>
      </div>
      <input 
        placeholder="Search your area..." 
        value={locationSearch}
        onChange={(e) => setLocationSearch(e.target.value)}
        className="w-full border p-3 rounded-lg mb-3"
      />
      <div className="max-h-[250px] overflow-y-auto">
        {filteredAreas.map(area => (
          <button key={area} className="block w-full text-left p-3 hover:bg-green-100 rounded-lg font-medium"
            onClick={() => {
              setLocation(area);
              localStorage.setItem("deliveryLocation", area);
              setShowLocation(false);
            }}>
            📍 {area}
          </button>
        ))}
      </div>
    </div>
  </div>
)}
        </div>
      </nav>
    </header>
  )
}
