import { useEffect, useState } from 'react'
import {
  ArrowLeft,
  ArrowRight,
  Eye,
  EyeOff,
  Leaf,
  LoaderCircle,
  LogOut,
  ShieldCheck,
} from 'lucide-react'
import Footer from '../components/Footer'
import { useAuth } from '../context/useAuth'
import { confirmPasswordReset, readAuthResponse, requestPasswordReset } from '../services/auth'

function AuthShell({ children, onNavigate, eyebrow, title, description }) {
  return (
    <div className="auth-page">
      <header className="auth-topbar page-shell">
        <a
          className="auth-brand"
          href="/"
          onClick={(event) => {
            event.preventDefault()
            onNavigate('/')
          }}
        >
          <span className="brand-mark"><Leaf size={21} /></span>
          <span className="brand-name">fresh<span>basket</span><small>GOOD FOOD, GOOD DAYS</small></span>
        </a>
        <a
          className="auth-back-link"
          href="/"
          onClick={(event) => {
            event.preventDefault()
            onNavigate('/')
          }}
        >
          <ArrowLeft size={16} /> Continue shopping
        </a>
      </header>

      <main className="auth-main page-shell">
        <aside className="auth-story">
          <span className="auth-story-eyebrow"><Leaf size={15} /> A fresher everyday</span>
          <h1>Good food starts with a good day.</h1>
          <p>Sign in to keep your FreshBasket favourites close and make everyday shopping feel a little easier.</p>
          <div className="auth-story-points">
            <span><ShieldCheck size={17} /> Your account stays yours</span>
            <span><Leaf size={17} /> Thoughtful groceries, all in one place</span>
          </div>
          <div className="auth-story-art" aria-hidden="true">
            <img
              src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=960&q=85"
              alt=""
              onError={(event) => {
                event.currentTarget.style.visibility = 'hidden'
              }}
            />
            <div className="auth-art-caption">
              <span>Goodness, picked with care</span>
              <strong>Fresh choices for your table.</strong>
            </div>
          </div>
        </aside>

        <section className="auth-card" aria-labelledby="auth-title">
          <div className="auth-card-heading">
            <span className="auth-eyebrow">{eyebrow}</span>
            <h2 id="auth-title">{title}</h2>
            <p>{description}</p>
          </div>
          {children}
        </section>
      </main>
      <Footer onNavigate={onNavigate} />
    </div>
  )
}

function PasswordInput({ id, label, value, onChange, autoComplete, required = true }) {
  const [visible, setVisible] = useState(false)

  return (
    <label className="auth-field" htmlFor={id}>
      <span>{label}</span>
      <span className="auth-password-wrap">
        <input
          id={id}
          name={id}
          type={visible ? 'text' : 'password'}
          value={value}
          onChange={onChange}
          autoComplete={autoComplete}
          minLength={id === 'password' ? 8 : undefined}
          required={required}
        />
        <button
          className="auth-password-toggle"
          type="button"
          onClick={() => setVisible((current) => !current)}
          aria-label={visible ? `Hide ${label.toLowerCase()}` : `Show ${label.toLowerCase()}`}
        >
          {visible ? <EyeOff size={17} /> : <Eye size={17} />}
        </button>
      </span>
    </label>
  )
}

function AuthSubmit({ busy, children }) {
  return (
    <button className="auth-submit" type="submit" disabled={busy}>
      {busy ? <LoaderCircle size={18} className="auth-spinner" /> : <>{children}<ArrowRight size={17} /></>}
    </button>
  )
}

export function LoginPage({ onNavigate, onSuccess }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      const user = await login({ email, password })
      onSuccess(`Welcome back${user.first_name ? `, ${user.first_name}` : ''}.`)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell
      onNavigate={onNavigate}
      eyebrow="Welcome back"
      title="Sign in to FreshBasket"
      description="Your everyday favourites are only a moment away."
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        {error && <div className="auth-alert" role="alert">{error}</div>}
        <label className="auth-field" htmlFor="login-email">
          <span>Email address</span>
          <input
            id="login-email"
            name="email"
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            autoComplete="email"
            required
          />
        </label>
        <PasswordInput
          id="password"
          label="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
        />
        <AuthSubmit busy={busy}>Sign in</AuthSubmit>
      </form>
      <p className="auth-switch">
        New to FreshBasket? <a href="/register" onClick={(event) => {
          event.preventDefault()
          onNavigate('/register')
        }}>Create an account</a> · <a href="/forgot-password" onClick={(event) => { event.preventDefault(); onNavigate('/forgot-password') }}>Forgot password?</a>
      </p>
    </AuthShell>
  )
}

