import { api } from '../lib/api'

export const listNotes = ({ area_id, tag, q } = {}) => {
  const params = new URLSearchParams()
  if (area_id) params.set('area_id', area_id)
  if (tag) params.set('tag', tag)
  if (q) params.set('q', q)
  const s = params.toString()
  return api(`/api/notes${s ? '?' + s : ''}`)
}
export const getNote = (id) => api(`/api/notes/${id}`)
export const createNote = (body) => api('/api/notes', { method: 'POST', body })
export const updateNote = (id, body) => api(`/api/notes/${id}`, { method: 'PATCH', body })
export const deleteNote = (id) => api(`/api/notes/${id}`, { method: 'DELETE' })
