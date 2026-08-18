import api from './axios'

export const getJournalEntries = async (page = 1, pageSize = 20) => {
  const response = await api.get('/journal-entries/entries/', {
    params: { page, page_size: pageSize },
  })
  return response.data
}

export const createJournalEntry = async (data) => {
  const response = await api.post('/journal-entries/entries/', data)
  return response.data
}
