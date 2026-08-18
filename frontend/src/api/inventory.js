import api from './axios'

export const getProducts = async (page = 1, pageSize = 20) => {
  const response = await api.get('/inventory/products/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const getStockMovements = async (page = 1, pageSize = 20) => {
  const response = await api.get('/inventory/stock-movements/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createProduct = async (data) => {
  const response = await api.post('/inventory/products/', data)
  return response.data
}
