import api from './axios'

export const getReceiptPayments = async (page = 1, pageSize = 20) => {
  const response = await api.get('/payments/receipts-payments/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createReceiptPayment = async (data) => {
  const response = await api.post('/payments/receipts-payments/', data)
  return response.data
}

export const allocatePaymentToInvoice = async (id, invoiceId, amount) => {
  const response = await api.post(`/payments/receipts-payments/${id}/allocate/`, {
    invoice_id: invoiceId,
    amount: amount,
  })
  return response.data
}

export const postReceiptPayment = async (id) => {
  const response = await api.post(`/payments/receipts-payments/${id}/post/`)
  return response.data
}
