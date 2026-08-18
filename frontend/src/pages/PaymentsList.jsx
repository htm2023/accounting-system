import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import {
  getReceiptPayments,
  createReceiptPayment,
  allocatePaymentToInvoice,
  postReceiptPayment,
} from '../api/payments'
import { getParties } from '../api/parties'
import { getFiscalPeriods } from '../api/fiscal'
import { getAccounts } from '../api/accounts'
import { getInvoices } from '../api/invoices'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  document_type: 'Receipt',
  fiscal_period: '',
  date: new Date().toISOString().slice(0, 10),
  party: '',
  amount: '',
  account: '',
  description: '',
}

const PaymentsList = () => {
  const { t } = useTranslation()
  const [payments, setPayments] = useState([])
  const [parties, setParties] = useState([])
  const [fiscalPeriods, setFiscalPeriods] = useState([])
  const [accounts, setAccounts] = useState([])
  const [invoices, setInvoices] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [showAllocateModal, setShowAllocateModal] = useState(false)
  const [currentPayment, setCurrentPayment] = useState(null)
  const [allocateInvoiceId, setAllocateInvoiceId] = useState('')
  const [allocateAmount, setAllocateAmount] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [postingId, setPostingId] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [paymentsData, partiesData, periodsData, accountsData, invoicesData] = await Promise.all([
        getReceiptPayments(page),
        getParties(),
        getFiscalPeriods(),
        getAccounts(),
        getInvoices(),
      ])
      setPayments(paymentsData.results)
      setCurrentPage(paymentsData.current_page || 1)
      setTotalPages(paymentsData.total_pages || 1)
      setTotalCount(paymentsData.count || 0)
      setParties(partiesData.results || partiesData)
      setFiscalPeriods(periodsData.results || periodsData)
      setAccounts(accountsData.results || accountsData)
      setInvoices(invoicesData.results || invoicesData)
    } catch (err) {
      setError(t('failedLoadPayments'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const handleOpenCreate = () => {
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
  }

  const handleFormChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const getPartyName = (partyId) => {
    const party = parties.find((p) => p.id === partyId)
    return party ? (party.name_ar || party.name_en) : partyId
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        document_type: formData.document_type,
        fiscal_period: Number(formData.fiscal_period),
        date: formData.date,
        party: Number(formData.party),
        amount: parseFloat(formData.amount),
        account: Number(formData.account),
        description: formData.description || '',
      }
      await createReceiptPayment(payload)
      setShowModal(false)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSavePayment')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleOpenAllocate = (payment) => {
    setCurrentPayment(payment)
    setAllocateInvoiceId('')
    setAllocateAmount('')
    setShowAllocateModal(true)
  }

  const handleAllocate = async () => {
    if (!currentPayment) return
    setSubmitting(true)
    setError('')
    try {
      await allocatePaymentToInvoice(currentPayment.id, Number(allocateInvoiceId), parseFloat(allocateAmount))
      setShowAllocateModal(false)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedAllocatePayment')))
    } finally {
      setSubmitting(false)
    }
  }

  const handlePost = async (payment) => {
    if (!window.confirm(t('confirmPostPayment'))) return
    setPostingId(payment.id)
    setError('')
    try {
      await postReceiptPayment(payment.id)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedPostPayment')))
    } finally {
      setPostingId(null)
    }
  }

  if (loading && payments.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('payments')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          <Button variant="primary" size="sm" onClick={handleOpenCreate}>
            {t('addPayment')}
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('paymentNumber')}</th>
            <th>{t('paymentType')}</th>
            <th>{t('party')}</th>
            <th>{t('paymentDate')}</th>
            <th>{t('amount')}</th>
            <th>{t('allocatedAmount')}</th>
            <th>{t('unallocatedAmount')}</th>
            <th>{t('paymentStatus')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {payments.length === 0 ? (
            <tr>
              <td colSpan="9" className="text-center">{t('noPayments')}</td>
            </tr>
          ) : (
            payments.map((pay) => (
              <tr key={pay.id}>
                <td>{pay.number}</td>
                <td>
                  <Badge bg={pay.document_type === 'Receipt' ? 'success' : 'warning'}>
                    {pay.document_type === 'Receipt' ? t('receiptLabel') : t('paymentLabel')}
                  </Badge>
                </td>
                <td>{getPartyName(pay.party)}</td>
                <td>{pay.date}</td>
                <td>{pay.amount}</td>
                <td>{pay.total_allocated}</td>
                <td>{pay.unallocated_amount}</td>
                <td>
                  {pay.journal_entry ? (
                    <Badge bg="success">{t('posted')}</Badge>
                  ) : (
                    <Badge bg="warning">{t('draft')}</Badge>
                  )}
                </td>
                <td>
                  {!pay.journal_entry && (
                    <>
                      <Button
                        variant="outline-primary"
                        size="sm"
                        className="me-2"
                        onClick={() => handleOpenAllocate(pay)}
                      >
                        {t('allocate')}
                      </Button>
                      <Button
                        variant="outline-success"
                        size="sm"
                        onClick={() => handlePost(pay)}
                        disabled={postingId === pay.id || pay.unallocated_amount > 0}
                      >
                        {postingId === pay.id ? t('posting') : t('post')}
                      </Button>
                    </>
                  )}
                </td>
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

      {/* نموذج إنشاء سند */}
      <Modal show={showModal} onHide={handleCloseModal} centered size="lg">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{t('newPayment')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('paymentType')} *</Form.Label>
                  <Form.Select name="document_type" value={formData.document_type} onChange={handleFormChange} required>
                    <option value="Receipt">{t('receiptLabel')}</option>
                    <option value="Payment">{t('paymentLabel')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('fiscalPeriod')} *</Form.Label>
                  <Form.Select name="fiscal_period" value={formData.fiscal_period} onChange={handleFormChange} required>
                    <option value="">{t('selectPeriod')}</option>
                    {fiscalPeriods.map((p) => (
                      <option key={p.id} value={p.id}>{p.name}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('paymentDate')} *</Form.Label>
                  <Form.Control type="date" name="date" value={formData.date} onChange={handleFormChange} required />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('amount')} *</Form.Label>
                  <Form.Control type="number" step="0.01" name="amount" value={formData.amount} onChange={handleFormChange} required />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('party')} *</Form.Label>
                  <Form.Select name="party" value={formData.party} onChange={handleFormChange} required>
                    <option value="">{t('selectParty')}</option>
                    {parties.map((p) => (
                      <option key={p.id} value={p.id}>{p.name_ar || p.name_en}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('bankAccount')} *</Form.Label>
                  <Form.Select name="account" value={formData.account} onChange={handleFormChange} required>
                    <option value="">{t('selectAccount')}</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.code} - {acc.name_ar || acc.name_en}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>{t('description')}</Form.Label>
              <Form.Control type="text" name="description" value={formData.description} onChange={handleFormChange} />
            </Form.Group>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseModal}>{t('cancel')}</Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? t('saving') : t('save')}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>

      {/* نموذج التخصيص */}
      <Modal show={showAllocateModal} onHide={() => setShowAllocateModal(false)} centered size="md">
        <Modal.Header closeButton>
          <Modal.Title>{t('allocatePayment')}: {currentPayment?.number}</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <p>{t('unallocatedAmount')}: {currentPayment?.unallocated_amount}</p>
          <Form.Group className="mb-3">
            <Form.Label>{t('selectInvoice')}</Form.Label>
            <Form.Select value={allocateInvoiceId} onChange={(e) => setAllocateInvoiceId(e.target.value)}>
              <option value="">{t('selectInvoice')}</option>
              {invoices
                .filter((inv) => inv.status === 'Posted' || inv.status === 'Partially Paid')
                .map((inv) => (
                  <option key={inv.id} value={inv.id}>
                    {inv.invoice_number} - {getPartyName(inv.party)} ({t('remaining')}: {inv.total_amount - inv.paid_amount})
                  </option>
                ))}
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t('allocationAmount')}</Form.Label>
            <Form.Control type="number" step="0.01" value={allocateAmount} onChange={(e) => setAllocateAmount(e.target.value)} />
          </Form.Group>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowAllocateModal(false)}>{t('cancel')}</Button>
          <Button variant="primary" onClick={handleAllocate} disabled={submitting || !allocateInvoiceId || !allocateAmount}>
            {submitting ? t('allocating') : t('allocate')}
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  )
}

export default PaymentsList
