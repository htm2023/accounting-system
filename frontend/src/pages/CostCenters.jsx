import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { getCostCenters, createCostCenter, updateCostCenter, deleteCostCenter } from '../api/costCenters'
import { getErrorMessage } from '../utils/errorHandler'

const initialFormState = {
  code: '',
  name_ar: '',
  name_en: '',
  is_active: true,
}

const CostCenters = () => {
  const { t } = useTranslation()
  const [costCenters, setCostCenters] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingCostCenter, setEditingCostCenter] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [submitting, setSubmitting] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getCostCenters()
      setCostCenters(data.results || data)
    } catch (err) {
      setError(t('failedLoadCostCenters'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handleOpenCreate = () => {
    setEditingCostCenter(null)
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleOpenEdit = (costCenter) => {
    setEditingCostCenter(costCenter)
    setFormData({
      code: costCenter.code,
      name_ar: costCenter.name_ar || '',
      name_en: costCenter.name_en || '',
      is_active: costCenter.is_active,
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingCostCenter(null)
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
      if (editingCostCenter) {
        await updateCostCenter(editingCostCenter.id, formData)
      } else {
        await createCostCenter(formData)
      }
      setShowModal(false)
      setEditingCostCenter(null)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveCostCenter')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirmDeleteCostCenter'))) return
    setError('')
    try {
      await deleteCostCenter(id)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteCostCenter')))
    }
  }

  if (loading && costCenters.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('costCenters')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={fetchData} className="me-2">
            {t('update')}
          </Button>
          <Button variant="primary" size="sm" onClick={handleOpenCreate}>
            {t('addCostCenter')}
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('costCenterCode')}</th>
            <th>{t('costCenterNameAr')}</th>
            <th>{t('costCenterNameEn')}</th>
            <th>{t('isActive')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {costCenters.length === 0 ? (
            <tr>
              <td colSpan="5" className="text-center">{t('noCostCenters')}</td>
            </tr>
          ) : (
            costCenters.map((cc) => (
              <tr key={cc.id}>
                <td>{cc.code}</td>
                <td>{cc.name_ar || '-'}</td>
                <td>{cc.name_en || '-'}</td>
                <td>
                  {cc.is_active ? <Badge bg="success" className="badge-status">{t('active')}</Badge> : <Badge bg="danger" className="badge-status">{t('inactive')}</Badge>}
                </td>
                <td>
                  <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEdit(cc)}>
                    {t('edit')}
                  </Button>
                  <Button variant="outline-danger" size="sm" onClick={() => handleDelete(cc.id)}>
                    {t('delete')}
                  </Button>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </Table>

      {/* نموذج مركز التكلفة */}
      <Modal show={showModal} onHide={handleCloseModal} centered>
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingCostCenter ? t('editCostCenter') : t('addCostCenter')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('costCenterCode')} *</Form.Label>
                  <Form.Control type="text" name="code" value={formData.code} onChange={handleChange} required />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('costCenterNameAr')} *</Form.Label>
                  <Form.Control type="text" name="name_ar" value={formData.name_ar} onChange={handleChange} required />
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>{t('costCenterNameEn')}</Form.Label>
              <Form.Control type="text" name="name_en" value={formData.name_en} onChange={handleChange} />
            </Form.Group>
            <Form.Check
              type="checkbox"
              label={t('isActive')}
              name="is_active"
              checked={formData.is_active}
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
    </div>
  )
}

export default CostCenters
