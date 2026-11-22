import { Heart, Minus, Plus } from 'lucide-react'
import ImageWithFallback from './ImageWithFallback'
import { getStockInfo } from '../utils/stock'

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

export default function ProductCard({
  product,
  quantity = 0,
  isWishlisted,
  onAdd,
  onQuantityChange,
  onToggleWishlist,
  cartBusy = false,
  wishlistBusy = false,
}) {
  const discount = Number.isFinite(product.discount)
    ? Math.round(product.discount)
    : product.mrp > 0
      ? Math.round(((product.mrp - product.price) / product.mrp) * 100)
      : 0

  const stockInfo = getStockInfo(product)

  return (
    <article className="product-card" data-sku={product.sku}>
      <div className="product-image-wrap">
        <ImageWithFallback
          className="product-image"
          src={product.image}
          alt={product.imageAlt || product.name}
          width={600}
          height={400}
          optimize
        />
        {product.badge && <span className="product-badge">{product.badge}</span>}
        {discount > 0 && <span className="discount-badge">{discount}% off</span>}
        <button
          className={`wishlist-toggle${isWishlisted ? ' is-active' : ''}`}
          type="button"
          aria-label={`${isWishlisted ? 'Remove' : 'Add'} ${product.name} ${isWishlisted ? 'from' : 'to'} wishlist`}
          aria-pressed={isWishlisted}
          disabled={wishlistBusy}
          onClick={() => onToggleWishlist(product.id)}
        >
          <Heart size={18} fill={isWishlisted ? 'currentColor' : 'none'} />
        </button>
      </div>
      <div className="product-info">
        {product.brand && <span className="product-brand">{product.brand}</span>}
        <h3 title={product.shortDescription || product.description}>{product.name}</h3>
        <span className="product-quantity">{product.quantity}</span>
        {product.sku && <span className="product-sku">SKU {product.sku}</span>}
        <div className="product-price-row">
          <span className="product-price">{currency.format(product.price)}</span>
          <span className="product-mrp">{currency.format(product.mrp)}</span>
          <span className={`product-stock ${stockInfo.className}`}>
            <span />{stockInfo.text}
          </span>
        </div>
        {quantity > 0 ? (
          <div className="quantity-control" aria-label={`${quantity} ${product.name} in basket`}>
            <button
              type="button"
              aria-label={`Remove one ${product.name}`}
              disabled={cartBusy}
              onClick={() => onQuantityChange(product.id, quantity - 1)}
            ><Minus size={15} /></button>
            <span aria-live="polite">{quantity}</span>
            <button
              type="button"
              aria-label={`Add one ${product.name}`}
              disabled={cartBusy || !stockInfo.inStock || quantity >= (product.availableQuantity ?? stockInfo.stockCount)}
              onClick={() => onQuantityChange(product.id, quantity + 1)}
            ><Plus size={15} /></button>
          </div>
        ) : (
          <button
            className="add-button"
            type="button"
            onClick={() => onAdd(product.id)}
            disabled={!stockInfo.inStock || cartBusy}
          >
            {stockInfo.inStock && <Plus size={16} aria-hidden="true" />}
            {stockInfo.inStock ? 'Add to basket' : 'Out of stock'}
          </button>
        )}
      </div>
    </article>
  )
}
