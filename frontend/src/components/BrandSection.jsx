export default function BrandSection({
  brands,
  loading,
  error,
  onRetry,
  onSelectBrand,
}) {
  return (
    <section className="brand-section page-shell" aria-labelledby="brand-title" data-reveal>
      <div className="brand-intro">
        <span className="section-kicker">GOOD PEOPLE, GOOD PRODUCE</span>
        <h2 id="brand-title">Brands you know.<br />Values we believe in.</h2>
      </div>
      {loading ? (
        <p className="catalogue-message" role="status">Loading brands…</p>
      ) : error ? (
        <div className="catalogue-message catalogue-error" role="alert">
          <p>{error}</p>
          <button className="button button-secondary" type="button" onClick={onRetry}>Retry brands</button>
        </div>
      ) : brands.length ? (
        <div className="brand-list">
          {brands.slice(0, 6).map((brand, index) => (
            <button
              className={`brand-wordmark brand-wordmark-${(index % 6) + 1}`}
              key={brand.slug}
              type="button"
              onClick={() => onSelectBrand(brand.slug)}
            >
              {brand.name}
            </button>
          ))}
        </div>
      ) : (
        <p className="catalogue-message">No brands are available right now.</p>
      )}
    </section>
  )
}
