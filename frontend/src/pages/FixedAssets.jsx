import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { getFixedAssets, createFixedAsset, updateFixedAsset, deleteFixedAsset } from '../api/fixedAssets'
import { getAccounts } from '../api/accounts'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  name: '',
  asset_account: '',
  depreciation_account: '',
  expense_account: '',
  purchase_date: '',
  cost: '',
  salvage_value: '0',
  useful_life_years: '',
  depreciation_method: 'Straight-line',
  status: 'Active',
}

const FixedAssets = () => {
  const { t } = useTranslation()
  const [assets, setAssets] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingAsset, setEditingAsset] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [submitting, setSubmitting] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [assetsData, accountsData] = await Promise.all([
        getFixedAssets(page),
        getAccounts(),
      ])
      setAssets(assetsData.results || assetsData)
      setCurrentPage(assetsData.current_page || 1)
      setTotalPages(assetsData.total_pages || 1)
      setTotalCount(assetsData.count || 0)
      setAccounts(accountsData.results || accountsData)
    } catch (err) {
      setError(t('failedLoadAssets'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const getAccountLabel = (accountId) => {
    const account = accounts.find((a) => a.id === accountId)
    return account ? `${account.code} - ${account.name_ar || account.name_en}` : accountId
  }

  const handleOpenCreate = () => {
    setEditingAsset(null)
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleOpenEdit = (asset) => {
    setEditingAsset(asset)
    setFormData({
      name: asset.name,
      asset_account: asset.asset_account || '',
      depreciation_account: asset.depreciation_account || '',
      expense_account: asset.expense_account || '',
      purchase_date: asset.purchase_date,
      cost: asset.cost,
      salvage_value: asset.salvage_value,
      useful_life_years: asset.useful_life_years,
      depreciation_method: asset.depreciation_method,
      status: asset.status,
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingAsset(null)
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
      asset_account: formData.asset_account ? Number(formData.asset_account) : null,
      depreciation_account: formData.depreciation_account ? Number(formData.depreciation_account) : null,
      expense_account: formData.expense_account ? Number(formData.expense_account) : null,
      cost: parseFloat(formData.cost) || 0,
      salvage_value: parseFloat(formData.salvage_value) || 0,
      useful_life_years: parseInt(formData.useful_life_years, 10) || 0,
    }
    try {
      if (editingAsset) {
        await updateFixedAsset(editingAsset.id, payload)
      } else {
        await createFixedAsset(payload)
      }
      setShowModal(false)
      setEditingAsset(null)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveAsset')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirmDeleteAsset'))) return
    setError('')
    try {
      await deleteFixedAsset(id)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteAsset')))
    }
  }

  if (loading && assets.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('fixedAssets')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          <Button variant="primary" size="sm" onClick={handleOpenCreate}>
            {t('addFixedAsset')}
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('assetName')}</th>
            <th>{t('assetAccount')}</th>
            <th>{t('depreciationAccount')}</th>
            <th>{t('expenseAccount')}</th>
            <th>{t('purchaseDate')}</th>
            <th>{t('assetCost')}</th>
            <th>{t('assetStatus')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {assets.length === 0 ? (
            <tr>
              <td colSpan="8" className="text-center">{t('noFixedAssets')}</td>
            </tr>
          ) : (
            assets.map((asset) => (
              <tr key={asset.id}>
                <td>{asset.name}</td>
                <td>{getAccountLabel(asset.asset_account)}</td>
                <td>{getAccountLabel(asset.depreciation_account)}</td>
                <td>{getAccountLabel(asset.expense_account)}</td>
                <td>{asset.purchase_date}</td>
                <td>{asset.cost}</td>
                <td>
                  {asset.status === 'Active' ? (
                    <Badge bg="success">{t('active')}</Badge>
                  ) : (
                    <Badge bg="danger">{t('disposed')}</Badge>
                  )}
                </td>
                <td>
                  <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEdit(asset)}>
                    {t('edit')}
                  </Button>
                  <Button variant="outline-danger" size="sm" onClick={() => handleDelete(asset.id)}>
                    {t('delete')}
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

      <Modal show={showModal} onHide={handleCloseModal} centered size="lg">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingAsset ? t('editFixedAsset') : t('addFixedAsset')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>{t('assetName')} *</Form.Label>
              <Form.Control type="text" name="name" value={formData.name} onChange={handleChange} required />
            </Form.Group>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('assetAccount')} *</Form.Label>
                  <Form.Select name="asset_account" value={formData.asset_account} onChange={handleChange} required>
                    <option value="">{t('selectAccount')}</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>
                        {acc.code} - {acc.name_ar || acc.name_en}
                      </option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('depreciationAccount')} *</Form.Label>
                  <Form.Select name="depreciation_account" value={formData.depreciation_account} onChange={handleChange} required>
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
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('expenseAccount')} *</Form.Label>
                  <Form.Select name="expense_account" value={formData.expense_account} onChange={handleChange} required>
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
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('purchaseDate')} *</Form.Label>
                  <Form.Control
                    type="date"
                    name="purchase_date"
                    value={formData.purchase_date}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('assetCost')} *</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="cost"
                    value={formData.cost}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('salvageValue')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="salvage_value"
                    value={formData.salvage_value}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('usefulLifeYears')} *</Form.Label>
                  <Form.Control
                    type="number"
                    step="1"
                    min="1"
                    name="useful_life_years"
                    value={formData.useful_life_years}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('depreciationMethod')} *</Form.Label>
                  <Form.Select name="depreciation_method" value={formData.depreciation_method} onChange={handleChange} required>
                    <option value="Straight-line">{t('straightLine')}</option>
                    <option value="Declining">{t('declining')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>{t('assetStatus')} *</Form.Label>
              <Form.Select name="status" value={formData.status} onChange={handleChange} required>
                <option value="Active">{t('active')}</option>
                <option value="Disposed">{t('disposed')}</option>
              </Form.Select>
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
    </div>
  )
}

export default FixedAssets
