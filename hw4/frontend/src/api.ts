export type StockLine = { size: string; quantity: number; in_stock?: boolean }

export type Product = {
  product_id: string
  name: string
  garment_type: string
  description: string
  colors?: string[]
  price: number
  image_url: string
  total_stock?: number
  sizes_in_stock?: string[]
  inventory?: StockLine[]
}

export type User = { id: number; first_name: string; last_name: string; email: string }
export type AuthResponse = { token: string; user: User }
export type ChatTurn = { role: 'user' | 'assistant'; content: string }
export type ChatReply = { reply: string; products: Product[]; blocked?: boolean; removed?: string[] }
export type SavedTurn = ChatTurn & { created_at: string; page: string | null; products: Product[] }

const TOKEN_KEY = 'cc_token'
export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t: string | null) =>
  t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY)

async function request<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Bearer ${token}`
  const res = await fetch(url, { ...init, headers: { ...headers, ...(init.headers as object) } })
  if (!res.ok) {
    const body = await res.json().catch(() => null)
    const detail = body?.detail
    const message = typeof detail === 'string' ? detail
      : Array.isArray(detail) ? detail.map((d: { msg: string }) => d.msg).join('; ')
      : `${res.status} ${res.statusText}`
    throw new Error(message)
  }
  return res.json() as Promise<T>
}

export const fetchProducts = () => request<Product[]>('/api/products')
export const fetchProduct = (id: string) => request<Product>(`/api/products/${encodeURIComponent(id)}`)

export const login = (email: string, password: string) =>
  request<AuthResponse>('/api/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) })
export const register = (body: { first_name: string; last_name: string; email: string; password: string }) =>
  request<AuthResponse>('/api/auth/register', { method: 'POST', body: JSON.stringify(body) })
export const fetchMe = () => request<User>('/api/auth/me')

export const sendChat = (message: string, history: ChatTurn[], page: string, viewing: string[]) =>
  request<ChatReply>('/api/chat', { method: 'POST', body: JSON.stringify({ message, history, page, viewing }) })
export const fetchChatHistory = () => request<{ turns: SavedTurn[] }>('/api/chat/history')
export const deleteChatHistory = () => request<{ deleted: number }>('/api/chat/history', { method: 'DELETE' })

export const formatPrice = (price: number) => `$${price.toFixed(2)}`
