import { getStockInfo } from '../utils/stock'
import { optimizeProductImageUrl } from '../utils/productImage'

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'
).replace(/\/+$/, '')
const CATALOG_URL = `${API_BASE_URL}/api/catalog`

async function request(path, { signal } = {}) {
  let response
  try {
    response = await fetch(`${CATALOG_URL}${path}`, {
      headers: { Accept: 'application/json' },
      signal,
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new Error('Unable to reach the FreshBasket catalogue API. Check that the backend is running.')
  }

  if (!response.ok) {
    throw new Error(`Catalogue request failed with HTTP ${response.status}.`)
  }

  return response.json()
}

function mapCategory(category) {
  return {
    ...category,
    id: category.slug,
    image: category.image_url,
    subcategories: category.subcategories ?? [],
  }
}

function mapProduct(product) {
  const primaryImage = product.images?.find((image) => image.is_primary)
  const image = primaryImage ?? product.images?.[0]
  const dietaryLabel = {
    vegetarian: 'Vegetarian',
    non_vegetarian: 'Non-vegetarian',
  }[product.dietary_type]

  const stockInfo = getStockInfo(product)

  return {
    id: String(product.id),
    sku: product.sku,
    slug: product.slug,
    name: product.name,
    brand: product.brand?.name ?? '',
    brandSlug: product.brand?.slug ?? '',
    categoryId: product.category?.slug ?? '',
    categoryName: product.category?.name ?? '',
    subcategoryId: product.subcategory?.slug ?? '',
    subcategoryName: product.subcategory?.name ?? '',
    description: product.description ?? '',
    shortDescription: product.short_description ?? '',
    dietaryType: product.dietary_type,
    quantity: product.pack_size,
    mrp: Number(product.mrp),
    price: Number(product.selling_price),
    discount: Number(product.discount_percentage),
    image: optimizeProductImageUrl(image?.image_url ?? ''),
    imageAlt: image?.alt_text || product.name,
    stockQuantity: stockInfo.stockCount,
    availableQuantity: stockInfo.stockCount,
    inStock: stockInfo.inStock,
    stock: stockInfo.text,
    stockClass: stockInfo.className,
    isLowStock: stockInfo.isLowStock,
    isFeatured: product.is_featured,
    bestSeller: product.is_bestseller,
    badge: product.is_bestseller
      ? 'Bestseller'
      : product.is_featured
        ? 'Featured'
        : dietaryLabel ?? '',
  }
}

export async function getCategories({ signal } = {}) {
  const categories = await request('/categories/', { signal })
  if (!Array.isArray(categories)) {
    throw new Error('The catalogue API returned an unexpected categories response.')
  }
  return categories.map(mapCategory)
}

export async function getBrands({ signal } = {}) {
  const brands = await request('/brands/', { signal })
  if (!Array.isArray(brands)) {
    throw new Error('The catalogue API returned an unexpected brands response.')
  }
  return brands
}

export async function getProducts(params = {}, { signal } = {}) {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) {
      query.set(key, String(value))
    }
  })

  const data = await request(`/products/?${query.toString()}`, { signal })
  if (!Array.isArray(data.results) || typeof data.count !== 'number') {
    throw new Error('The catalogue API returned an unexpected products response.')
  }

  return {
    ...data,
    results: data.results.map(mapProduct),
  }
}

export async function getHealth({ signal } = {}) {
  const response = await fetch(`${API_BASE_URL}/api/health/`, {
    headers: { Accept: 'application/json' },
    signal,
  })
  if (!response.ok) throw new Error(`Health check failed with HTTP ${response.status}.`)
  return response.json()
}
