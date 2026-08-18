import api from './axios'

export const getCurrencies = async (page = 1, pageSize = 20) => {
  const response = await api.get('/currencies/currencies/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createCurrency = async (data) => {
  const response = await api.post('/currencies/currencies/', data)
  return response.data
}

export const updateCurrency = async (id, data) => {
  const response = await api.put(`/currencies/currencies/${id}/`, data)
  return response.data
}

export const deleteCurrency = async (id) => {
  const response = await api.delete(`/currencies/currencies/${id}/`)
  return response.data
}

export const getExchangeRates = async (page = 1, pageSize = 20) => {
  const response = await api.get('/currencies/exchange-rates/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createExchangeRate = async (data) => {
  const response = await api.post('/currencies/exchange-rates/', data)
  return response.data
}

export const updateExchangeRate = async (id, data) => {
  const response = await api.put(`/currencies/exchange-rates/${id}/`, data)
  return response.data
}

export const deleteExchangeRate = async (id) => {
  const response = await api.delete(`/currencies/exchange-rates/${id}/`)
  return response.data
}
