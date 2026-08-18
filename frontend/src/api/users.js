import api from './axios'

export const getUsers = async (page = 1, pageSize = 20) => {
  const response = await api.get('/auth/users/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createUser = async (data) => {
  const response = await api.post('/auth/users/', data)
  return response.data
}

export const updateUser = async (id, data) => {
  const response = await api.put(`/auth/users/${id}/`, data)
  return response.data
}

export const deleteUser = async (id) => {
  const response = await api.delete(`/auth/users/${id}/`)
  return response.data
}
