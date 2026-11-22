import { useCallback, useEffect, useRef, useState } from 'react'
import { useAuth } from '../context/useAuth'
import {
  addWishlistItem,
  deleteWishlistProduct,
  getWishlist,
} from '../services/shopping'

function snapshotFromResponse(ownerId, data) {
  const items = data.items ?? []
  return {
    ownerId,
    items,
    productIds: new Set(items.map((item) => String(item.product.id))),
    error: '',
  }
}

function emptySnapshot(ownerId = null, error = '') {
  return {
    ownerId,
    items: [],
    productIds: new Set(),
    error,
  }
}

export function useWishlist() {
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
      const data = await getWishlist(authenticatedFetch, { signal })
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
    getWishlist(authenticatedFetch, { signal: controller.signal })
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

  const mutate = useCallback(async (operation, optimisticIds) => {
    if (!isAuthenticated || !userId) {
      throw new Error('Sign in to save your wishlist.')
    }
    if (mutationInProgress.current) {
      throw new Error('Please wait for the current wishlist update to finish.')
    }

    mutationInProgress.current = true
    const mutationId = ++mutationVersion.current
    setIsMutating(true)
    const previous = currentRef.current.ownerId === userId
      ? currentRef.current
      : emptySnapshot(userId)
    const optimistic = {
      ...previous,
      items: previous.items.filter(
        (item) => optimisticIds.has(String(item.product.id)),
      ),
      productIds: optimisticIds,
      error: '',
    }
    currentRef.current = optimistic
    setSnapshot(optimistic)

    try {
      const data = await operation()
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

  const toggleWishlist = useCallback((productId) => {
    if (!isAuthenticated || !userId) {
      return Promise.reject(new Error('Sign in to save your wishlist.'))
    }
    const id = String(productId)
    const current = currentRef.current.ownerId === userId
      ? currentRef.current.productIds
      : new Set()
    const next = new Set(current)
    const isSaved = next.has(id)
    if (isSaved) next.delete(id)
    else next.add(id)

    return mutate(
      () => (isSaved
        ? deleteWishlistProduct(authenticatedFetch, productId)
          .then(() => getWishlist(authenticatedFetch))
        : addWishlistItem(authenticatedFetch, productId)),
      next,
    )
  }, [authenticatedFetch, isAuthenticated, mutate, userId])

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

  return {
    wishlist: visible.productIds,
    wishlistItems: visible.items,
    isLoading: authLoading || (Boolean(userId) && snapshot.ownerId !== userId),
    isMutating,
    error: visible.error,
    toggleWishlist,
    refresh,
    clearLocal,
  }
}
