import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api'
import { useStore } from '../store'

export default function CreateAccount() {
  const { signIn } = useStore()
  const navigate = useNavigate()
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const set = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [key]: e.target.value })

  async function submit(e: FormEvent) {
    e.preventDefault()
    setError('')
    if (form.password.length < 8) return setError('Password must be at least 8 characters.')
    if (form.password !== form.confirm) return setError('Passwords do not match.')
    setBusy(true)
    try {
      const { confirm: _confirm, ...body } = form
      signIn(await register(body))
      navigate('/')
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="form-page index-card">
      <p className="kicker">Join the shop</p>
      <h1>Create account</h1>
      <form onSubmit={submit}>
        <label>First name<input autoComplete="given-name" required value={form.first_name} onChange={set('first_name')} /></label>
        <label>Last name<input autoComplete="family-name" required value={form.last_name} onChange={set('last_name')} /></label>
        <label>Email<input type="email" autoComplete="email" required value={form.email} onChange={set('email')} /></label>
        <label>Password<input type="password" autoComplete="new-password" required value={form.password} onChange={set('password')} /></label>
        <label>Confirm password<input type="password" autoComplete="new-password" required value={form.confirm} onChange={set('confirm')} /></label>
        {error && <p className="error">{error}</p>}
        <button type="submit" className="button" disabled={busy}>{busy ? 'Creating…' : 'Create account'}</button>
      </form>
      <p className="muted">Already have an account? <Link to="/login">Log in</Link></p>
    </section>
  )
}
