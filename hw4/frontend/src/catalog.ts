import type { Product } from './api'

// The catalogue spells garment types 22 different ways; shoppers think in six departments.
export const CATEGORIES = [
  { key: 'hoodies', label: 'Hoodies', blurb: 'Pullovers & full-zips for the walk to Sterling' },
  { key: 'crewnecks', label: 'Crewnecks', blurb: 'The reverse-weave staple of every quad' },
  { key: 'tees', label: 'Tees & Tops', blurb: 'Game-day tees and track shirts' },
  { key: 'quarter-zips', label: 'Quarter-Zips', blurb: 'College & school zips for seminar' },
  { key: 'jackets', label: 'Jackets & Fleece', blurb: 'Bombers and fleece for November' },
] as const

export type CategoryKey = (typeof CATEGORIES)[number]['key'] | 'other'

export function categoryOf(p: Pick<Product, 'garment_type'>): CategoryKey {
  const t = p.garment_type.toLowerCase()
  if (t.includes('quarter-zip')) return 'quarter-zips'
  if (t.includes('hood')) return 'hoodies'
  if (t.includes('jacket') || t.includes('fleece')) return 'jackets'
  if (t.includes('crewneck') || t.includes('mockneck') || t.includes('sweatshirt')) return 'crewnecks'
  if (t.includes('shirt') || t.includes('tee')) return 'tees'
  return 'other'
}

export const SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL']

// Fabric swatches for the color names used in the catalogue.
const SWATCHES: [RegExp, string][] = [
  [/navy|dark blue/, '#1b2a4a'], [/yale blue|royal/, '#00356b'], [/light blue|sky|carolina/, '#8fb3d9'],
  [/blue/, '#2c4f86'], [/charcoal/, '#3d3d40'], [/heather|gray|grey/, '#9a9a98'], [/black/, '#1c1c1c'],
  [/white|ivory/, '#f8f6f0'], [/cream|natural|oatmeal/, '#ece0c4'], [/maroon|burgundy|cardinal/, '#6b1324'],
  [/red|crimson/, '#a8202e'], [/green|forest/, '#2e4a3b'], [/gold|yellow/, '#c9a13b'], [/orange/, '#d2691e'],
  [/pink/, '#e7a1b0'], [/purple/, '#5b3b7a'], [/brown|tan|khaki/, '#8a6b47'],
]
export function swatch(color: string): string {
  const c = color.toLowerCase()
  return SWATCHES.find(([re]) => re.test(c))?.[1] ?? '#c8b998'
}

// A catalogue "style number" from the product's place in the alphabetical catalogue.
export function styleNo(productId: string, catalogue: Product[]): string {
  const i = catalogue.findIndex((p) => p.product_id === productId)
  return i < 0 ? '' : `No. ${String(i + 1).padStart(3, '0')}`
}
