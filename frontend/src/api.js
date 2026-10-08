const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`)
  return res.json()
}

export const listCases = () => request('/cases')
export const getCase = (id) => request(`/cases/${encodeURIComponent(id)}`)
export const analyzeCase = (id) =>
  request(`/cases/${encodeURIComponent(id)}/analyze`, {
    method: 'POST',
    body: JSON.stringify({ operator_id: 'demo-operator' }),
  })
