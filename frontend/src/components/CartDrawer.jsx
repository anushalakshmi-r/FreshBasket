import { ArrowRight, LoaderCircle, Minus, Plus, ShoppingBasket, Trash2 } from 'lucide-react'
import ImageWithFallback from './ImageWithFallback'
import SidePanel from './SidePanel'

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

export default function CartDrawer({
  open,
  onClose,
  cartItems = [],
  cartData,
  isAuthenticated,
  isLoading,
  isBusy,
  error,
  onRetry,
  onSignIn,
  onClear,
  onCheckout,
  onQuantityChange,
  onRemove,
}) {
  return (
    <SidePanel open={open} title="Your basket" onClose={onClose}>
      {isLoading ? (
        <div className="panel-empty" role="status">
          <span><LoaderCircle className="spin" size={25} /></span>
          <h3>Loading your basket…</h3>
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
          {cartItems.length ? (
            <>
              <div className="panel-items">
                {cartItems.map((item) => {
                  const product = item.product
                  const unavailable = !product.is_active || product.available_stock <= 0
                  const exceedsStock = item.quantity > product.available_stock
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
                        {unavailable ? (
                          <small className="product-stock is-out-of-stock">This product is unavailable.</small>
                        ) : exceedsStock ? (
                          <small className="product-stock is-out-of-stock">
                            Only {product.available_stock} available; update the quantity.
                          </small>
                        ) : (
                          <small className="product-stock">{product.available_stock} available</small>
                        )}
                        <div className="quantity-control panel-quantity">
                          <button
                            type="button"
                            aria-label={`Remove one ${product.name}`}
                            disabled={isBusy}
                            onClick={() => onQuantityChange(String(product.id), item.quantity - 1)}
                          ><Minus size={14} /></button>
                          <span>{item.quantity}</span>
                          <button
                            type="button"
                            aria-label={`Add one ${product.name}`}
                            disabled={isBusy || unavailable || item.quantity >= product.available_stock}
                            onClick={() => onQuantityChange(String(product.id), item.quantity + 1)}
                          ><Plus size={14} /></button>
                        </div>
                      </div>
                      <button
                        className="remove-item"
                        type="button"
                        aria-label={`Remove ${product.name} from basket`}
                        disabled={isBusy}
                        onClick={() => onRemove(String(product.id))}
                      ><Trash2 size={17} /></button>
                    </article>
                  )
                })}
              </div>
              <div className="panel-summary">
                <div className="subtotal-row">
                  <span>Subtotal</span>
                  <strong>{currency.format(Number(cartData?.total ?? 0))}</strong>
                </div>
                <p>Delivery and any applicable charges are shown when checkout is available.</p>
                <button
                  className="text-button"
                  type="button"
                  disabled={isBusy}
                  onClick={onClear}
                >
                  {isBusy ? 'Updating basket…' : 'Clear basket'}
                </button>
                <button
                  className="button button-primary panel-continue"
                  type="button"
                  disabled={isBusy}
                  onClick={isAuthenticated ? onCheckout : onSignIn}
                >
                  {isAuthenticated ? 'Proceed to checkout' : 'Sign in to checkout'} <ArrowRight size={17} />
                </button>
                <button className="button button-primary panel-continue" type="button" onClick={onClose}>
                  Continue shopping <ArrowRight size={17} />
                </button>
              </div>
            </>
          ) : (
            <div className="panel-empty">
              <span><ShoppingBasket size={25} /></span>
              <h3>{isAuthenticated ? 'Your basket is taking a breather.' : 'Sign in to sync your basket.'}</h3>
              <p>
                {isAuthenticated
                  ? 'Add a few fresh favourites and they’ll be waiting here.'
                  : 'Your basket is saved to your customer account, ready on your next visit.'}
              </p>
              {isAuthenticated ? (
                <button className="button button-primary" type="button" onClick={onClose}>Explore the shop</button>
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
