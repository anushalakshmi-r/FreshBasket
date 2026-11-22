import { ImageOff } from 'lucide-react'
import { useState } from 'react'
import { optimizeProductImageUrl } from '../utils/productImage'

export default function ImageWithFallback({
  src,
  alt,
  className = '',
  loading = 'lazy',
  width,
  height,
  optimize = false,
}) {
  const [failed, setFailed] = useState(false)
  const imageSrc = optimize ? optimizeProductImageUrl(src) : src

  if (failed || !src) {
    return (
      <div className={`image-fallback ${className}`} role="img" aria-label={alt}>
        <ImageOff size={25} aria-hidden="true" />
        <span>FreshBasket</span>
      </div>
    )
  }

  return (
    <img
      className={className}
      src={imageSrc}
      alt={alt}
      loading={loading}
      decoding="async"
      width={width}
      height={height}
      onError={() => setFailed(true)}
    />
  )
}
