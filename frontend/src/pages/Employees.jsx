import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { getEmployees, createEmployee, updateEmployee, deleteEmployee } from '../api/payroll'
import { getAccounts } from '../api/accounts'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  name: '',
  position: '',
  basic_salary: '',
  hire_date: '',
  status: 'Active',
  salary_account: '',
  payment_account: '',
}

const Employees = () => {
  const { t } = useTranslation()
  const role = useSelector((state) => state.auth.user?.role)
  const canManage = role === 'Admin' || role === 'Accountant'
  const [employees, setEmployees] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingEmployee, setEditingEmployee] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [submitting, setSubmitting] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [employeesData, accountsData] = await Promise.all([
        getEmployees(page),
        getAccounts(),
      ])
      setEmployees(employeesData.results || employeesData)
      setCurrentPage(employeesData.current_page || 1)
      setTotalPages(employeesData.total_pages || 1)
      setTotalCount(employeesData.count || 0)
      setAccounts(accountsData.results || accountsData)
    } catch (err) {
      setError(t('failedLoadEmployees'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const handleOpenCreate = () => {
    setEditingEmployee(null)
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleOpenEdit = (employee) => {
    setEditingEmployee(employee)
    setFormData({
      name: employee.name,
      position: employee.position || '',
      basic_salary: employee.basic_salary,
      hire_date: employee.hire_date,
      status: employee.status,
      salary_account: employee.salary_account || '',
      payment_account: employee.payment_account || '',
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingEmployee(null)
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
      basic_salary: parseFloat(formData.basic_salary) || 0,
      salary_account: formData.salary_account ? Number(formData.salary_account) : null,
      payment_account: formData.payment_account ? Number(formData.payment_account) : null,
    }
    try {
      if (editingEmployee) {
        await updateEmployee(editingEmployee.id, payload)
      } else {
        await createEmployee(payload)
      }
      setShowModal(false)
      setEditingEmployee(null)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveEmployee')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirmDeleteEmployee'))) return
    setError('')
    try {
      await deleteEmployee(id)
      fetchData(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteEmployee')))
    }
  }

  if (loading && employees.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('employees')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          {canManage && (
            <Button variant="primary" size="sm" onClick={handleOpenCreate}>
              {t('addEmployee')}
            </Button>
          )}
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('employeeName')}</th>
            <th>{t('position')}</th>
            <th>{t('basicSalary')}</th>
            <th>{t('hireDate')}</th>
            <th>{t('employeeStatus')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {employees.length === 0 ? (
            <tr>
              <td colSpan="6" className="text-center">{t('noEmployees')}</td>
            </tr>
          ) : (
            employees.map((employee) => (
              <tr key={employee.id}>
                <td>{employee.name}</td>
                <td>{employee.position || '-'}</td>
                <td>{employee.basic_salary}</td>
                <td>{employee.hire_date}</td>
                <td>
                  {employee.status === 'Active' ? (
                    <Badge bg="success" className="badge-status">{t('employeeActive')}</Badge>
                  ) : (
                    <Badge bg="danger" className="badge-status">{t('employeeTerminated')}</Badge>
                  )}
                </td>
                <td>
                  {canManage && (
                    <>
                      <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEdit(employee)}>
                        {t('edit')}
                      </Button>
                      <Button variant="outline-danger" size="sm" onClick={() => handleDelete(employee.id)}>
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

      <Modal show={showModal} onHide={handleCloseModal} centered size="lg">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingEmployee ? t('editEmployee') : t('addEmployee')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('employeeName')} *</Form.Label>
                  <Form.Control type="text" name="name" value={formData.name} onChange={handleChange} required />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('position')}</Form.Label>
                  <Form.Control type="text" name="position" value={formData.position} onChange={handleChange} />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
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
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('hireDate')} *</Form.Label>
                  <Form.Control
                    type="date"
                    name="hire_date"
                    value={formData.hire_date}
                    onChange={handleChange}
                    required
                  />
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>{t('employeeStatus')} *</Form.Label>
              <Form.Select name="status" value={formData.status} onChange={handleChange} required>
                <option value="Active">{t('employeeActive')}</option>
                <option value="Terminated">{t('employeeTerminated')}</option>
              </Form.Select>
            </Form.Group>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('salaryAccount')} *</Form.Label>
                  <Form.Select name="salary_account" value={formData.salary_account} onChange={handleChange} required>
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
                  <Form.Label>{t('paymentAccount')} *</Form.Label>
                  <Form.Select name="payment_account" value={formData.payment_account} onChange={handleChange} required>
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

export default Employees
