function findMessage(value) {
  if (typeof value === 'string') return value
  if (Array.isArray(value)) {
    for (const item of value) {
      const message = findMessage(item)
      if (message) return message
    }
  }
  if (value && typeof value === 'object') {
    for (const nested of Object.values(value)) {
      const message = findMessage(nested)
      if (message) return message
    }
  }
  return ''
}

async function request(authenticatedFetch, path, options = {}) {
  const response = await authenticatedFetch(path, options)
  let data = null
  if (response.status !== 204) {
    try {
      data = await response.json()
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error('The FreshBasket order API returned an invalid response.')
      }
      throw error
    }
  }
  if (!response.ok) {
    throw new Error(findMessage(data) || `Order request failed with HTTP ${response.status}.`)
  }
  return data
}

function postJson(authenticatedFetch, path, payload = {}) {
  return request(authenticatedFetch, path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getAddresses(authenticatedFetch, options = {}) {
  return request(authenticatedFetch, '/api/accounts/addresses/', options)
}

export function createAddress(authenticatedFetch, payload) {
  return postJson(authenticatedFetch, '/api/accounts/addresses/', payload)
}

export function updateAddress(authenticatedFetch, addressId, payload) {
  return request(authenticatedFetch, `/api/accounts/addresses/${addressId}/`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function deleteAddress(authenticatedFetch, addressId) {
  return request(authenticatedFetch, `/api/accounts/addresses/${addressId}/`, {
    method: 'DELETE',
  })
}

export function setDefaultAddress(authenticatedFetch, addressId) {
  return postJson(authenticatedFetch, `/api/accounts/addresses/${addressId}/set-default/`)
}

export function getCheckoutQuote(authenticatedFetch, options = {}) {
  return request(authenticatedFetch, '/api/orders/checkout/', options)
}

export function placeOrder(authenticatedFetch, payload) {
  return postJson(authenticatedFetch, '/api/orders/checkout/', payload)
}

export function getOrders(authenticatedFetch, options = {}) {
  return request(authenticatedFetch, '/api/orders/', options)
}

export function getOrder(authenticatedFetch, orderNumber, options = {}) {
  return request(authenticatedFetch, `/api/orders/${encodeURIComponent(orderNumber)}/`, options)
}

export function cancelOrder(authenticatedFetch, orderNumber) {
  return postJson(
    authenticatedFetch,
    `/api/orders/${encodeURIComponent(orderNumber)}/cancel/`,
  )
}
