import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col, Tabs, Tab } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import {
  getCurrencies,
  createCurrency,
  updateCurrency,
  deleteCurrency,
  getExchangeRates,
  createExchangeRate,
  updateExchangeRate,
  deleteExchangeRate,
} from '../api/currencies'
import { getErrorMessage } from '../utils/errorHandler'

const initialCurrencyForm = {
  code: '',
  name: '',
  is_base_currency: false,
}

const initialRateForm = {
  currency: '',
  rate: '',
  date: '',
}

const Currencies = () => {
  const { t } = useTranslation()
  const [currencies, setCurrencies] = useState([])
  const [exchangeRates, setExchangeRates] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState('currencies')

  const [showModal, setShowModal] = useState(false)
  const [editingCurrency, setEditingCurrency] = useState(null)
  const [formData, setFormData] = useState(initialCurrencyForm)
  const [submitting, setSubmitting] = useState(false)

  const [showRateModal, setShowRateModal] = useState(false)
  const [editingRate, setEditingRate] = useState(null)
  const [rateFormData, setRateFormData] = useState(initialRateForm)
  const [rateSubmitting, setRateSubmitting] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const [currenciesData, ratesData] = await Promise.all([
        getCurrencies(),
        getExchangeRates(),
      ])
      setCurrencies(currenciesData.results || currenciesData)
      setExchangeRates(ratesData.results || ratesData)
    } catch (err) {
      setError(t('failedLoadCurrencies'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const getCurrencyCode = (currencyId) => {
    const currency = currencies.find((c) => c.id === currencyId)
    return currency ? currency.code : currencyId
  }

  // ===== عملة =====
  const handleOpenCreateCurrency = () => {
    setEditingCurrency(null)
    setFormData(initialCurrencyForm)
    setShowModal(true)
  }

  const handleOpenEditCurrency = (currency) => {
    setEditingCurrency(currency)
    setFormData({
      code: currency.code,
      name: currency.name,
      is_base_currency: currency.is_base_currency,
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingCurrency(null)
  }

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      if (editingCurrency) {
        await updateCurrency(editingCurrency.id, formData)
      } else {
        await createCurrency(formData)
      }
      setShowModal(false)
      setEditingCurrency(null)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveCurrency')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteCurrency = async (id) => {
    if (!window.confirm(t('confirmDeleteCurrency'))) return
    setError('')
    try {
      await deleteCurrency(id)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteCurrency')))
    }
  }

  // ===== سعر صرف =====
  const handleOpenCreateRate = () => {
    setEditingRate(null)
    setRateFormData(initialRateForm)
    setShowRateModal(true)
  }

  const handleOpenEditRate = (rate) => {
    setEditingRate(rate)
    setRateFormData({
      currency: rate.currency,
      rate: rate.rate,
      date: rate.date,
    })
    setShowRateModal(true)
  }

  const handleCloseRateModal = () => {
    setShowRateModal(false)
    setEditingRate(null)
  }

  const handleRateChange = (e) => {
    const { name, value } = e.target
    setRateFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleRateSubmit = async (e) => {
    e.preventDefault()
    setRateSubmitting(true)
    setError('')
    const payload = {
      currency: Number(rateFormData.currency),
      rate: parseFloat(rateFormData.rate),
      date: rateFormData.date,
    }
    try {
      if (editingRate) {
        await updateExchangeRate(editingRate.id, payload)
      } else {
        await createExchangeRate(payload)
      }
      setShowRateModal(false)
      setEditingRate(null)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveExchangeRate')))
    } finally {
      setRateSubmitting(false)
    }
  }

  const handleDeleteRate = async (id) => {
    if (!window.confirm(t('confirmDeleteExchangeRate'))) return
    setError('')
    try {
      await deleteExchangeRate(id)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteExchangeRate')))
    }
  }

  if (loading && currencies.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('currencies')}</h4>
        <Button variant="outline-primary" size="sm" onClick={fetchData}>
          {t('update')}
        </Button>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} className="mb-3">
        <Tab eventKey="currencies" title={t('currencies')}>
          <div className="d-flex justify-content-end mb-2">
            <Button variant="primary" size="sm" onClick={handleOpenCreateCurrency}>
              {t('addCurrency')}
            </Button>
          </div>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>{t('currencyCode')}</th>
                <th>{t('currencyName')}</th>
                <th>{t('baseCurrency')}</th>
                <th>{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {currencies.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center">{t('noCurrencies')}</td>
                </tr>
              ) : (
                currencies.map((currency) => (
                  <tr key={currency.id}>
                    <td>{currency.code}</td>
                    <td>{currency.name}</td>
                    <td>
                      {currency.is_base_currency ? <Badge bg="success" className="badge-status">{t('yes')}</Badge> : <Badge bg="secondary" className="badge-status">{t('no')}</Badge>}
                    </td>
                    <td>
                      <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEditCurrency(currency)}>
                        {t('edit')}
                      </Button>
                      <Button variant="outline-danger" size="sm" onClick={() => handleDeleteCurrency(currency.id)}>
                        {t('delete')}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </Tab>

        <Tab eventKey="exchangeRates" title={t('exchangeRates')}>
          <div className="d-flex justify-content-end mb-2">
            <Button variant="primary" size="sm" onClick={handleOpenCreateRate}>
              {t('addExchangeRate')}
            </Button>
          </div>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>{t('currency')}</th>
                <th>{t('rate')}</th>
                <th>{t('rateDate')}</th>
                <th>{t('actions')}</th>
              </tr>
            </thead>
            <tbody>
              {exchangeRates.length === 0 ? (
                <tr>
                  <td colSpan="4" className="text-center">{t('noExchangeRates')}</td>
                </tr>
              ) : (
                exchangeRates.map((rate) => (
                  <tr key={rate.id}>
                    <td>{getCurrencyCode(rate.currency)}</td>
                    <td>{rate.rate}</td>
                    <td>{rate.date}</td>
                    <td>
                      <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEditRate(rate)}>
                        {t('edit')}
                      </Button>
                      <Button variant="outline-danger" size="sm" onClick={() => handleDeleteRate(rate.id)}>
                        {t('delete')}
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </Tab>
      </Tabs>

      {/* نموذج العملة */}
      <Modal show={showModal} onHide={handleCloseModal} centered>
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingCurrency ? t('editCurrency') : t('addCurrency')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>{t('currencyCode')} *</Form.Label>
              <Form.Control type="text" name="code" value={formData.code} onChange={handleChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>{t('currencyName')} *</Form.Label>
              <Form.Control type="text" name="name" value={formData.name} onChange={handleChange} required />
            </Form.Group>
            <Form.Check
              type="checkbox"
              label={t('baseCurrency')}
              name="is_base_currency"
              checked={formData.is_base_currency}
              onChange={handleChange}
            />
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseModal}>{t('cancel')}</Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? t('saving') : t('save')}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* نموذج سعر الصرف */}
      <Modal show={showRateModal} onHide={handleCloseRateModal} centered>
        <Form onSubmit={handleRateSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingRate ? t('editExchangeRate') : t('addExchangeRate')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>{t('currency')} *</Form.Label>
              <Form.Select name="currency" value={rateFormData.currency} onChange={handleRateChange} required>
                <option value="">{t('selectCurrency')}</option>
                {currencies.map((currency) => (
                  <option key={currency.id} value={currency.id}>{currency.code} - {currency.name}</option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>{t('rate')} *</Form.Label>
              <Form.Control type="number" step="0.000001" name="rate" value={rateFormData.rate} onChange={handleRateChange} required />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>{t('rateDate')} *</Form.Label>
              <Form.Control type="date" name="date" value={rateFormData.date} onChange={handleRateChange} required />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseRateModal}>{t('cancel')}</Button>
            <Button variant="primary" type="submit" disabled={rateSubmitting}>
              {rateSubmitting ? t('saving') : t('save')}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </div>
  )
}

export default Currencies
