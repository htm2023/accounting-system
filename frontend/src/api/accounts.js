import api from './axios'

export const getAccounts = async (page = 1, pageSize = 20) => {
  const response = await api.get('/chart-of-accounts/accounts/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const getAccount = async (id) => {
  const response = await api.get(`/chart-of-accounts/accounts/${id}/`)
  return response.data
}

export const createAccount = async (data) => {
  const response = await api.post('/chart-of-accounts/accounts/', data)
  return response.data
}

export const updateAccount = async (id, data) => {
  const response = await api.put(`/chart-of-accounts/accounts/${id}/`, data)
  return response.data
}

export const deleteAccount = async (id) => {
  const response = await api.delete(`/chart-of-accounts/accounts/${id}/`)
  return response.data
}
