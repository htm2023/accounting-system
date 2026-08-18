import api from './axios'

// Fixed Assets
export const getFixedAssets = async (page = 1, pageSize = 20) => {
  const response = await api.get('/fixed-assets/assets/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createFixedAsset = async (data) => {
  const response = await api.post('/fixed-assets/assets/', data)
  return response.data
}

export const updateFixedAsset = async (id, data) => {
  const response = await api.put(`/fixed-assets/assets/${id}/`, data)
  return response.data
}

export const deleteFixedAsset = async (id) => {
  const response = await api.delete(`/fixed-assets/assets/${id}/`)
  return response.data
}

// Depreciation Schedules
export const getDepreciationSchedules = async (page = 1, pageSize = 20) => {
  const response = await api.get('/fixed-assets/depreciation-schedules/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createDepreciationSchedule = async (data) => {
  const response = await api.post('/fixed-assets/depreciation-schedules/', data)
  return response.data
}

export const updateDepreciationSchedule = async (id, data) => {
  const response = await api.put(`/fixed-assets/depreciation-schedules/${id}/`, data)
  return response.data
}

export const deleteDepreciationSchedule = async (id) => {
  const response = await api.delete(`/fixed-assets/depreciation-schedules/${id}/`)
  return response.data
}

export const postDepreciationSchedule = async (id) => {
  const response = await api.post(`/fixed-assets/depreciation-schedules/${id}/post/`)
  return response.data
}
