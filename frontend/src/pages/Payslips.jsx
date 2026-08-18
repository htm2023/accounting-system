import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { getPayslips, createPayslip, postPayslip, getEmployees } from '../api/payroll'
import { getFiscalPeriods } from '../api/fiscal'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  employee: '',
  fiscal_period: '',
  basic_salary: '',
  allowances: '0',
  deductions: '0',
}

const Payslips = () => {
  const { t } = useTranslation()
  const role = useSelector((state) => state.auth.user?.role)
  const canManage = role === 'Admin' || role === 'Accountant'
  const canPost = role === 'Admin'
  const [payslips, setPayslips] = useState([])
  const [employees, setEmployees] = useState([])
  const [fiscalPeriods, setFiscalPeriods] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
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
      const [payslipsData, employeesData, periodsData] = await Promise.all([
        getPayslips(page),
        getEmployees(),
        getFiscalPeriods(),
      ])
      setPayslips(payslipsData.results || payslipsData)
      setCurrentPage(payslipsData.current_page || 1)
      setTotalPages(payslipsData.total_pages || 1)
      setTotalCount(payslipsData.count || 0)
      setEmployees(employeesData.results || employeesData)
      setFiscalPeriods(periodsData.results || periodsData)
    } catch (err) {
      setError(t('failedLoadPayslips'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const getEmployeeName = (employeeId) => {
    const employee = employees.find((e) => e.id === employeeId)
    return employee ? employee.name : employeeId
  }

  const getPeriodName = (periodId) => {
    const period = fiscalPeriods.find((p) => p.id === periodId)
    return period ? period.name : periodId
  }

  const handleOpenCreate = () => {
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    if (name === 'employee') {
      const employee = employees.find((emp) => emp.id === Number(value))
      setFormData((prev) => ({
        ...prev,
        employee: value,
        basic_salary: employee ? employee.basic_salary : prev.basic_salary,
      }))
      return
    }
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    const payload = {
      employee: Number(formData.employee),
      fiscal_period: Number(formData.fiscal_period),
      basic_salary: parseFloat(formData.basic_salary) || 0,
      allowances: parseFloat(formData.allowances) || 0,
      deductions: parseFloat(formData.deductions) || 0,
    }
    try {
      await createPayslip(payload)
      setShowModal(false)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedSavePayslip')))
    } finally {
      setSubmitting(false)
    }
  }

  const handlePost = async (id) => {
    if (!window.confirm(t('confirmPostPayslip'))) return
    setPostingId(id)
    setError('')
    try {
      await postPayslip(id)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedPostPayslip')))
    } finally {
      setPostingId(null)
    }
  }

  if (loading && payslips.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('payslips')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          {canManage && (
            <Button variant="primary" size="sm" onClick={handleOpenCreate}>
              {t('createPayslip')}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('employeeLabel')}</th>
            <th>{t('fiscalPeriod')}</th>
            <th>{t('basicSalary')}</th>
            <th>{t('allowances')}</th>
            <th>{t('deductions')}</th>
            <th>{t('netSalary')}</th>
            <th>{t('status')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {payslips.length === 0 ? (
            <tr>
              <td colSpan="8" className="text-center">{t('noPayslips')}</td>
            </tr>
          ) : (
            payslips.map((payslip) => (
              <tr key={payslip.id}>
                <td>{getEmployeeName(payslip.employee)}</td>
                <td>{getPeriodName(payslip.fiscal_period)}</td>
                <td>{payslip.basic_salary}</td>
                <td>{payslip.allowances}</td>
                <td>{payslip.deductions}</td>
                <td>{payslip.net_salary}</td>
                <td>
                  {payslip.journal_entry ? (
                    <Badge bg="success" className="badge-status">{t('posted')}</Badge>
                  ) : (
                    <Badge bg="secondary" className="badge-status">{t('draft')}</Badge>
                  )}
                </td>
                <td>
                  {!payslip.journal_entry && canPost && (
                    <Button
                      variant="outline-primary"
                      size="sm"
                      disabled={postingId === payslip.id}
                      onClick={() => handlePost(payslip.id)}
                    >
                      {postingId === payslip.id ? t('posting') : t('post')}
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
            <Modal.Title>{t('createPayslip')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Form.Group className="mb-3">
              <Form.Label>{t('employeeLabel')} *</Form.Label>
              <Form.Select name="employee" value={formData.employee} onChange={handleChange} required>
                <option value="">{t('selectEmployee')}</option>
                {employees.map((employee) => (
                  <option key={employee.id} value={employee.id}>{employee.name}</option>
                ))}
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>{t('fiscalPeriod')} *</Form.Label>
              <Form.Select name="fiscal_period" value={formData.fiscal_period} onChange={handleChange} required>
                <option value="">{t('selectFiscalPeriod')}</option>
                {fiscalPeriods.map((period) => (
                  <option key={period.id} value={period.id}>
                    {period.name} ({period.start_date} - {period.end_date})
                  </option>
                ))}
              </Form.Select>
            </Form.Group>
            <Row>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('basicSalary')} *</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="basic_salary"
                    value={formData.basic_salary}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('allowances')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="allowances"
                    value={formData.allowances}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
              <Col md={4}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('deductions')}</Form.Label>
                  <Form.Control
                    type="number"
                    step="0.01"
                    name="deductions"
                    value={formData.deductions}
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

export default Payslips