export function ForgotPasswordPage({ onNavigate }) {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event) {
    event.preventDefault(); setBusy(true); setError(''); setMessage('')
    try { setMessage((await requestPasswordReset(email)).detail) } catch (requestError) { setError(requestError.message) } finally { setBusy(false) }
  }
  return <AuthShell onNavigate={onNavigate} eyebrow="Account recovery" title="Reset your password" description="We’ll send a secure, time-limited reset link if an account exists for that email.">
    <form className="auth-form" onSubmit={submit}>{error && <div className="auth-alert" role="alert">{error}</div>}{message && <div className="auth-notice" role="status">{message}</div>}
      <label className="auth-field" htmlFor="reset-email"><span>Email address</span><input id="reset-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
      <AuthSubmit busy={busy}>Send reset link</AuthSubmit>
    </form>
  </AuthShell>
}

export function ResetPasswordPage({ onNavigate, uid, token }) {
  const [password, setPassword] = useState(''); const [confirm, setConfirm] = useState(''); const [message, setMessage] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  async function submit(event) { event.preventDefault(); setBusy(true); setError(''); try { setMessage((await confirmPasswordReset({ uid, token, new_password: password, confirm_password: confirm })).detail) } catch (requestError) { setError(requestError.message) } finally { setBusy(false) } }
  return <AuthShell onNavigate={onNavigate} eyebrow="Account recovery" title="Choose a new password" description="Use at least eight characters and keep your account secure.">
    <form className="auth-form" onSubmit={submit}>{error && <div className="auth-alert" role="alert">{error}</div>}{message && <div className="auth-notice" role="status">{message} <button type="button" className="orders-link-button" onClick={() => onNavigate('/login')}>Sign in</button></div>}
      <PasswordInput id="password" label="New password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="new-password" /><PasswordInput id="confirm_password" label="Confirm password" value={confirm} onChange={(event) => setConfirm(event.target.value)} autoComplete="new-password" /><AuthSubmit busy={busy}>Update password</AuthSubmit>
    </form>
  </AuthShell>
}

export function RegisterPage({ onNavigate, onSuccess }) {
  const { register } = useAuth()
  const [form, setForm] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone_number: '',
    password: '',
    confirm_password: '',
  })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  function updateField(event) {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setBusy(true)
    try {
      await register(form)
      onSuccess('Your FreshBasket account is ready.')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <AuthShell
      onNavigate={onNavigate}
      eyebrow="A little more FreshBasket"
      title="Create your account"
      description="A few details, then your everyday favourites are easier to find."
    >
      <form className="auth-form auth-register-form" onSubmit={handleSubmit}>
        {error && <div className="auth-alert" role="alert">{error}</div>}
        <div className="auth-field-row">
          <label className="auth-field" htmlFor="first_name">
            <span>First name</span>
            <input id="first_name" name="first_name" value={form.first_name} onChange={updateField} autoComplete="given-name" required />
          </label>
          <label className="auth-field" htmlFor="last_name">
            <span>Last name</span>
            <input id="last_name" name="last_name" value={form.last_name} onChange={updateField} autoComplete="family-name" required />
          </label>
        </div>
        <label className="auth-field" htmlFor="register-email">
          <span>Email address</span>
          <input
            id="register-email"
            name="email"
            type="email"
            value={form.email}
            onChange={updateField}
            autoComplete="email"
            required
          />
        </label>
        <label className="auth-field" htmlFor="phone_number">
          <span>Phone number</span>
          <input
            id="phone_number"
            name="phone_number"
            type="tel"
            value={form.phone_number}
            onChange={updateField}
            autoComplete="tel"
            pattern="\+?[1-9]\d{6,14}"
            title="Enter 7 to 15 digits, optionally prefixed by +."
            required
          />
        </label>
        <PasswordInput
          id="password"
          label="Password"
          value={form.password}
          onChange={updateField}
          autoComplete="new-password"
        />
        <PasswordInput
          id="confirm_password"
          label="Confirm password"
          value={form.confirm_password}
          onChange={updateField}
          autoComplete="new-password"
        />
        <AuthSubmit busy={busy}>Create account</AuthSubmit>
      </form>
      <p className="auth-switch">
        Already have an account? <a href="/login" onClick={(event) => {
          event.preventDefault()
          onNavigate('/login')
        }}>Sign in</a>
      </p>
    </AuthShell>
  )
}

