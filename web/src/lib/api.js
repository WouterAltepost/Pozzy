import { supabase } from './supabase'

const BASE = (import.meta.env.VITE_API_BASE || '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(code, message, status) {
    super(message)
    this.name = 'ApiError'
    this.code = code
    this.status = status
  }
}

/**
 * Fetch wrapper for the Flask API.
 * Adds the Supabase access token, unwraps the {data, error} envelope,
 * and throws ApiError when the request or the envelope reports an error.
 */
export async function api(path, { method = 'GET', body } = {}) {
  const { data: { session } } = await supabase.auth.getSession()

  const headers = { Accept: 'application/json' }
  if (session?.access_token) headers.Authorization = `Bearer ${session.access_token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    throw new ApiError('network_error', `Could not reach the API: ${err.message}`, 0)
  }

  let payload = null
  try {
    payload = await res.json()
  } catch {
    // Non-JSON body (proxy error page, empty response). Fall through to status handling.
  }

  if (payload?.error) {
    throw new ApiError(payload.error.code, payload.error.message, res.status)
  }
  if (!res.ok) {
    throw new ApiError('http_error', `HTTP ${res.status}`, res.status)
  }
  return payload?.data ?? null
}
