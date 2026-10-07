import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { fetchMe, fetchProducts, getToken, setToken, type AuthResponse, type Product, type User } from './api'

type ChatResults = { query: string; products: Product[] } | null

type Store = {
  user: User | null
  signIn: (auth: AuthResponse) => void
  signOut: () => void
  catalogue: Product[]
  catalogueError: string
  chatResults: ChatResults
  setChatResults: (r: ChatResults) => void
  chatOpen: boolean
  setChatOpen: (open: boolean) => void
}

const StoreContext = createContext<Store | null>(null)

export function StoreProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [catalogue, setCatalogue] = useState<Product[]>([])
  const [catalogueError, setCatalogueError] = useState('')
  const [chatResults, setChatResults] = useState<ChatResults>(null)
  const [chatOpen, setChatOpen] = useState(false)

  // Restore the session from a saved token, and load the catalogue once for every page.
  useEffect(() => {
    if (getToken()) fetchMe().then(setUser).catch(() => setToken(null))
    fetchProducts().then(setCatalogue).catch((e: Error) => setCatalogueError(e.message))
  }, [])

  const signIn = (auth: AuthResponse) => { setToken(auth.token); setUser(auth.user) }
  const signOut = () => { setToken(null); setUser(null) }

  return (
    <StoreContext.Provider value={{ user, signIn, signOut, catalogue, catalogueError, chatResults,
      setChatResults, chatOpen, setChatOpen }}>
      {children}
    </StoreContext.Provider>
  )
}

// eslint-disable-next-line react-refresh/only-export-components
export function useStore() {
  const store = useContext(StoreContext)
  if (!store) throw new Error('useStore must be used inside StoreProvider')
  return store
}
