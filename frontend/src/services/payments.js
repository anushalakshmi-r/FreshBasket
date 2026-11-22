async function request(authenticatedFetch, path, options = {}) {
  const response = await authenticatedFetch(path, options)
  let data = null
  if (response.status !== 204) {
    try {
      data = await response.json()
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new Error('The FreshBasket payment API returned an invalid response.')
      }
      throw error
    }
  }
  if (!response.ok) {
    const message = data && typeof data === 'object'
      ? Object.values(data).flat(Infinity).find((value) => typeof value === 'string')
      : ''
    throw new Error(message || `Payment request failed with HTTP ${response.status}.`)
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

export function createPaymentOrder(authenticatedFetch, orderNumber) {
  return postJson(authenticatedFetch, '/api/payments/create-order/', {
    order_number: orderNumber,
  })
}

export function verifyPayment(authenticatedFetch, payload) {
  return postJson(authenticatedFetch, '/api/payments/verify/', payload)
}

export function getPaymentStatus(authenticatedFetch, orderNumber, options = {}) {
  return request(
    authenticatedFetch,
    `/api/payments/order/${encodeURIComponent(orderNumber)}/`,
    options,
  )
}

function loadRazorpayCheckout() {
  if (window.Razorpay) return Promise.resolve()
  return new Promise((resolve, reject) => {
    let script = document.querySelector('script[data-freshbasket-razorpay]')
    if (!script) {
      script = document.createElement('script')
      script.src = 'https://checkout.razorpay.com/v1/checkout.js'
      script.async = true
      script.dataset.freshbasketRazorpay = 'true'
      document.body.appendChild(script)
    }
    script.addEventListener('load', resolve, { once: true })
    script.addEventListener(
      'error',
      () => reject(new Error('Razorpay Checkout could not be loaded. Check your connection and retry.')),
      { once: true },
    )
  })
}

export async function openRazorpayCheckout(paymentOrder, prefill = {}) {
  await loadRazorpayCheckout()
  return new Promise((resolve, reject) => {
    try {
      const checkout = new window.Razorpay({
        key: paymentOrder.key_id,
        amount: paymentOrder.amount,
        currency: paymentOrder.currency,
        name: 'FreshBasket',
        description: `Order ${paymentOrder.order_number}`,
        order_id: paymentOrder.razorpay_order_id,
        prefill,
        theme: { color: '#315f42' },
        handler: (response) => resolve({ status: 'success', response }),
        modal: {
          ondismiss: () => resolve({ status: 'dismissed' }),
        },
      })
      checkout.on('payment.failed', (response) => {
        resolve({ status: 'failed', error: response.error })
      })
      checkout.open()
    } catch (error) {
      reject(error)
    }
  })
}
