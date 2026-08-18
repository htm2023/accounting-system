import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { getParties, createParty, updateParty, deleteParty } from '../api/parties'
import { getAccounts } from '../api/accounts'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  party_type: 'Customer',
  name_ar: '',
  name_en: '',
  email: '',
  phone: '',
  address: '',
  tax_number: '',
  credit_limit: '',
  opening_balance: '0',
  opening_balance_date: '',
  default_account: '',
}

const PartiesList = () => {
  const { t } = useTranslation()
  const role = useSelector((state) => state.auth.user?.role)
  const canManage = role === 'Admin' || role === 'Accountant'
  const [parties, setParties] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingParty, setEditingParty] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [submitting, setSubmitting] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [partiesData, accountsData] = await Promise.all([
        getParties(page),
        getAccounts(),
      ])
      setParties(partiesData.results)
      setCurrentPage(partiesData.current_page || 1)
      setTotalPages(partiesData.total_pages || 1)
      setTotalCount(partiesData.count || 0)
      setAccounts(accountsData.results || accountsData)
    } catch (err) {
      setError(t('failedLoadParties'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const handleOpenCreate = () => {
    setEditingParty(null)
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleOpenEdit = (party) => {
    setEditingParty(party)
    setFormData({
      party_type: party.party_type,
      name_ar: party.name_ar || '',
      name_en: party.name_en || '',
      email: party.email || '',
      phone: party.phone || '',
      address: party.address || '',
      tax_number: party.tax_number || '',
      credit_limit: party.credit_limit || '',
      opening_balance: party.opening_balance || '0',
      opening_balance_date: party.opening_balance_date || '',
      default_account: party.default_account || '',
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingParty(null)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    const payload = {
      ...formData,
      credit_limit: formData.credit_limit ? parseFloat(formData.credit_limit) : null,
      opening_balance: parseFloat(formData.opening_balance) || 0,
      opening_balance_date: formData.opening_balance_date || null,
      default_account: formData.default_account ? Number(formData.default_account) : null,
    }
    try {
      if (editingParty) {
        await updateParty(editingParty.id, payload)
      } else {
        await createParty(payload)
      }
      setShowModal(false)
      setEditingParty(null)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveParty')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirmDeleteParty'))) return
    setError('')
    try {
      await deleteParty(id)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteParty')))
    }
  }

  if (loading && parties.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('parties')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          {canManage && (
            <Button variant="primary" size="sm" onClick={handleOpenCreate}>
              {t('addParty')}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('partyType')}</th>
            <th>{t('partyName')}</th>
            <th>{t('email')}</th>
            <th>{t('phone')}</th>
            <th>{t('openingBalance')}</th>
            <th>{t('defaultAccount')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {parties.length === 0 ? (
            <tr>
              <td colSpan="7" className="text-center">{t('noParties')}</td>
            </tr>
          ) : (
            parties.map((party) => (
              <tr key={party.id}>
                <td>
                  <Badge bg={party.party_type === 'Customer' ? 'primary' : 'info'} className="badge-status">
                    {party.party_type === 'Customer' ? t('customer') : party.party_type === 'Supplier' ? t('supplier') : t('both')}
                  </Badge>
                </td>
                <td>{party.name_ar || party.name_en || '-'}</td>
                <td>{party.email || '-'}</td>
                <td>{party.phone || '-'}</td>
                <td>{party.opening_balance}</td>
                <td>{party.default_account ? accounts.find(a => a.id === party.default_account)?.code || party.default_account : '-'}</td>
                <td>
                  {canManage && (
                    <>
                      <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEdit(party)}>
                        {t('edit')}
                      </Button>
                      <Button variant="outline-danger" size="sm" onClick={() => handleDelete(party.id)}>
                        {t('delete')}
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

      {/* نموذج الطرف */}
      <Modal show={showModal} onHide={handleCloseModal} centered size="lg">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingParty ? t('editParty') : t('addParty')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('partyType')} *</Form.Label>
                  <Form.Select name="party_type" value={formData.party_type} onChange={handleChange} required>
                    <option value="Customer">{t('customer')}</option>
                    <option value="Supplier">{t('supplier')}</option>
                    <option value="Both">{t('both')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('partyName')} *</Form.Label>
                  <Form.Control
                    type="text"
                    name="name_ar"
                    value={formData.name_ar}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('nameEn')}</Form.Label>
                  <Form.Control
                    type="text"
                    name="name_en"
                    value={formData.name_en}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('email')}</Form.Label>
                  <Form.Control
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('phone')}</Form.Label>
                  <Form.Control
                    type="text"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('taxNumber')}</Form.Label>
                  <Form.Control
                    type="text"
                    name="tax_number"
                    value={formData.tax_number}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>{t('address')}</Form.Label>
              <Form.Control
                type="text"
                name="address"
                value={formData.address}
                onChange={handleChange}
              />
            </Form.Group>
            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('creditLimit')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="credit_limit"
                    value={formData.credit_limit}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('openingBalance')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="opening_balance"
                    value={formData.opening_balance}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('openingBalanceDate')}</Form.Label>
                  <Form.Control
                    type="date"
                    name="opening_balance_date"
                    value={formData.opening_balance_date}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>{t('defaultAccount')}</Form.Label>
              <Form.Select name="default_account" value={formData.default_account} onChange={handleChange}>
                <option value="">{t('selectAccount')}</option>
                {accounts.map((acc) => (
                  <option key={acc.id} value={acc.id}>
                    {acc.code} - {acc.name_ar || acc.name_en}
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
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

export default PartiesList
