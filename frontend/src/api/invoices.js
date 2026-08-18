import api from './axios'

export const getInvoices = async (page = 1, pageSize = 20) => {
  const response = await api.get('/invoicing/invoices/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createInvoice = async (data) => {
  const response = await api.post('/invoicing/invoices/', data)
  return response.data
}

export const postInvoice = async (id) => {
  const response = await api.post(`/invoicing/invoices/${id}/post/`)
  return response.data
}

export const downloadInvoicePDF = async (id) => {
  const response = await api.get(`/invoicing/invoices/${id}/pdf/`, {
    responseType: 'blob',
  })
  return response.data
}
