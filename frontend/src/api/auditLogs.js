import api from './axios'

export const getAuditLogs = async (params = {}, page = 1, pageSize = 20) => {
  const response = await api.get('/audit/logs/', {
    params: { ...params, page, page_size: pageSize },
  })
  return response.data
}
