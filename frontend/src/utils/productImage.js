export function optimizeProductImageUrl(imageUrl) {
  if (!imageUrl) return ''

  try {
    const url = new URL(imageUrl)
    if (url.hostname !== 'images.unsplash.com') return imageUrl

    url.searchParams.set('auto', 'format')
    url.searchParams.set('fit', 'crop')
    url.searchParams.set('w', '600')
    url.searchParams.set('q', '60')
    return url.toString()
  } catch {
    return imageUrl
  }
}
