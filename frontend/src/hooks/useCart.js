import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useAuth } from '../context/useAuth'
import {
  addCartItem,
  clearCart as clearCartRequest,
  deleteCartItem,
  getCart,
  updateCartItem,
} from '../services/shopping'

function emptyData() {
  return { items: [], item_count: 0, total: '0.00' }
}

function snapshotFromResponse(ownerId, data) {
  const items = data.items ?? []
  return {
    ownerId,
    data: { ...data, items },
    quantities: Object.fromEntries(
      items.map((item) => [String(item.product.id), item.quantity]),
    ),
    error: '',
  }
}

function emptySnapshot(ownerId = null, error = '') {
  return {
    ownerId,
    data: emptyData(),
    quantities: {},
    error,
  }
}

export function useCart() {
  const {
    user,
    isAuthenticated,
    isLoading: authLoading,
    authenticatedFetch,
  } = useAuth()
  const userId = isAuthenticated ? user?.id : null
  const userIdRef = useRef(userId)
  const currentRef = useRef(emptySnapshot())
  const mutationInProgress = useRef(false)
  const mutationVersion = useRef(0)
  const [snapshot, setSnapshot] = useState(() => emptySnapshot())
  const [isMutating, setIsMutating] = useState(false)

  const refresh = useCallback(async (signal) => {
    if (!userId) return
    try {
      const data = await getCart(authenticatedFetch, { signal })
      if (userIdRef.current !== userId) return
      const next = snapshotFromResponse(userId, data)
      currentRef.current = next
      setSnapshot(next)
    } catch (error) {
      if (error.name === 'AbortError' || userIdRef.current !== userId) return
      const failed = emptySnapshot(userId, error.message)
      currentRef.current = failed
      setSnapshot(failed)
    }
  }, [authenticatedFetch, userId])

  useEffect(() => {
    userIdRef.current = userId
    if (authLoading || !isAuthenticated || !userId) {
      if (!userId) currentRef.current = emptySnapshot()
      return undefined
    }
    const controller = new AbortController()
    currentRef.current = emptySnapshot(userId)
    getCart(authenticatedFetch, { signal: controller.signal })
      .then((data) => {
        if (controller.signal.aborted || userIdRef.current !== userId) return
        const next = snapshotFromResponse(userId, data)
        currentRef.current = next
        setSnapshot(next)
      })
      .catch((error) => {
        if (
          error.name === 'AbortError'
          || controller.signal.aborted
          || userIdRef.current !== userId
        ) return
        const failed = emptySnapshot(userId, error.message)
        currentRef.current = failed
        setSnapshot(failed)
      })
    return () => controller.abort()
  }, [authLoading, authenticatedFetch, isAuthenticated, userId])

  const mutate = useCallback(async (operation, optimisticQuantities, optimisticData) => {
    if (!isAuthenticated || !userId) {
      throw new Error('Sign in to save your basket.')
    }
    if (mutationInProgress.current) {
      throw new Error('Please wait for the current basket update to finish.')
    }

    mutationInProgress.current = true
    const mutationId = ++mutationVersion.current
    setIsMutating(true)
    const previous = currentRef.current.ownerId === userId
      ? currentRef.current
      : emptySnapshot(userId)
    const optimistic = {
      ...previous,
      data: optimisticData ?? previous.data,
      quantities: optimisticQuantities,
      error: '',
    }
    currentRef.current = optimistic
    setSnapshot(optimistic)

    try {
      const data = await operation(previous)
      if (
        mutationVersion.current === mutationId
        && userIdRef.current === userId
        && data
      ) {
        const next = snapshotFromResponse(userId, data)
        currentRef.current = next
        setSnapshot(next)
      }
    } catch (error) {
      if (
        mutationVersion.current === mutationId
        && userIdRef.current === userId
      ) {
        const restored = { ...previous, error: error.message }
        currentRef.current = restored
        setSnapshot(restored)
      }
      throw error
    } finally {
      if (mutationVersion.current === mutationId) {
        mutationInProgress.current = false
        setIsMutating(false)
      }
    }
  }, [isAuthenticated, userId])

  const addItem = useCallback((productId) => {
    const id = String(productId)
    const current = currentRef.current.ownerId === userId
      ? currentRef.current.quantities
      : {}
    return mutate(
      () => addCartItem(authenticatedFetch, productId),
      { ...current, [id]: (current[id] ?? 0) + 1 },
    )
  }, [authenticatedFetch, mutate, userId])

  const updateQuantity = useCallback((productId, quantity) => {
    const id = String(productId)
    const current = currentRef.current.ownerId === userId
      ? currentRef.current
      : emptySnapshot(userId)
    const item = current.data.items.find(
      (cartItem) => String(cartItem.product.id) === id,
    )
    if (quantity <= 0) {
      if (!item) return Promise.resolve()
      const next = { ...current.quantities }
      delete next[id]
      return mutate(
        () => deleteCartItem(authenticatedFetch, item.id).then(() => (
          getCart(authenticatedFetch)
        )),
        next,
      )
    }

    const next = { ...current.quantities, [id]: quantity }
    return mutate(
      () => item
        ? updateCartItem(authenticatedFetch, item.id, quantity)
        : addCartItem(authenticatedFetch, productId, quantity),
      next,
    )
  }, [authenticatedFetch, mutate, userId])

  const removeItem = useCallback((productId) => (
    updateQuantity(productId, 0)
  ), [updateQuantity])

  const clear = useCallback(() => {
    const current = currentRef.current.ownerId === userId
      ? currentRef.current
      : emptySnapshot(userId)
    return mutate(
      () => clearCartRequest(authenticatedFetch),
      {},
      { ...current.data, items: [], item_count: 0, total: '0.00' },
    )
  }, [authenticatedFetch, mutate, userId])

  const clearLocal = useCallback(() => {
    mutationVersion.current += 1
    mutationInProgress.current = false
    const cleared = emptySnapshot()
    currentRef.current = cleared
    setSnapshot(cleared)
    setIsMutating(false)
  }, [])

  const visible = snapshot.ownerId === userId
    ? snapshot
    : emptySnapshot(userId)
  const cart = visible.quantities
  const itemCount = useMemo(
    () => Object.values(cart).reduce((total, quantity) => total + quantity, 0),
    [cart],
  )

  return {
    cart,
    cartData: visible.data,
    cartItems: visible.data.items,
    itemCount,
    isLoading: authLoading || (Boolean(userId) && snapshot.ownerId !== userId),
    isMutating,
    error: visible.error,
    addItem,
    updateQuantity,
    removeItem,
    clear,
    refresh,
    clearLocal,
  }
}
