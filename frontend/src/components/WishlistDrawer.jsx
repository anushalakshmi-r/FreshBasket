import { ArrowRight, Heart, LoaderCircle, ShoppingBasket, Trash2, X } from 'lucide-react'
import ImageWithFallback from './ImageWithFallback'
import SidePanel from './SidePanel'
import { getStockInfo } from '../utils/stock'

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

export default function WishlistDrawer({
  open,
  onClose,
  wishlistItems = [],
  isAuthenticated,
  isLoading,
  isBusy,
  error,
  onRetry,
  onSignIn,
  onAdd,
  onToggleWishlist,
}) {
  return (
    <SidePanel open={open} title="Your wishlist" onClose={onClose}>
      {isLoading ? (
        <div className="panel-empty" role="status">
          <span><LoaderCircle className="spin" size={25} /></span>
          <h3>Loading your wishlist…</h3>
        </div>
      ) : (
        <>
          {error && (
            <div className="catalogue-message catalogue-error" role="alert">
              <p>{error}</p>
              <button className="button button-secondary" type="button" onClick={onRetry}>
                Retry
              </button>
            </div>
          )}
          {wishlistItems.length ? (
            <div className="panel-items">
              {wishlistItems.map((item) => {
                const product = item.product
                const stockInfo = getStockInfo(product)
                const available = product.is_active !== false && stockInfo.inStock
                return (
                  <article className="panel-item" key={item.id}>
                    <ImageWithFallback
                      className="panel-product-image"
                      src={product.image_url}
                      alt={product.name}
                      optimize
                    />
                    <div className="panel-item-copy">
                      <span>{product.brand_name}</span>
                      <h3>{product.name}</h3>
                      <small>{product.pack_size}</small>
                      <strong>{currency.format(Number(product.selling_price))}</strong>
                      <small className={`product-stock ${stockInfo.className}`}>
                        <span />{stockInfo.text}
                      </small>
                      <div className="wishlist-item-actions">
                        <button
                          className="wishlist-add-button"
                          type="button"
                          disabled={!available || isBusy}
                          onClick={() => onAdd(String(product.id))}
                        >
                          <ShoppingBasket size={15} /> Add to basket
                        </button>
                        <button
                          className="wishlist-remove-button"
                          type="button"
                          disabled={isBusy}
                          onClick={() => onToggleWishlist(String(product.id))}
                          aria-label={`Remove ${product.name} from wishlist`}
                        >
                          <Trash2 size={15} /> Remove
                        </button>
                      </div>
                    </div>
                    <button
                      className="remove-item"
                      type="button"
                      aria-label={`Remove ${product.name} from wishlist`}
                      disabled={isBusy}
                      onClick={() => onToggleWishlist(String(product.id))}
                    ><X size={18} /></button>
                  </article>
                )
              })}
            </div>
          ) : (
            <div className="panel-empty">
              <span><Heart size={25} /></span>
              <h3>{isAuthenticated ? 'Save a little for later.' : 'Sign in to sync your wishlist.'}</h3>
              <p>
                {isAuthenticated
                  ? 'Tap the heart on any product to keep your favourites close.'
                  : 'Your favourites are saved to your customer account.'}
              </p>
              {isAuthenticated ? (
                <button className="button button-primary" type="button" onClick={onClose}>
                  Find your favourites <ArrowRight size={16} />
                </button>
              ) : (
                <button className="button button-primary" type="button" onClick={onSignIn}>Sign in</button>
              )}
            </div>
          )}
        </>
      )}
    </SidePanel>
  )
}
