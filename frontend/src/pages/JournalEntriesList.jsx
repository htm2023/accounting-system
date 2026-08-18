import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { getJournalEntries, createJournalEntry } from '../api/journalEntries'
import { getAccounts } from '../api/accounts'
import { getFiscalPeriods, getFiscalYears } from '../api/fiscal'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const JournalEntriesList = () => {
  const role = useSelector((state) => state.auth.user?.role)
  const canManage = role === 'Admin' || role === 'Accountant'
  const [entries, setEntries] = useState([])
  const [accounts, setAccounts] = useState([])
  const [fiscalPeriods, setFiscalPeriods] = useState([])
  const [fiscalYears, setFiscalYears] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  // نموذج القيد
  const [formData, setFormData] = useState({
    fiscal_period: '',
    date: '',
    description: '',
    reference: '',
    lines: [
      { account: '', debit: 0, credit: 0, description: '' },
      { account: '', debit: 0, credit: 0, description: '' },
    ],
  })

  const { t } = useTranslation()

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [entriesData, accountsData, periodsData, yearsData] = await Promise.all([
        getJournalEntries(page),
        getAccounts(),
        getFiscalPeriods(),
        getFiscalYears(),
      ])
      setEntries(entriesData.results)
      setCurrentPage(entriesData.current_page || 1)
      setTotalPages(entriesData.total_pages || 1)
      setTotalCount(entriesData.count || 0)
      setAccounts(accountsData.results || accountsData)
      setFiscalPeriods(periodsData.results || periodsData)
      setFiscalYears(yearsData.results || yearsData)
    } catch (err) {
      setError(t('failedLoadEntries'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const handleOpenCreate = () => {
    setFormData({
      fiscal_period: '',
      date: new Date().toISOString().slice(0, 10),
      description: '',
      reference: '',
      lines: [
        { account: '', debit: 0, credit: 0, description: '' },
        { account: '', debit: 0, credit: 0, description: '' },
      ],
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
  }

  const handleFormChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleLineChange = (index, field, value) => {
    setFormData((prev) => {
      const lines = [...prev.lines]
      lines[index] = { ...lines[index], [field]: value }
      return { ...prev, lines }
    })
  }

  const addLine = () => {
    setFormData((prev) => ({
      ...prev,
      lines: [...prev.lines, { account: '', debit: 0, credit: 0, description: '' }],
    }))
  }

  const removeLine = (index) => {
    setFormData((prev) => {
      const lines = prev.lines.filter((_, i) => i !== index)
      return { ...prev, lines }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        fiscal_period: Number(formData.fiscal_period),
        date: formData.date,
        description: formData.description,
        reference: formData.reference || null,
        lines: formData.lines.map((line) => ({
          account: Number(line.account),
          debit: parseFloat(line.debit) || 0,
          credit: parseFloat(line.credit) || 0,
          description: line.description || '',
        })),
      }
      await createJournalEntry(payload)
      setShowModal(false)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveEntry')))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading && entries.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('journalEntries')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          {canManage && (
            <Button variant="primary" size="sm" onClick={handleOpenCreate}>
              {t('addJournalEntry')}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('entryNumber')}</th>
            <th>{t('entryDate')}</th>
            <th>{t('description')}</th>
            <th>{t('fiscalPeriod')}</th>
            <th>{t('status')}</th>
            <th>{t('sourceType')}</th>
          </tr>
        </thead>
        <tbody>
          {entries.length === 0 ? (
            <tr>
              <td colSpan="6" className="text-center">{t('noEntries')}</td>
            </tr>
          ) : (
            entries.map((entry) => (
              <tr key={entry.id}>
                <td>{entry.entry_number}</td>
                <td>{entry.date}</td>
                <td>{entry.description}</td>
                <td>{fiscalPeriods.find((p) => p.id === entry.fiscal_period)?.name || '-'}</td>
                <td>
                  {entry.is_posted ? (
                    <Badge bg="success" className="badge-status">{t('posted')}</Badge>
                  ) : (
                    <Badge bg="warning" className="badge-status">{t('draft')}</Badge>
                  )}
                </td>
                <td>{entry.source_type}</td>
              </tr>
            ))
          )}
        </tbody>
      </Table>

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={(page) => fetchData(page)}
      />

      {/* نموذج إنشاء قيد */}
      <Modal show={showModal} onHide={handleCloseModal} centered size="xl">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{t('newJournalEntry')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('fiscalPeriod')} *</Form.Label>
                  <Form.Select
                    name="fiscal_period"
                    value={formData.fiscal_period}
                    onChange={handleFormChange}
                    required
                  >
                    <option value="">{t('selectPeriod')}</option>
                    {fiscalPeriods.map((period) => {
                      const year = fiscalYears.find((y) => y.id === period.fiscal_year)
                      return (
                        <option key={period.id} value={period.id}>
                          {period.name}{year ? ` (${year.name})` : ''}
                        </option>
                      )
                    })}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('entryDate')} *</Form.Label>
                  <Form.Control
                    type="date"
                    name="date"
                    value={formData.date}
                    onChange={handleFormChange}
                    required
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={12}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('description')}</Form.Label>
                  <Form.Control
                    type="text"
                    name="description"
                    value={formData.description}
                    onChange={handleFormChange}
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={12}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('reference')}</Form.Label>
                  <Form.Control
                    type="text"
                    name="reference"
                    value={formData.reference}
                    onChange={handleFormChange}
                  />
                </Form.Group>
              </Col>
            </Row>

            <h6>{t('lines')}</h6>
            {formData.lines.map((line, index) => (
              <Row key={index} className="mb-2 align-items-end">
                <Col md={3}>
                  <Form.Label>{t('account')} *</Form.Label>
                  <Form.Select
                    value={line.account}
                    onChange={(e) => handleLineChange(index, 'account', e.target.value)}
                    required
                  >
                    <option value="">{t('selectAccount')}</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.code} - {acc.name_ar || acc.name_en}
                      </option>
                    ))}
                  </Form.Select>
                </Col>
                <Col md={2}>
                  <Form.Label>{t('debit')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    value={line.debit}
                    onChange={(e) => handleLineChange(index, 'debit', e.target.value)}
                    min="0"
                  />
                </Col>
                <Col md={2}>
                  <Form.Label>{t('credit')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    value={line.credit}
                    onChange={(e) => handleLineChange(index, 'credit', e.target.value)}
                    min="0"
                  />
                </Col>
                <Col md={3}>
                  <Form.Label>{t('lineDescription')}</Form.Label>
                  <Form.Control
                    type="text"
                    value={line.description}
                    onChange={(e) => handleLineChange(index, 'description', e.target.value)}
                  />
                </Col>
                <Col md={2}>
                  <Button
                    variant="outline-danger"
                    size="sm"
                    onClick={() => removeLine(index)}
                    disabled={formData.lines.length <= 2}
                  >
                    {t('removeLine')}
                  </Button>
                </Col>
              </Row>
            ))}
            <Button variant="outline-secondary" size="sm" onClick={addLine} className="mt-2">
              + {t('addLine')}
            </Button>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseModal}>
              {t('cancel')}
            </Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? t('saving') : t('save')}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </div>
  )
}

export default JournalEntriesList
