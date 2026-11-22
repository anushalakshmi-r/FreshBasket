/**
 * Helper to compute stock display text, classes, and availability status.
 *
 * Rules:
 * - If stock <= 5 (and > 0): show in orange/red bold text "Only 2 left - Hurry!" / "Only 3 left"
 * - If stock > 5: show "In stock" in green
 * - If stock is 0 or unavailable: show "Out of stock" and disable add to basket
 */
export function getStockInfo(product) {
  if (!product) {
    return {
      stockCount: 0,
      inStock: false,
      text: 'Out of stock',
      className: 'is-out-of-stock',
      isLowStock: false,
      isOutOfStock: true,
    }
  }

  // Determine numerical stock count
  let count = null
  if (typeof product.available_stock === 'number') {
    count = product.available_stock
  } else if (typeof product.availableQuantity === 'number') {
    count = product.availableQuantity
  } else if (typeof product.stockQuantity === 'number') {
    count = product.stockQuantity
  } else if (typeof product.stock_quantity === 'number') {
    count = product.stock_quantity
  } else if (typeof product.stock === 'number') {
    count = product.stock
  } else if (typeof product.stock === 'string' && /^\d+$/.test(product.stock.trim())) {
    count = parseInt(product.stock.trim(), 10)
  }

  // Determine availability flag
  const inStock = Boolean(
    product.is_active !== false &&
    product.in_stock !== false &&
    product.inStock !== false &&
    (count === null || count > 0)
  )

  if (!inStock || count === 0) {
    return {
      stockCount: 0,
      inStock: false,
      text: 'Out of stock',
      className: 'is-out-of-stock',
      isLowStock: false,
      isOutOfStock: true,
    }
  }

  if (count !== null && count <= 5) {
    const text = count <= 3 ? `Only ${count} left - Hurry!` : `Only ${count} left`
    return {
      stockCount: count,
      inStock: true,
      text,
      className: 'is-low-stock',
      isLowStock: true,
      isOutOfStock: false,
    }
  }

  return {
    stockCount: count ?? 10,
    inStock: true,
    text: 'In stock',
    className: 'is-in-stock',
    isLowStock: false,
    isOutOfStock: false,
  }
}
