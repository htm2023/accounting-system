import api from './axios'

// Employees
export const getEmployees = async (page = 1, pageSize = 20) => {
  const response = await api.get('/payroll/employees/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createEmployee = async (data) => {
  const response = await api.post('/payroll/employees/', data)
  return response.data
}

export const updateEmployee = async (id, data) => {
  const response = await api.put(`/payroll/employees/${id}/`, data)
  return response.data
}

export const deleteEmployee = async (id) => {
  const response = await api.delete(`/payroll/employees/${id}/`)
  return response.data
}

// Payslips
export const getPayslips = async (page = 1, pageSize = 20) => {
  const response = await api.get('/payroll/payslips/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createPayslip = async (data) => {
  const response = await api.post('/payroll/payslips/', data)
  return response.data
}

export const postPayslip = async (id) => {
  const response = await api.post(`/payroll/payslips/${id}/post/`)
  return response.data
}
