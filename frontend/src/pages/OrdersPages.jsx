import { useEffect, useRef, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  LoaderCircle,
  MapPin,
  PackageCheck,
  Plus,
  ShoppingBasket,
  Trash2,
} from 'lucide-react'
import Footer from '../components/Footer'
import ImageWithFallback from '../components/ImageWithFallback'
import { useAuth } from '../context/useAuth'
import {
  cancelOrder,
  createAddress,
  deleteAddress,
  getAddresses,
  getCheckoutQuote,
  getOrder,
  getOrders,
  placeOrder,
  setDefaultAddress,
  updateAddress,
} from '../services/orders'
import {
  createPaymentOrder,
  getPaymentStatus,
  openRazorpayCheckout,
  verifyPayment,
} from '../services/payments'

const currency = new Intl.NumberFormat('en-IN', {
  style: 'currency',
  currency: 'INR',
  maximumFractionDigits: 2,
})

const emptyAddress = {
  full_name: '',
  phone_number: '',
  address_line_1: '',
  address_line_2: '',
  landmark: '',
  city: '',
  state: '',
  postal_code: '',
  address_type: 'home',
  is_default: false,
}

const LAST_PLACED_ORDER_KEY = 'freshbasket:lastPlacedOrder'

function readSavedOrder(orderNumber) {
  try {
    const savedOrder = JSON.parse(localStorage.getItem(LAST_PLACED_ORDER_KEY) || 'null')
    return savedOrder?.order_number === orderNumber ? savedOrder : null
  } catch {
    return null
  }
}

