import { apiUrl } from './apiBase'

const ACCOUNTS_URL = '/accounts'
let csrfToken = ''
let refreshCookiePresent = false

const fieldLabels = {
  confirm_password: 'Confirm password',
  detail: '',
  email: 'Email',
  first_name: 'First name',
  last_name: 'Last name',
  password: 'Password',
  phone_number: 'Phone number',
  non_field_errors: '',
}

export class AuthApiError extends Error {
  constructor(message, statusCode = 0, data = null) {
    super(message)
    this.name = 'AuthApiError'
    this.status = statusCode
    this.data = data
  }
}

function firstErrorMessage(value, key = '') {
  if (typeof value === 'string') {
    const label = fieldLabels[key] ?? key
    return label ? `${label}: ${value}` : value
  }

  if (Array.isArray(value)) {
    for (const item of value) {
      const message = firstErrorMessage(item, key)
      if (message) return message
    }
    return ''
  }

  if (value && typeof value === 'object') {
    for (const [nestedKey, nestedValue] of Object.entries(value)) {
      const message = firstErrorMessage(nestedValue, nestedKey)
      if (message) return message
    }
  }

  return ''
}

export async function readAuthResponse(response) {
  let data = null
  if (response.status !== 204) {
    try {
      data = await response.json()
    } catch (error) {
      if (error instanceof SyntaxError) {
        throw new AuthApiError('The authentication API returned an invalid response.', response.status)
      }
      throw error
    }
  }

  if (!response.ok) {
    const message = firstErrorMessage(data) || `Authentication request failed with HTTP ${response.status}.`
    throw new AuthApiError(message, response.status, data)
  }

  return data
}

async function fetchAccounts(path, options = {}) {
  try {
    return await fetch(apiUrl(`${ACCOUNTS_URL}${path}`), {
      ...options,
      credentials: 'include',
      headers: { Accept: 'application/json', ...options.headers },
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new AuthApiError('Unable to reach the FreshBasket account API. Check that the backend is running.')
  }
}

export async function getCsrfToken({ force = false } = {}) {
  if (csrfToken && !force) return csrfToken

  const response = await fetchAccounts('/csrf/')
  const data = await readAuthResponse(response)
  if (typeof data?.csrf_token !== 'string' || !data.csrf_token) {
    throw new AuthApiError('The account API did not provide a CSRF token.')
  }
  csrfToken = data.csrf_token
  refreshCookiePresent = Boolean(data.refresh_cookie_present)
  return csrfToken
}

export function hasRefreshCookie() {
  return refreshCookiePresent
}

async function postJson(path, payload) {
  const token = await getCsrfToken()
  const response = await fetchAccounts(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': token,
    },
    body: JSON.stringify(payload),
  })
  return readAuthResponse(response)
}

export function registerCustomer(payload) {
  return postJson('/register/', payload)
}

export function loginCustomer(payload) {
  return postJson('/login/', payload)
}

export function refreshCustomerSession() {
  return postJson('/token/refresh/', {})
}

export function logoutCustomer() {
  return postJson('/logout/', {})
}

export function requestPasswordReset(email) {
  return postJson('/password-reset/', { email })
}

export function confirmPasswordReset(payload) {
  return postJson('/password-reset/confirm/', payload)
}

export async function fetchWithAccessToken(path, accessToken, options = {}) {
  const method = (options.method ?? 'GET').toUpperCase()
  const headers = new Headers(options.headers ?? {})
  headers.set('Accept', 'application/json')
  if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`)

  if (!['GET', 'HEAD', 'OPTIONS', 'TRACE'].includes(method)) {
    const token = await getCsrfToken()
    headers.set('X-CSRFToken', token)
  }

  try {
    return await fetch(apiUrl(path), {
      ...options,
      method,
      headers,
      credentials: 'include',
    })
  } catch (error) {
    if (error.name === 'AbortError') throw error
    throw new AuthApiError('Unable to reach the FreshBasket API. Check that the backend is running.')
  }
}
