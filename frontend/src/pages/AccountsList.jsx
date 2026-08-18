import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { getAccounts, createAccount, updateAccount, deleteAccount } from '../api/accounts'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  code: '',
  name_ar: '',
  name_en: '',
  account_type: 'Asset',
  parent: '',
  normal_balance: 'Debit',
  is_active: true,
  allow_posting: true,
}

const AccountsList = () => {
  const { t } = useTranslation()
  const role = useSelector((state) => state.auth.user?.role)
  const canManage = role === 'Admin' || role === 'Accountant'
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [submitting, setSubmitting] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchAccounts = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const data = await getAccounts(page)
      setAccounts(data.results)
      setCurrentPage(data.current_page || 1)
      setTotalPages(data.total_pages || 1)
      setTotalCount(data.count || 0)
    } catch (err) {
      setError(t('failedLoadAccounts'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAccounts(1)
  }, [])

  const handleOpenCreate = () => {
    setEditingAccount(null)
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleOpenEdit = (account) => {
    setEditingAccount(account)
    setFormData({
      code: account.code,
      name_ar: account.name_ar || '',
      name_en: account.name_en || '',
      account_type: account.account_type,
      parent: account.parent || '',
      normal_balance: account.normal_balance,
      is_active: account.is_active,
      allow_posting: account.allow_posting,
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingAccount(null)
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
    const payload = {
      ...formData,
      parent: formData.parent ? Number(formData.parent) : null,
    }
    try {
      if (editingAccount) {
        await updateAccount(editingAccount.id, payload)
      } else {
        await createAccount(payload)
      }
      setShowModal(false)
      setEditingAccount(null)
      fetchAccounts()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveAccount')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirmDeleteAccount'))) return
    setError('')
    try {
      await deleteAccount(id)
      fetchAccounts()
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteAccount')))
    }
  }

  if (loading && accounts.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('accounts')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchAccounts(currentPage)} className="me-2">
            {t('update')}
          </Button>
          {canManage && (
            <Button variant="primary" size="sm" onClick={handleOpenCreate}>
              {t('addAccount')}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('accountCode')}</th>
            <th>{t('accountName')}</th>
            <th>{t('accountType')}</th>
            <th>{t('normalBalance')}</th>
            <th>{t('parentAccount')}</th>
            <th>{t('allowPosting')}</th>
            <th>{t('isActive')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {accounts.length === 0 ? (
            <tr>
              <td colSpan="8" className="text-center">{t('noAccounts')}</td>
            </tr>
          ) : (
            accounts.map((acc) => (
              <tr key={acc.id}>
                <td>{acc.code}</td>
                <td>{acc.name_ar || acc.name_en || '-'}</td>
                <td>{acc.account_type}</td>
                <td>{acc.normal_balance}</td>
                <td>{acc.parent ? accounts.find(a => a.id === acc.parent)?.code || acc.parent : '-'}</td>
                <td>
                  {acc.allow_posting ? <Badge bg="success" className="badge-status">{t('yes')}</Badge> : <Badge bg="secondary" className="badge-status">{t('no')}</Badge>}
                </td>
                <td>
                  {acc.is_active ? <Badge bg="success" className="badge-status">{t('active')}</Badge> : <Badge bg="danger" className="badge-status">{t('inactive')}</Badge>}
                </td>
                <td>
                  {canManage && (
                    <>
                      <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEdit(acc)}>
                        {t('edit')}
                      </Button>
                      <Button variant="outline-danger" size="sm" onClick={() => handleDelete(acc.id)}>
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
        onPageChange={(page) => fetchAccounts(page)}
      />

      {/* نموذج الحساب */}
      <Modal show={showModal} onHide={handleCloseModal} centered size="lg">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingAccount ? t('editAccount') : t('addAccount')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('code')} *</Form.Label>
                  <Form.Control
                    type="text"
                    name="code"
                    value={formData.code}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('type')} *</Form.Label>
                  <Form.Select name="account_type" value={formData.account_type} onChange={handleChange} required>
                    <option value="Asset">{t('asset')}</option>
                    <option value="Liability">{t('liability')}</option>
                    <option value="Equity">{t('equity')}</option>
                    <option value="Revenue">{t('revenue')}</option>
                    <option value="Expense">{t('expense')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('nameAr')} *</Form.Label>
                  <Form.Control
                    type="text"
                    name="name_ar"
                    value={formData.name_ar}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
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
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('parent')}</Form.Label>
                  <Form.Select name="parent" value={formData.parent} onChange={handleChange}>
                    <option value="">{t('selectParent')}</option>
                    {accounts
                      .filter((a) => !editingAccount || a.id !== editingAccount.id)
                      .map((a) => (
                        <option key={a.id} value={a.id}>
                          {a.code} - {a.name_ar || a.name_en}
                        </option>
                      ))}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('normalBalance')}</Form.Label>
                  <Form.Select name="normal_balance" value={formData.normal_balance} onChange={handleChange}>
                    <option value="Debit">{t('debit')}</option>
                    <option value="Credit">{t('credit')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Form.Check
              type="checkbox"
              label={t('allowPosting')}
              name="allow_posting"
              checked={formData.allow_posting}
              onChange={handleChange}
              className="mb-2"
            />
            <Form.Check
              type="checkbox"
              label={t('isActive')}
              name="is_active"
              checked={formData.is_active}
              onChange={handleChange}
              className="mb-2"
            />
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

export default AccountsList