function savePlacedOrder(order) {
  try {
    localStorage.setItem(LAST_PLACED_ORDER_KEY, JSON.stringify(order))
  } catch {
    // The server remains the source of truth if browser storage is unavailable.
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat('en-IN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value))
}

function OrderShell({ children, onNavigate, eyebrow = 'FreshBasket orders', title, description }) {
  return (
    <div className="orders-page">
      <header className="auth-topbar page-shell">
        <a
          className="auth-brand"
          href="/"
          onClick={(event) => {
            event.preventDefault()
            onNavigate('/')
          }}
        >
          <span className="brand-mark"><ShoppingBasket size={21} /></span>
          <span className="brand-name">fresh<span>basket</span><small>GOOD FOOD, GOOD DAYS</small></span>
        </a>
        <button className="auth-back-link" type="button" onClick={() => onNavigate('/')}>
          <ArrowLeft size={16} /> Continue shopping
        </button>
      </header>
      <main className="orders-main page-shell">
        <div className="orders-heading">
          <span className="auth-eyebrow">{eyebrow}</span>
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
        {children}
      </main>
      <Footer onNavigate={onNavigate} />
    </div>
  )
}

function LoadingNotice({ children = 'Loading your order details…' }) {
  return (
    <div className="orders-notice" role="status">
      <LoaderCircle className="auth-spinner" size={22} /> {children}
    </div>
  )
}

function ErrorNotice({ message, onRetry }) {
  return (
    <div className="auth-alert" role="alert">
      <p>{message}</p>
      {onRetry && <button className="orders-link-button" type="button" onClick={onRetry}>Retry</button>}
    </div>
  )
}

function AddressForm({ address, busy, onCancel, onSave, onChange }) {
  return (
    <form className="orders-address-form" onSubmit={onSave}>
      <div className="auth-field-row">
        <label className="auth-field">
          <span>Full name</span>
          <input name="full_name" value={address.full_name} onChange={onChange} autoComplete="name" required />
        </label>
        <label className="auth-field">
          <span>Phone number</span>
          <input name="phone_number" type="tel" value={address.phone_number} onChange={onChange} pattern="\+?[1-9]\d{6,14}" required />
        </label>
      </div>
      <label className="auth-field">
        <span>Address line 1</span>
        <input name="address_line_1" value={address.address_line_1} onChange={onChange} autoComplete="address-line1" required />
      </label>
      <div className="auth-field-row">
        <label className="auth-field">
          <span>Address line 2 <small>(optional)</small></span>
          <input name="address_line_2" value={address.address_line_2} onChange={onChange} autoComplete="address-line2" />
        </label>
        <label className="auth-field">
          <span>Landmark <small>(optional)</small></span>
          <input name="landmark" value={address.landmark} onChange={onChange} />
        </label>
      </div>
      <div className="auth-field-row orders-address-location">
        <label className="auth-field">
          <span>City</span>
          <input name="city" value={address.city} onChange={onChange} autoComplete="address-level2" required />
        </label>
        <label className="auth-field">
          <span>State</span>
          <input name="state" value={address.state} onChange={onChange} autoComplete="address-level1" required />
        </label>
        <label className="auth-field">
          <span>PIN code</span>
          <input name="postal_code" inputMode="numeric" pattern="[1-9]\d{5}" maxLength={6} value={address.postal_code} onChange={onChange} autoComplete="postal-code" required />
        </label>
      </div>
      <div className="auth-field-row orders-address-footer">
        <label className="auth-field">
          <span>Address type</span>
          <select name="address_type" value={address.address_type} onChange={onChange}>
            <option value="home">Home</option>
            <option value="work">Work</option>
            <option value="other">Other</option>
          </select>
        </label>
        <label className="orders-checkbox">
          <input name="is_default" type="checkbox" checked={address.is_default} onChange={onChange} />
          Make this my default address
        </label>
      </div>
      <div className="orders-form-actions">
        <button className="button button-primary" type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Save address'}
        </button>
        <button className="orders-link-button" type="button" onClick={onCancel} disabled={busy}>Cancel</button>
      </div>
    </form>
  )
}

function AddressCard({ address, selected, disabled, onSelect, onEdit, onDelete, onDefault }) {
  return (
    <article className={`orders-address-card${selected ? ' is-selected' : ''}`}>
      <label className="orders-address-select">
        <input
          type="radio"
          name="delivery_address"
          value={address.id}
          checked={selected}
          onChange={onSelect}
          disabled={disabled}
        />
        <span className="orders-address-icon"><MapPin size={18} /></span>
        <span className="orders-address-copy">
          <strong>{address.full_name} <small>{address.address_type}</small></strong>
          <span>{address.address_line_1}{address.address_line_2 ? `, ${address.address_line_2}` : ''}</span>
          {address.landmark && <span>Near {address.landmark}</span>}
          <span>{address.city}, {address.state} {address.postal_code}</span>
          <span>{address.phone_number}</span>
        </span>
      </label>
      {address.is_default && <span className="orders-default-badge">Default</span>}
      <div className="orders-address-actions">
        {!address.is_default && (
          <button type="button" onClick={onDefault} disabled={disabled}>Make default</button>
        )}
        <button type="button" onClick={onEdit} disabled={disabled}>Edit</button>
        <button type="button" onClick={onDelete} disabled={disabled} aria-label={`Delete ${address.address_type} address`}>
          <Trash2 size={14} /> Delete
        </button>
      </div>
    </article>
  )
}

export function CheckoutPage({ onNavigate, onOrderPlaced }) {
  const { authenticatedFetch, isAuthenticated, isLoading: authLoading } = useAuth()
  const [addresses, setAddresses] = useState([])
  const [quote, setQuote] = useState(null)
  const [selectedAddressId, setSelectedAddressId] = useState('')
  const [paymentMethod, setPaymentMethod] = useState('cod')
  const [addressForm, setAddressForm] = useState(null)
  const [editingAddressId, setEditingAddressId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [quoteVersion, setQuoteVersion] = useState(0)
  const [placedOrder, setPlacedOrder] = useState(null)
  const submitInProgress = useRef(false)

  useEffect(() => {
    if (authLoading) return undefined
    if (!isAuthenticated) {
      onNavigate('/login')
      return undefined
    }
    const controller = new AbortController()
    Promise.all([
      getAddresses(authenticatedFetch, { signal: controller.signal }),
      getCheckoutQuote(authenticatedFetch, { signal: controller.signal }),
    ])
      .then(([savedAddresses, currentQuote]) => {
        if (controller.signal.aborted) return
        setAddresses(savedAddresses)
        setSelectedAddressId((current) => (
          current || String(savedAddresses.find((address) => address.is_default)?.id ?? savedAddresses[0]?.id ?? '')
        ))
        setQuote(currentQuote)
      })
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') setError(requestError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [authLoading, authenticatedFetch, isAuthenticated, onNavigate, quoteVersion])

  function updateAddressField(event) {
    const { name, type, value, checked } = event.target
    setAddressForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }))
  }

  function startAddressForm(address = null) {
    setEditingAddressId(address?.id ?? null)
    setAddressForm(address ? { ...address } : { ...emptyAddress })
    setError('')
  }

  async function saveAddress(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const saved = editingAddressId
        ? await updateAddress(authenticatedFetch, editingAddressId, addressForm)
        : await createAddress(authenticatedFetch, addressForm)
      const next = await getAddresses(authenticatedFetch)
      setAddresses(next)
      setSelectedAddressId(String(saved.id))
      setAddressForm(null)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  async function removeAddress(addressId) {
    if (!window.confirm('Delete this saved delivery address?')) return
    setBusy(true)
    setError('')
    try {
      await deleteAddress(authenticatedFetch, addressId)
      const next = await getAddresses(authenticatedFetch)
      setAddresses(next)
      if (String(addressId) === selectedAddressId) {
        setSelectedAddressId(String(next.find((address) => address.is_default)?.id ?? next[0]?.id ?? ''))
      }
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  async function makeDefault(addressId) {
    setBusy(true)
    setError('')
    try {
      await setDefaultAddress(authenticatedFetch, addressId)
      const next = await getAddresses(authenticatedFetch)
      setAddresses(next)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  async function submitOrder() {
    if (submitInProgress.current || !selectedAddressId || !quote?.items?.length) return
    submitInProgress.current = true
    setBusy(true)
    setError('')
    try {
      const order = await placeOrder(authenticatedFetch, {
        address_id: Number(selectedAddressId),
        payment_method: paymentMethod,
      })
      savePlacedOrder(order)
      setPlacedOrder(order)
      await onOrderPlaced()
      if (paymentMethod === 'cod') {
        onNavigate(`/order-confirmation/${encodeURIComponent(order.order_number)}`)
        return
      }

      try {
        const paymentOrder = await createPaymentOrder(authenticatedFetch, order.order_number)
        const result = await openRazorpayCheckout(paymentOrder)
        if (result.status === 'success') {
          await verifyPayment(authenticatedFetch, result.response)
        } else if (result.status === 'failed') {
          const paymentId = result.error?.metadata?.payment_id
          if (paymentId) {
            await verifyPayment(authenticatedFetch, {
              razorpay_order_id: paymentOrder.razorpay_order_id,
              razorpay_payment_id: paymentId,
            })
          }
        }
        onNavigate(`/order-confirmation/${encodeURIComponent(order.order_number)}`)
      } catch (paymentError) {
        setError(
          `Order ${order.order_number} was placed, but payment could not be completed: ${paymentError.message}`,
        )
      }
    } catch (requestError) {
      setError(requestError.message)
      setQuoteVersion((version) => version + 1)
    } finally {
      submitInProgress.current = false
      setBusy(false)
    }
  }

  if (authLoading || loading) {
    return <OrderShell onNavigate={onNavigate} title="Checkout"><LoadingNotice>Preparing your checkout…</LoadingNotice></OrderShell>
  }

  return (
    <OrderShell
      onNavigate={onNavigate}
      title="A few details, then it’s on its way."
      description="Choose where your groceries should go and how you’d like to pay."
    >
      {error && (
        <ErrorNotice
          message={error}
          onRetry={() => {
            setError('')
            setQuoteVersion((version) => version + 1)
          }}
        />
      )}
      {placedOrder ? (
        <section className="orders-empty checkout-order-success">
          <CheckCircle2 size={28} />
          <h2>Order Placed! 🎉 #{placedOrder.order_number}</h2>
          <p>Your order details are saved. You can track its progress or continue shopping.</p>
          <div className="orders-bottom-actions">
            <button className="button button-primary" type="button" onClick={() => onNavigate('/track-order')}>Track My Order</button>
            <button className="button button-secondary" type="button" onClick={() => onNavigate('/')}>Continue Shopping</button>
          </div>
        </section>
      ) : !quote?.items?.length ? (
        <section className="orders-empty">
          <ShoppingBasket size={28} />
          <h2>Your basket is empty</h2>
          <p>Add a few fresh favourites before starting checkout.</p>
          <button className="button button-primary" type="button" onClick={() => onNavigate('/')}>Browse groceries</button>
        </section>
      ) : (
        <div className="checkout-layout">
          <div className="checkout-main-column">
            <section className="orders-card">
              <div className="orders-section-heading">
                <span>01</span><div><h2>Delivery address</h2><p>Choose an address saved to your account.</p></div>
                {!addressForm && (
                  <button className="orders-add-button" type="button" onClick={() => startAddressForm()}>
                    <Plus size={16} /> Add new
                  </button>
                )}
              </div>
              {addressForm ? (
                <AddressForm
                  address={addressForm}
                  busy={busy}
                  onCancel={() => setAddressForm(null)}
                  onSave={saveAddress}
                  onChange={updateAddressField}
                />
              ) : addresses.length ? (
                <div className="orders-address-list">
                  {addresses.map((address) => (
                    <AddressCard
                      key={address.id}
                      address={address}
                      selected={String(address.id) === selectedAddressId}
                      disabled={busy}
                      onSelect={() => setSelectedAddressId(String(address.id))}
                      onEdit={() => startAddressForm(address)}
                      onDelete={() => removeAddress(address.id)}
                      onDefault={() => makeDefault(address.id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="orders-inline-empty">
                  <p>Add a delivery address to continue.</p>
                  <button className="button button-secondary" type="button" onClick={() => startAddressForm()}>Add address</button>
                </div>
              )}
            </section>

            <section className="orders-card">
              <div className="orders-section-heading">
                <span>02</span><div><h2>Payment method</h2><p>Choose Cash on Delivery or secure online payment.</p></div>
              </div>
              <div className="orders-payment-options">
                <label className={paymentMethod === 'cod' ? 'is-selected' : ''}>
                  <input type="radio" name="payment_method" value="cod" checked={paymentMethod === 'cod'} onChange={() => setPaymentMethod('cod')} />
                  <span><strong>Cash on Delivery</strong><small>Pay when your order arrives.</small></span>
                </label>
                <label className={paymentMethod === 'online' ? 'is-selected' : ''}>
                  <input type="radio" name="payment_method" value="online" checked={paymentMethod === 'online'} onChange={() => setPaymentMethod('online')} />
                  <span><strong>Online payment</strong><small>Pay securely with Razorpay after placing your order.</small></span>
                </label>
              </div>
            </section>
          </div>

          <aside className="orders-card checkout-summary">
            <div className="orders-section-heading">
              <span>03</span><div><h2>Your order</h2><p>{quote.items.length} product{quote.items.length === 1 ? '' : 's'}</p></div>
            </div>
            <div className="checkout-products">
              {quote.items.map((item) => (
                <article className="checkout-product" key={item.product_id}>
                  <ImageWithFallback src={item.image_url} alt={item.product_name} optimize />
                  <div><strong>{item.product_name}</strong><small>Qty {item.quantity} × {currency.format(Number(item.unit_price))}</small></div>
                  <b>{currency.format(Number(item.line_total))}</b>
                </article>
              ))}
            </div>
            <div className="checkout-totals">
              <div><span>Subtotal</span><strong>{currency.format(Number(quote.subtotal))}</strong></div>
              <div><span>Delivery</span><strong>{Number(quote.delivery_fee) ? currency.format(Number(quote.delivery_fee)) : 'Free'}</strong></div>
              <div><span>Discount</span><strong>−{currency.format(Number(quote.discount))}</strong></div>
              <div className="checkout-grand-total"><span>Total</span><strong>{currency.format(Number(quote.grand_total))}</strong></div>
            </div>
            <p className="checkout-delivery-note">
              {Number(quote.delivery_fee)
                ? `Free delivery on orders of ${currency.format(Number(quote.free_delivery_threshold))} or more.`
                : 'Your order qualifies for free delivery.'}
            </p>
            <button
              className="button button-primary checkout-place-order"
              type="button"
              disabled={busy || !selectedAddressId || !addresses.length}
              onClick={submitOrder}
            >
              {busy ? <><LoaderCircle className="auth-spinner" size={17} /> Placing order…</> : <>Place order <ArrowRight size={17} /></>}
            </button>
            <p className="checkout-safe-note">Your total and product availability are confirmed securely by FreshBasket when you place the order.</p>
          </aside>
        </div>
      )}
    </OrderShell>
  )
}

export function OrdersPage({ onNavigate }) {
  const { authenticatedFetch, isAuthenticated, isLoading: authLoading } = useAuth()
  const [orders, setOrders] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshVersion, setRefreshVersion] = useState(0)

  useEffect(() => {
    if (authLoading) return undefined
    if (!isAuthenticated) {
      onNavigate('/login')
      return undefined
    }
    const controller = new AbortController()
    getOrders(authenticatedFetch, { signal: controller.signal })
      .then(setOrders)
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') setError(requestError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [authLoading, authenticatedFetch, isAuthenticated, onNavigate, refreshVersion])

  async function handleCancel(orderNumber) {
    if (!window.confirm(`Cancel order ${orderNumber}?`)) return
    try {
      await cancelOrder(authenticatedFetch, orderNumber)
      setRefreshVersion((version) => version + 1)
    } catch (requestError) {
      setError(requestError.message)
    }
  }

  return (
    <OrderShell
      onNavigate={onNavigate}
      title="My orders"
      description="A little history of the good things headed your way."
    >
      {error && <ErrorNotice message={error} onRetry={() => setRefreshVersion((version) => version + 1)} />}
      {loading ? <LoadingNotice /> : orders.length ? (
        <div className="orders-list">
          {orders.map((order) => (
            <article className="orders-card order-list-card" key={order.order_number}>
              <div className="order-list-heading">
                <div><span className="auth-eyebrow">Order placed {formatDate(order.created_at)}</span><h2>{order.order_number}</h2></div>
                <span className={`order-status status-${order.order_status}`}>{order.order_status}</span>
              </div>
              <div className="order-list-meta">
                <span>{order.items.length} item{order.items.length === 1 ? '' : 's'}</span>
                <span>{order.payment_method === 'cod' ? 'Cash on Delivery' : 'Online'} · Payment {order.payment_status}</span>
                <strong>{currency.format(Number(order.grand_total))}</strong>
              </div>
              <div className="order-list-actions">
                <button className="button button-secondary" type="button" onClick={() => onNavigate(`/orders/${encodeURIComponent(order.order_number)}`)}>
                  View order <ArrowRight size={16} />
                </button>
                {['pending', 'confirmed'].includes(order.order_status) && (
                  <button className="orders-link-button orders-cancel-button" type="button" onClick={() => handleCancel(order.order_number)}>Cancel order</button>
                )}
              </div>
            </article>
          ))}
        </div>
      ) : (
        <section className="orders-empty">
          <ClipboardList size={28} /><h2>No orders just yet</h2>
          <p>Your next fresh find is waiting on the shelves.</p>
          <button className="button button-primary" type="button" onClick={() => onNavigate('/')}>Explore the shop</button>
        </section>
      )}
    </OrderShell>
  )
}

function OrderContents({ order }) {
  return (
    <>
      <div className="order-detail-layout">
        <section className="orders-card order-detail-items">
          <div className="orders-section-heading"><span><PackageCheck size={18} /></span><div><h2>Items in your order</h2><p>Prices shown are from when you placed this order.</p></div></div>
          {order.items.map((item) => (
            <article className="checkout-product order-detail-product" key={item.id}>
              <ImageWithFallback src={item.product_image_snapshot} alt={item.product_name_snapshot} optimize />
              <div><strong>{item.product_name_snapshot}</strong><small>{item.sku_snapshot} · Qty {item.quantity} × {currency.format(Number(item.unit_price))}</small></div>
              <b>{currency.format(Number(item.line_total))}</b>
            </article>
          ))}
          <div className="checkout-totals">
            <div><span>Subtotal</span><strong>{currency.format(Number(order.subtotal))}</strong></div>
            <div><span>Delivery</span><strong>{Number(order.delivery_fee) ? currency.format(Number(order.delivery_fee)) : 'Free'}</strong></div>
            <div><span>Discount</span><strong>−{currency.format(Number(order.discount))}</strong></div>
            <div className="checkout-grand-total"><span>Total</span><strong>{currency.format(Number(order.grand_total))}</strong></div>
          </div>
        </section>
        <aside className="orders-card order-address-snapshot">
          <div className="orders-section-heading"><span><MapPin size={18} /></span><div><h2>Delivery address</h2><p>Saved with your order.</p></div></div>
          <strong>{order.delivery_address_snapshot.full_name}</strong>
          <p>{order.delivery_address_snapshot.address_line_1}</p>
          {order.delivery_address_snapshot.address_line_2 && <p>{order.delivery_address_snapshot.address_line_2}</p>}
          {order.delivery_address_snapshot.landmark && <p>Near {order.delivery_address_snapshot.landmark}</p>}
          <p>{order.delivery_address_snapshot.city}, {order.delivery_address_snapshot.state} {order.delivery_address_snapshot.postal_code}</p>
          <p>{order.delivery_address_snapshot.phone_number}</p>
          <div className="order-payment-note">
            <strong>{order.payment_method === 'cod' ? 'Cash on Delivery' : 'Online payment'}</strong>
            <span>Payment {order.payment_status}</span>
          </div>
        </aside>
      </div>
    </>
  )
}

function OrderRecordPage({ orderNumber, onNavigate, confirmation = false }) {
  const { authenticatedFetch, isAuthenticated, isLoading: authLoading } = useAuth()
  const [order, setOrder] = useState(() => confirmation ? readSavedOrder(orderNumber) : null)
  const [loading, setLoading] = useState(() => !(confirmation && readSavedOrder(orderNumber)))
  const [error, setError] = useState('')
  const [paymentMessage, setPaymentMessage] = useState('')
  const [paymentAvailability, setPaymentAvailability] = useState(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (authLoading) return undefined
    if (!isAuthenticated) {
      onNavigate('/login')
      return undefined
    }
    const controller = new AbortController()
    getOrder(authenticatedFetch, orderNumber, { signal: controller.signal })
      .then((currentOrder) => {
        if (controller.signal.aborted) return
        setOrder(currentOrder)
        if (confirmation) savePlacedOrder(currentOrder)
        if (
          currentOrder.payment_method === 'online'
          && ['pending', 'failed'].includes(currentOrder.payment_status)
        ) {
          getPaymentStatus(
            authenticatedFetch,
            orderNumber,
            { signal: controller.signal },
          )
            .then((availability) => {
              if (!controller.signal.aborted) setPaymentAvailability(availability)
            })
            .catch((requestError) => {
              if (requestError.name !== 'AbortError') setPaymentMessage(requestError.message)
            })
        }
      })
      .catch((requestError) => {
        if (requestError.name !== 'AbortError' && !readSavedOrder(orderNumber)) setError(requestError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [authLoading, authenticatedFetch, isAuthenticated, onNavigate, orderNumber])

  async function handleCancel() {
    if (!order || !window.confirm(`Cancel order ${order.order_number}?`)) return
    setBusy(true)
    try {
      setOrder(await cancelOrder(authenticatedFetch, order.order_number))
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  async function handlePaymentRetry() {
    if (!order || busy) return
    setBusy(true)
    setPaymentMessage('')
    try {
      const paymentOrder = await createPaymentOrder(authenticatedFetch, order.order_number)
      const result = await openRazorpayCheckout(paymentOrder)
      if (result.status === 'success') {
        const verification = await verifyPayment(authenticatedFetch, result.response)
        setPaymentMessage(
          verification.state === 'captured'
            ? 'Payment confirmed. Your order is being prepared.'
            : 'Payment is still being confirmed. Refresh this page shortly.',
        )
      } else if (result.status === 'failed') {
        const paymentId = result.error?.metadata?.payment_id
        if (paymentId) {
          try {
            await verifyPayment(authenticatedFetch, {
              razorpay_order_id: paymentOrder.razorpay_order_id,
              razorpay_payment_id: paymentId,
            })
          } catch (verificationError) {
            setPaymentMessage(verificationError.message)
          }
        } else {
          setPaymentMessage('Payment did not complete. You can try again using the same order.')
        }
      } else {
        setPaymentMessage('Payment window closed. You can retry whenever you are ready.')
      }
      const refreshedOrder = await getOrder(authenticatedFetch, order.order_number)
      setOrder(refreshedOrder)
      const availability = await getPaymentStatus(authenticatedFetch, order.order_number)
      setPaymentAvailability(availability)
    } catch (requestError) {
      setPaymentMessage(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  if (loading || authLoading) {
    return <OrderShell onNavigate={onNavigate} title={confirmation ? 'Order received' : 'Order details'}><LoadingNotice /></OrderShell>
  }

  return (
    <OrderShell
      onNavigate={onNavigate}
      eyebrow={confirmation ? 'Thank you for shopping FreshBasket' : 'Your order'}
      title={confirmation ? 'Your order is in good hands.' : 'Order details'}
      description={order ? `${order.order_number} · Placed ${formatDate(order.created_at)}` : ''}
    >
      {error && <ErrorNotice message={error} />}
      {!order ? (
        <section className="orders-empty"><h2>We couldn’t find that order</h2><button className="button button-primary" type="button" onClick={() => onNavigate('/orders')}>Go to my orders</button></section>
      ) : (
        <>
          {confirmation && (
            <div className="order-confirmation-banner">
              <CheckCircle2 size={23} />
              <div>
                <strong>Order Placed! 🎉 #{order.order_number}</strong>
                <span>
                  {order.payment_status === 'paid'
                    ? `Payment for order ${order.order_number} is verified.`
                    : `Your order number is ${order.order_number}. We’ve saved your basket as an order.`}
                </span>
              </div>
            </div>
          )}
          <div className="order-status-bar">
            <span className={`order-status status-${order.order_status}`}>{order.order_status}</span>
            <span>Payment: {order.payment_status}</span>
            {paymentAvailability?.can_retry && (
              <button
                className="button button-primary"
                type="button"
                disabled={busy}
                onClick={handlePaymentRetry}
              >
                {busy ? 'Waiting for payment…' : 'Pay with Razorpay'}
              </button>
            )}
            {['pending', 'confirmed'].includes(order.order_status) && (
              <button className="orders-link-button orders-cancel-button" type="button" disabled={busy} onClick={handleCancel}>
                {busy ? 'Cancelling…' : 'Cancel order'}
              </button>
            )}
          </div>
          {paymentAvailability?.configured === false && order.payment_method === 'online' && (
            <ErrorNotice message="Razorpay is not configured on the backend yet. Add test credentials locally to enable online payment." />
          )}
          {paymentMessage && <div className="orders-notice" role="status">{paymentMessage}</div>}
          <OrderContents order={order} />
          <div className="orders-bottom-actions">
            {confirmation ? (
              <>
                <button className="button button-primary" type="button" onClick={() => onNavigate('/track-order')}>Track My Order</button>
                <button className="button button-secondary" type="button" onClick={() => onNavigate('/')}>Continue Shopping</button>
              </>
            ) : (
              <>
                <button className="button button-secondary" type="button" onClick={() => onNavigate('/orders')}>View all orders</button>
                <button className="button button-primary" type="button" onClick={() => onNavigate('/')}>Continue shopping</button>
              </>
            )}
          </div>
        </>
      )}
    </OrderShell>
  )
}

export function OrderDetailPage({ orderNumber, onNavigate }) {
  return <OrderRecordPage orderNumber={orderNumber} onNavigate={onNavigate} />
}

export function OrderConfirmationPage({ orderNumber, onNavigate }) {
  return <OrderRecordPage orderNumber={orderNumber} onNavigate={onNavigate} confirmation />
}
