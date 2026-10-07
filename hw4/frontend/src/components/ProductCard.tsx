import { Link } from 'react-router-dom'
import { formatPrice, type Product } from '../api'
import { styleNo } from '../catalog'
import { useStore } from '../store'

// A catalogue plate: a print-toned photo that blooms to full color on hover, with a swinging price tag.
export default function ProductCard({ product, index = 0 }: { product: Product; index?: number }) {
  const { catalogue } = useStore()
  return (
    <Link to={`/products/${product.product_id}`} className="plate" style={{ animationDelay: `${Math.min(index, 16) * 40}ms` }}>
      <div className="plate-photo">
        <img src={product.image_url} alt={product.name} loading="lazy" />
        <span className="hangtag">
          <span className="hangtag-hole" />
          {formatPrice(product.price)}
        </span>
      </div>
      <div className="plate-body">
        <p className="plate-no">{styleNo(product.product_id, catalogue)} · {product.garment_type}</p>
        <h3>{product.name}</h3>
        <p className="plate-desc">{product.description}</p>
      </div>
    </Link>
  )
}
