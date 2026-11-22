function errorMessage(data, fallback) {
  if (typeof data === 'string') return data
  if (Array.isArray(data)) {
    for (const item of data) {
      const message = errorMessage(item, '')
      if (message) return message
    }
  }
  if (data && typeof data === 'object') {
    for (const value of Object.values(data)) {
      const message = errorMessage(value, '')
      if (message) return message
    }
  }
  return fallback
}

async function request(authenticatedFetch, path, options = {}) {
  const response = await authenticatedFetch(path, options)
  let data = null
  if (response.status !== 204) {
    try {
      data = await response.json()
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error('The shopping API returned an invalid response.')
      }
      throw error
    }
  }

  if (!response.ok) {
    throw new Error(errorMessage(
      data,
      `Shopping request failed with HTTP ${response.status}.`,
    ))
  }
  return data
}

function postJson(authenticatedFetch, path, payload) {
  return request(authenticatedFetch, path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getCart(authenticatedFetch, options = {}) {
  return request(authenticatedFetch, '/api/cart/', options)
}

export function addCartItem(authenticatedFetch, productId, quantity = 1) {
  return postJson(authenticatedFetch, '/api/cart/add/', {
    product_id: Number(productId),
    quantity,
  })
}

export function updateCartItem(authenticatedFetch, itemId, quantity) {
  return request(authenticatedFetch, `/api/cart/items/${itemId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quantity }),
  })
}

export function deleteCartItem(authenticatedFetch, itemId) {
  return request(authenticatedFetch, `/api/cart/items/${itemId}/`, {
    method: 'DELETE',
  })
}

export function clearCart(authenticatedFetch) {
  return request(authenticatedFetch, '/api/cart/clear/', {
    method: 'DELETE',
  })
}

export function getWishlist(authenticatedFetch, options = {}) {
  return request(authenticatedFetch, '/api/wishlist/', options)
}

export function addWishlistItem(authenticatedFetch, productId) {
  return postJson(authenticatedFetch, '/api/wishlist/add/', {
    product_id: Number(productId),
  })
}

export function deleteWishlistProduct(authenticatedFetch, productId) {
  return request(
    authenticatedFetch,
    `/api/wishlist/remove-product/${Number(productId)}/`,
    { method: 'DELETE' },
  )
}
