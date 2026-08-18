import api from './axios'

export const getCostCenters = async (page = 1, pageSize = 20) => {
  const response = await api.get('/cost-centers/cost-centers/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createCostCenter = async (data) => {
  const response = await api.post('/cost-centers/cost-centers/', data)
  return response.data
}

export const updateCostCenter = async (id, data) => {
  const response = await api.put(`/cost-centers/cost-centers/${id}/`, data)
  return response.data
}

export const deleteCostCenter = async (id) => {
  const response = await api.delete(`/cost-centers/cost-centers/${id}/`)
  return response.data
}
