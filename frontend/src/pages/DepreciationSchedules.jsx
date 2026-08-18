import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import {
  getDepreciationSchedules,
  createDepreciationSchedule,
  updateDepreciationSchedule,
  deleteDepreciationSchedule,
  postDepreciationSchedule,
  getFixedAssets,
} from '../api/fixedAssets'
import { getFiscalPeriods } from '../api/fiscal'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  asset: '',
  fiscal_period: '',
  depreciation_amount: '',
  accumulated_depreciation: '0',
}

const DepreciationSchedules = () => {
  const { t } = useTranslation()
  const role = useSelector((state) => state.auth.user?.role)
  const canManage = role === 'Admin' || role === 'Accountant'
  const canPost = role === 'Admin'
  const [schedules, setSchedules] = useState([])
  const [assets, setAssets] = useState([])
  const [fiscalPeriods, setFiscalPeriods] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingSchedule, setEditingSchedule] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [submitting, setSubmitting] = useState(false)
  const [postingId, setPostingId] = useState(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [schedulesData, assetsData, periodsData] = await Promise.all([
        getDepreciationSchedules(page),
        getFixedAssets(),
        getFiscalPeriods(),
      ])
      setSchedules(schedulesData.results || schedulesData)
      setCurrentPage(schedulesData.current_page || 1)
      setTotalPages(schedulesData.total_pages || 1)
      setTotalCount(schedulesData.count || 0)
      setAssets(assetsData.results || assetsData)
      setFiscalPeriods(periodsData.results || periodsData)
    } catch (err) {
      setError(t('failedLoadDepreciationSchedules'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const getAssetName = (assetId) => {
    const asset = assets.find((a) => a.id === assetId)
    return asset ? asset.name : assetId
  }

  const getPeriodName = (periodId) => {
    const period = fiscalPeriods.find((p) => p.id === periodId)
    return period ? period.name : periodId
  }

  const handleOpenCreate = () => {
    setEditingSchedule(null)
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleOpenEdit = (schedule) => {
    setEditingSchedule(schedule)
    setFormData({
      asset: schedule.asset || '',
      fiscal_period: schedule.fiscal_period || '',
      depreciation_amount: schedule.depreciation_amount,
      accumulated_depreciation: schedule.accumulated_depreciation,
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingSchedule(null)
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
      asset: formData.asset ? Number(formData.asset) : null,
      fiscal_period: formData.fiscal_period ? Number(formData.fiscal_period) : null,
      depreciation_amount: parseFloat(formData.depreciation_amount) || 0,
      accumulated_depreciation: parseFloat(formData.accumulated_depreciation) || 0,
    }
    try {
      if (editingSchedule) {
        await updateDepreciationSchedule(editingSchedule.id, payload)
      } else {
        await createDepreciationSchedule(payload)
      }
      setShowModal(false)
      setEditingSchedule(null)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveDepreciationSchedule')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirmDeleteDepreciation'))) return
    setError('')
    try {
      await deleteDepreciationSchedule(id)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteDepreciationSchedule')))
    }
  }

  const handlePost = async (id) => {
    if (!window.confirm(t('confirmPostDepreciation'))) return
    setPostingId(id)
    setError('')
    try {
      await postDepreciationSchedule(id)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedPostDepreciation')))
    } finally {
      setPostingId(null)
    }
  }

  if (loading && schedules.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('depreciationSchedules')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          {canManage && (
            <Button variant="primary" size="sm" onClick={handleOpenCreate}>
              {t('addDepreciationSchedule')}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('assetName')}</th>
            <th>{t('fiscalPeriod')}</th>
            <th>{t('depreciationAmount')}</th>
            <th>{t('accumulatedDepreciation')}</th>
            <th>{t('isPosted')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {schedules.length === 0 ? (
            <tr>
              <td colSpan="6" className="text-center">{t('noDepreciationSchedules')}</td>
            </tr>
          ) : (
            schedules.map((schedule) => (
              <tr key={schedule.id}>
                <td>{getAssetName(schedule.asset)}</td>
                <td>{getPeriodName(schedule.fiscal_period)}</td>
                <td>{schedule.depreciation_amount}</td>
                <td>{schedule.accumulated_depreciation}</td>
                <td>
                  {schedule.is_posted ? (
                    <Badge bg="success" className="badge-status">{t('posted')}</Badge>
                  ) : (
                    <Badge bg="secondary" className="badge-status">{t('draft')}</Badge>
                  )}
                </td>
                <td>
                  {canManage && (
                    <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEdit(schedule)}>
                      {t('edit')}
                    </Button>
                  )}
                  {!schedule.is_posted && canPost && (
                    <Button
                      variant="outline-primary"
                      size="sm"
                      className="me-2"
                      disabled={postingId === schedule.id}
                      onClick={() => handlePost(schedule.id)}
                    >
                      {postingId === schedule.id ? t('posting') : t('postDepreciation')}
                    </Button>
                  )}
                  {canManage && (
                    <Button variant="outline-danger" size="sm" onClick={() => handleDelete(schedule.id)}>
                      {t('delete')}
                    </Button>
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

      <Modal show={showModal} onHide={handleCloseModal} centered>
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingSchedule ? t('editDepreciationSchedule') : t('addDepreciationSchedule')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>{t('assetName')} *</Form.Label>
              <Form.Select name="asset" value={formData.asset} onChange={handleChange} required>
                <option value="">{t('selectAsset')}</option>
                {assets.map((asset) => (
                  <option key={asset.id} value={asset.id}>{asset.name}</option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>{t('fiscalPeriod')} *</Form.Label>
              <Form.Select name="fiscal_period" value={formData.fiscal_period} onChange={handleChange} required>
                <option value="">{t('selectPeriod')}</option>
                {fiscalPeriods.map((period) => (
                  <option key={period.id} value={period.id}>
                    {period.name} ({period.start_date} - {period.end_date})
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('depreciationAmount')} *</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="depreciation_amount"
                    value={formData.depreciation_amount}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('accumulatedDepreciation')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="accumulated_depreciation"
                    value={formData.accumulated_depreciation}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
            </Row>
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

export default DepreciationSchedules
