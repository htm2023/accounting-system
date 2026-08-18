export const getErrorMessage = (err, fallbackMessage = 'حدث خطأ غير متوقع') => {
  if (err?.response?.data) {
    const data = err.response.data
    // DRF يضع الرسالة غالبًا في detail أو non_field_errors أو error أو message
    if (typeof data.detail === 'string') return data.detail
    if (typeof data.error === 'string') return data.error
    if (typeof data.message === 'string') return data.message
    if (typeof data.non_field_errors === 'string') return data.non_field_errors
    // إذا كانت البيانات object يحتوي على أخطاء حقول
    const firstKey = Object.keys(data)[0]
    if (firstKey && typeof data[firstKey] === 'string') return data[firstKey]
    if (firstKey && Array.isArray(data[firstKey]) && data[firstKey].length > 0) return data[firstKey][0]
  }
  if (err?.message) return err.message
  return fallbackMessage
}