export function AccountPage({ message, onNavigate, onLogout }) {
  const { authError, authenticatedFetch, isLoading, updateProfile, user } = useAuth()
  const [profile, setProfile] = useState(null)
  const [profileLoading, setProfileLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(message)
  const userId = user?.id

  useEffect(() => {
    if (isLoading) return undefined
    if (!userId) {
      onNavigate('/login')
      return undefined
    }

    const controller = new AbortController()
    authenticatedFetch('/api/accounts/profile/', { signal: controller.signal })
      .then(readAuthResponse)
      .then(setProfile)
      .catch((requestError) => {
        if (requestError.name !== 'AbortError') setError(requestError.message)
      })
      .finally(() => {
        if (!controller.signal.aborted) setProfileLoading(false)
      })

    return () => controller.abort()
  }, [authenticatedFetch, isLoading, onNavigate, userId])

  function updateField(event) {
    setProfile((current) => ({ ...current, [event.target.name]: event.target.value }))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSuccess('')
    setBusy(true)
    try {
      const updatedProfile = await updateProfile(profile)
      setProfile(updatedProfile)
      setSuccess('Your profile has been updated.')
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  if (isLoading || profileLoading) {
    return (
      <main className="account-page">
        <div className="account-loading"><LoaderCircle className="auth-spinner" size={24} /> Loading your account…</div>
      </main>
    )
  }

  if (!user) {
    return (
      <main className="account-page">
        <div className="account-loading">{authError || 'Taking you to sign in…'}</div>
      </main>
    )
  }

  return (
    <div className="account-page">
      <header className="account-topbar page-shell">
        <a className="auth-brand" href="/" onClick={(event) => {
          event.preventDefault()
          onNavigate('/')
        }}>
          <span className="brand-mark"><Leaf size={21} /></span>
          <span className="brand-name">fresh<span>basket</span><small>GOOD FOOD, GOOD DAYS</small></span>
        </a>
        <button className="account-signout" type="button" onClick={onLogout}>
          <LogOut size={16} /> Sign out
        </button>
      </header>
      <main className="account-main page-shell">
        <div className="account-heading">
          <span className="auth-eyebrow">Your FreshBasket</span>
          <h1>Hello, {profile?.first_name || user.first_name || 'there'}.</h1>
          <p>Manage your account details here.</p>
          <button className="button button-secondary account-orders-link" type="button" onClick={() => onNavigate('/orders')}>
            <ArrowRight size={16} /> View my orders
          </button>
        </div>
        <section className="account-card">
          {success && <div className="auth-success" role="status">{success}</div>}
          {error && <div className="auth-alert" role="alert">{error}</div>}
          {!profile ? (
            <p className="account-fallback">Your profile could not be loaded. {authError}</p>
          ) : (
            <form className="auth-form account-form" onSubmit={handleSubmit}>
              <div className="auth-field-row">
                <label className="auth-field" htmlFor="profile-first-name">
                  <span>First name</span>
                  <input id="profile-first-name" name="first_name" value={profile.first_name ?? ''} onChange={updateField} autoComplete="given-name" required />
                </label>
                <label className="auth-field" htmlFor="profile-last-name">
                  <span>Last name</span>
                  <input id="profile-last-name" name="last_name" value={profile.last_name ?? ''} onChange={updateField} autoComplete="family-name" required />
                </label>
              </div>
              <label className="auth-field" htmlFor="profile-email">
                <span>Email address</span>
                <input id="profile-email" name="email" type="email" value={profile.email ?? ''} onChange={updateField} autoComplete="email" required />
              </label>
              <label className="auth-field" htmlFor="profile-phone">
                <span>Phone number</span>
                <input
                  id="profile-phone"
                  name="phone_number"
                  type="tel"
                  value={profile.phone_number ?? ''}
                  onChange={updateField}
                  autoComplete="tel"
                  pattern="\+?[1-9]\d{6,14}"
                  title="Enter 7 to 15 digits, optionally prefixed by +."
                  required
                />
              </label>
              <button className="auth-submit" type="submit" disabled={busy}>
                {busy ? <LoaderCircle size={18} className="auth-spinner" /> : <>Save changes <ArrowRight size={17} /></>}
              </button>
            </form>
          )}
        </section>
      </main>
      <Footer onNavigate={onNavigate} />
    </div>
  )
}
