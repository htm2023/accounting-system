import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { getInvoices, createInvoice, postInvoice, downloadInvoicePDF } from '../api/invoices'
import { getParties } from '../api/parties'
import { getFiscalPeriods } from '../api/fiscal'
import { getProducts } from '../api/inventory'
import { getAccounts } from '../api/accounts'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  invoice_type: 'Sale',
  fiscal_period: '',
  date: new Date().toISOString().slice(0, 10),
  due_date: '',
  party: '',
  currency: null,
  exchange_rate_used: '1',
  tax_amount: '0',
  tax_account: '',
  discount: '0',
  discount_account: '',
  items: [
    { product: '', quantity: 1, unit_price: 0, tax_rate: 0, discount: 0 },
  ],
}

const InvoicesList = () => {
  const { t } = useTranslation()
  const [invoices, setInvoices] = useState([])
  const [parties, setParties] = useState([])
  const [fiscalPeriods, setFiscalPeriods] = useState([])
  const [products, setProducts] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState(initialFormState)
  const [postingId, setPostingId] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [invoicesData, partiesData, periodsData, productsData, accountsData] = await Promise.all([
        getInvoices(page),
        getParties(),
        getFiscalPeriods(),
        getProducts(),
        getAccounts(),
      ])
      setInvoices(invoicesData.results)
      setCurrentPage(invoicesData.current_page || 1)
      setTotalPages(invoicesData.total_pages || 1)
      setTotalCount(invoicesData.count || 0)
      setParties(partiesData.results || partiesData)
      setFiscalPeriods(periodsData.results || periodsData)
      setProducts(productsData.results || productsData)
      setAccounts(accountsData.results || accountsData)
    } catch (err) {
      setError(t('failedLoadInvoices'))
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

  const handleItemChange = (index, field, value) => {
    setFormData((prev) => {
      const items = [...prev.items]
      items[index] = { ...items[index], [field]: value }
      return { ...prev, items }
    })
  }

  const addItem = () => {
    setFormData((prev) => ({
      ...prev,
      items: [...prev.items, { product: '', quantity: 1, unit_price: 0, tax_rate: 0, discount: 0 }],
    }))
  }

  const removeItem = (index) => {
    setFormData((prev) => {
      const items = prev.items.filter((_, i) => i !== index)
      return { ...prev, items }
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        invoice_type: formData.invoice_type,
        fiscal_period: Number(formData.fiscal_period),
        date: formData.date,
        due_date: formData.due_date || null,
        party: Number(formData.party),
        currency: formData.currency ? Number(formData.currency) : null,
        exchange_rate_used: parseFloat(formData.exchange_rate_used) || 1,
        tax_amount: parseFloat(formData.tax_amount) || 0,
        tax_account: formData.tax_account ? Number(formData.tax_account) : null,
        discount: parseFloat(formData.discount) || 0,
        discount_account: formData.discount_account ? Number(formData.discount_account) : null,
        items: formData.items.map((item) => ({
          product: Number(item.product),
          quantity: parseFloat(item.quantity) || 0,
          unit_price: parseFloat(item.unit_price) || 0,
          tax_rate: parseFloat(item.tax_rate) || 0,
          discount: parseFloat(item.discount) || 0,
        })),
      }
      await createInvoice(payload)
      setShowModal(false)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveInvoice')))
    } finally {
      setSubmitting(false)
    }
  }

  const handlePost = async (id) => {
    if (!window.confirm(t('confirmPostInvoice'))) return
    setPostingId(id)
    setError('')
    try {
      await postInvoice(id)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedPostInvoice')))
    } finally {
      setPostingId(null)
    }
  }

  const handleDownloadPDF = async (invoice) => {
    try {
      const blob = await downloadInvoicePDF(invoice.id)
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `${invoice.invoice_number}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (err) {
      setError(t('failedLoadPdf'))
    }
  }

  const statusBadge = (status) => {
    const map = {
      Draft: { bg: 'secondary', label: t('draft') },
      Posted: { bg: 'success', label: t('posted') },
      'Partially Paid': { bg: 'warning', label: t('partiallyPaid') },
      Paid: { bg: 'success', label: t('paid') },
      Cancelled: { bg: 'danger', label: t('cancelled') },
    }
    return map[status] || { bg: 'secondary', label: status }
  }

  if (loading && invoices.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('invoices')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          <Button variant="primary" size="sm" onClick={handleOpenCreate}>
            {t('addInvoice')}
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('invoiceNumber')}</th>
            <th>{t('invoiceType')}</th>
            <th>{t('party')}</th>
            <th>{t('invoiceDate')}</th>
            <th>{t('totalAmount')}</th>
            <th>{t('paidAmount')}</th>
            <th>{t('invoiceStatus')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {invoices.length === 0 ? (
            <tr>
              <td colSpan="8" className="text-center">{t('noInvoices')}</td>
            </tr>
          ) : (
            invoices.map((inv) => (
              <tr key={inv.id}>
                <td>{inv.invoice_number}</td>
                <td>
                  <Badge bg={inv.invoice_type === 'Sale' ? 'primary' : 'info'}>
                    {inv.invoice_type === 'Sale' ? t('sale') : t('purchase')}
                  </Badge>
                </td>
                <td>{getPartyName(inv.party)}</td>
                <td>{inv.date}</td>
                <td>{inv.total_amount}</td>
                <td>{inv.paid_amount}</td>
                <td>
                  <Badge bg={statusBadge(inv.status).bg}>
                    {statusBadge(inv.status).label}
                  </Badge>
                </td>
                <td>
                  {inv.status === 'Draft' && (
                    <Button
                      variant="outline-success"
                      size="sm"
                      className="me-2"
                      onClick={() => handlePost(inv.id)}
                      disabled={postingId === inv.id}
                    >
                      {postingId === inv.id ? t('posting') : t('post')}
                    </Button>
                  )}
                  <Button variant="outline-primary" size="sm" onClick={() => handleDownloadPDF(inv)}>
                    PDF
                  </Button>
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

      {/* نموذج إنشاء فاتورة */}
      <Modal show={showModal} onHide={handleCloseModal} centered size="xl">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{t('newInvoice')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('invoiceType')} *</Form.Label>
                  <Form.Select name="invoice_type" value={formData.invoice_type} onChange={handleFormChange} required>
                    <option value="Sale">{t('sale')}</option>
                    <option value="Purchase">{t('purchase')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={4}>
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
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('invoiceDate')} *</Form.Label>
                  <Form.Control type="date" name="date" value={formData.date} onChange={handleFormChange} required />
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
                  <Form.Label>{t('dueDate')}</Form.Label>
                  <Form.Control type="date" name="due_date" value={formData.due_date} onChange={handleFormChange} />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('taxAmount')}</Form.Label>
                  <Form.Control type="number" step="0.01" name="tax_amount" value={formData.tax_amount} onChange={handleFormChange} min="0" />
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('taxAccount')}</Form.Label>
                  <Form.Select name="tax_account" value={formData.tax_account} onChange={handleFormChange}>
                    <option value="">{t('none')}</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>{acc.code} - {acc.name_ar || acc.name_en}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('discountAmount')}</Form.Label>
                  <Form.Control type="number" step="0.01" name="discount" value={formData.discount} onChange={handleFormChange} min="0" />
                </Form.Group>
              </Col>
              <Col md={3}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('discountAccount')}</Form.Label>
                  <Form.Select name="discount_account" value={formData.discount_account} onChange={handleFormChange}>
                    <option value="">{t('none')}</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>{acc.code} - {acc.name_ar || acc.name_en}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>

            <h6>{t('items')}</h6>
            {formData.items.map((item, index) => (
              <Row key={index} className="mb-2 align-items-end">
                <Col md={3}>
                  <Form.Label>{t('product')} *</Form.Label>
                  <Form.Select
                    value={item.product}
                    onChange={(e) => handleItemChange(index, 'product', e.target.value)}
                    required
                  >
                    <option value="">{t('selectProduct')}</option>
                    {products.map((prod) => (
                      <option key={prod.id} value={prod.id}>
                        {prod.sku} - {prod.name_ar || prod.name_en}
                      </option>
                    ))}
                  </Form.Select>
                </Col>
                <Col md={2}>
                  <Form.Label>{t('quantity')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    value={item.quantity}
                    onChange={(e) => handleItemChange(index, 'quantity', e.target.value)}
                    min="0.01"
                    required
                  />
                </Col>
                <Col md={2}>
                  <Form.Label>{t('unitPrice')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    value={item.unit_price}
                    onChange={(e) => handleItemChange(index, 'unit_price', e.target.value)}
                    min="0"
                    required
                  />
                </Col>
                <Col md={2}>
                  <Form.Label>{t('taxRate')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    value={item.tax_rate}
                    onChange={(e) => handleItemChange(index, 'tax_rate', e.target.value)}
                    min="0"
                  />
                </Col>
                <Col md={2}>
                  <Form.Label>{t('discount')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    value={item.discount}
                    onChange={(e) => handleItemChange(index, 'discount', e.target.value)}
                    min="0"
                  />
                </Col>
                <Col md={1}>
                  <Button variant="outline-danger" size="sm" onClick={() => removeItem(index)} disabled={formData.items.length <= 1}>
                    {t('removeItem')}
                  </Button>
                </Col>
              </Row>
            ))}
            <Button variant="outline-secondary" size="sm" onClick={addItem} className="mt-2">
              + {t('addItem')}
            </Button>
          </Modal.Body>
          <Modal.Footer>
            <Button variant="secondary" onClick={handleCloseModal}>{t('cancel')}</Button>
            <Button variant="primary" type="submit" disabled={submitting}>
              {submitting ? t('saving') : t('saveAsDraft')}
            </Button>
          </Modal.Footer>
        </Form>
      </Modal>
    </div>
  )
}

export default InvoicesList
