import api from './axios'

export const getParties = async (page = 1, pageSize = 20) => {
  const response = await api.get('/parties/parties/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createParty = async (data) => {
  const response = await api.post('/parties/parties/', data)
  return response.data
}

export const updateParty = async (id, data) => {
  const response = await api.put(`/parties/parties/${id}/`, data)
  return response.data
}

export const deleteParty = async (id) => {
  const response = await api.delete(`/parties/parties/${id}/`)
  return response.data
}
