import api from './axios'

export const getFiscalPeriods = async () => {
  const response = await api.get('/fiscal/periods/')
  return response.data
}

export const getFiscalYears = async () => {
  const response = await api.get('/fiscal/years/')
  return response.data
}
