import api from './axios'

export const getTrialBalance = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/trial-balance/', { params })
  return response.data
}

export const getIncomeStatement = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/income-statement/', { params })
  return response.data
}

export const getBalanceSheet = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/balance-sheet/', { params })
  return response.data
}

export const getCashFlow = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/cash-flow/', { params })
  return response.data
}

export const getPartyStatement = async (partyId) => {
  const response = await api.get(`/reports/party-statement/${partyId}/`)
  return response.data
}

export const exportTrialBalance = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/trial-balance/export/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportIncomeStatement = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/income-statement/export/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportBalanceSheet = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/balance-sheet/export/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportCashFlow = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/cash-flow/export/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportPartyStatement = async (partyId) => {
  const response = await api.get(`/reports/party-statement/${partyId}/export/`, {
    responseType: 'blob',
  })
  return response.data
}

export const exportTrialBalancePDF = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/trial-balance/export-pdf/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportIncomeStatementPDF = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/income-statement/export-pdf/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportBalanceSheetPDF = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/balance-sheet/export-pdf/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportCashFlowPDF = async (fiscalPeriodId = null) => {
  const params = fiscalPeriodId ? { fiscal_period: fiscalPeriodId } : {}
  const response = await api.get('/reports/cash-flow/export-pdf/', {
    params,
    responseType: 'blob',
  })
  return response.data
}

export const exportPartyStatementPDF = async (partyId) => {
  const response = await api.get(`/reports/party-statement/${partyId}/export-pdf/`, {
    responseType: 'blob',
  })
  return response.data
}
