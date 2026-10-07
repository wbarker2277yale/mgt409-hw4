import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CATEGORIES, SIZES, categoryOf } from '../catalog'
import ProductCard from '../components/ProductCard'
import { useStore } from '../store'

const SORTS = [
  { key: 'featured', label: 'Featured' },
  { key: 'price-asc', label: 'Price: low to high' },
  { key: 'price-desc', label: 'Price: high to low' },
  { key: 'name', label: 'Name' },
]

export default function Products() {
  const { catalogue, catalogueError, chatResults, setChatResults } = useStore()
  // Problem 9 (F1): filters live in the address bar, so a filtered view can be shared and survives a reload.
  const [params, setParams] = useSearchParams()
  const cat = params.get('cat') ?? 'all'
  const size = params.get('size') ?? ''
  const sort = params.get('sort') ?? 'featured'
  const q = params.get('q') ?? ''

  function set(key: string, value: string) {
    const next = new URLSearchParams(params)
    if (!value || value === 'all' || (key === 'sort' && value === 'featured')) next.delete(key)
    else next.set(key, value)
    setParams(next, { replace: true })
  }

  const shown = useMemo(() => {
    const words = q.toLowerCase().split(/\s+/).filter(Boolean)
    const list = catalogue.filter((p) =>
      (cat === 'all' || categoryOf(p) === cat) &&
      (!size || p.sizes_in_stock?.includes(size)) &&
      words.every((w) => `${p.name} ${p.description} ${(p.colors ?? []).join(' ')}`.toLowerCase().includes(w)))
    if (sort === 'price-asc') return [...list].sort((a, b) => a.price - b.price || a.name.localeCompare(b.name))
    if (sort === 'price-desc') return [...list].sort((a, b) => b.price - a.price || a.name.localeCompare(b.name))
    if (sort === 'name') return [...list].sort((a, b) => a.name.localeCompare(b.name))
    return list
  }, [catalogue, cat, size, sort, q])

  // Problem 7: cards the chat assistant found replace the catalogue until the shopper clears them.
  if (chatResults) {
    return (
      <>
        <div className="clerk-note">
          <div>
            <p className="kicker">A note from the clerk · you asked</p>
            <p className="clerk-query">“{chatResults.query}”</p>
          </div>
          <div className="clerk-count">
            <strong>{chatResults.products.length}</strong>
            <span>{chatResults.products.length === 1 ? 'match' : 'matches'}</span>
          </div>
          <button className="button" onClick={() => setChatResults(null)}>Show all products</button>
        </div>
        <div className="grid">
          {chatResults.products.map((p, i) => <ProductCard key={p.product_id} product={p} index={i} />)}
        </div>
      </>
    )
  }

  if (catalogueError) return <p className="error">Could not load products: {catalogueError}</p>
  if (!catalogue.length) return <p className="loading">Pulling the catalogue from the drawer…</p>

  const filtered = cat !== 'all' || size || q || sort !== 'featured'

  return (
    <>
      <header className="page-head">
        <p className="kicker">Campus Customs · New Haven</p>
        <h1>The Catalogue</h1>
      </header>

      <section className="filters" aria-label="Filter products">
        <div className="filter-tabs" role="tablist" aria-label="Department">
          {[{ key: 'all', label: 'All' }, ...CATEGORIES, { key: 'other', label: 'Other' }].map((c) => (
            <button key={c.key} role="tab" aria-selected={cat === c.key} className={cat === c.key ? 'on' : ''}
                    onClick={() => set('cat', c.key)}>{c.label}</button>
          ))}
        </div>
        <div className="filter-row">
          <div className="filter-group" aria-label="In stock in my size">
            <span className="filter-label">In stock in my size</span>
            {SIZES.map((s) => (
              <button key={s} className={`size-chip ${size === s ? 'on' : ''}`} aria-pressed={size === s}
                      onClick={() => set('size', size === s ? '' : s)}>{s}</button>
            ))}
          </div>
          <label className="filter-group">
            <span className="filter-label">Sort</span>
            <select value={sort} onChange={(e) => set('sort', e.target.value)}>
              {SORTS.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
            </select>
          </label>
          <label className="filter-group filter-search">
            <span className="filter-label">Keyword</span>
            <input type="search" value={q} placeholder="navy, bulldog, hockey…" onChange={(e) => set('q', e.target.value)} />
          </label>
        </div>
        <p className="filter-count">
          Showing <strong>{shown.length}</strong> of {catalogue.length} items
          {filtered && <button className="link-button" onClick={() => setParams({}, { replace: true })}>Clear filters</button>}
        </p>
      </section>

      {shown.length === 0
        ? <p className="empty">Nothing on the shelf matches. Try another size, or ask the clerk.</p>
        : <div className="grid">{shown.map((p, i) => <ProductCard key={p.product_id} product={p} index={i} />)}</div>}
    </>
  )
}
