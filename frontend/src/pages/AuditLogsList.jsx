import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Form, Row, Col, Button, Badge } from 'react-bootstrap'
import { getAuditLogs } from '../api/auditLogs'
import { useTranslation } from 'react-i18next'
import Pagination from '../components/Pagination'

const AuditLogsList = () => {
  const { t } = useTranslation()
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ action: '', model_name: '', user__username: '' })
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchLogs = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const params = {}
      if (filters.action) params.action = filters.action
      if (filters.model_name) params.model_name = filters.model_name
      if (filters.user__username) params.user__username = filters.user__username
      const data = await getAuditLogs(params, page)
      setLogs(data.results || data)
      setCurrentPage(data.current_page || 1)
      setTotalPages(data.total_pages || 1)
      setTotalCount(data.count || 0)
    } catch (err) {
      setError(t('failedLoadAuditLogs'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs(1)
  }, [])

  const handleFilterChange = (e) => {
    const { name, value } = e.target
    setFilters((prev) => ({ ...prev, [name]: value }))
  }

  const handleFilterSubmit = (e) => {
    e.preventDefault()
    fetchLogs(1)
  }

  if (loading) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <h4>{t('auditLogs')}</h4>
      <Form onSubmit={handleFilterSubmit} className="mb-3">
        <Row>
          <Col md={3}>
            <Form.Group>
              <Form.Label>{t('action')}</Form.Label>
              <Form.Select name="action" value={filters.action} onChange={handleFilterChange}>
                <option value="">{t('all')}</option>
                <option value="Create">Create</option>
                <option value="Update">Update</option>
                <option value="Delete">Delete</option>
                <option value="Login">Login</option>
                <option value="Logout">Logout</option>
                <option value="Post">Post</option>
                <option value="Reverse">Reverse</option>
                <option value="Close">Close</option>
              </Form.Select>
            </Form.Group>
          </Col>
          <Col md={3}>
            <Form.Group>
              <Form.Label>{t('modelName')}</Form.Label>
              <Form.Control type="text" name="model_name" value={filters.model_name} onChange={handleFilterChange} />
            </Form.Group>
          </Col>
          <Col md={3}>
            <Form.Group>
              <Form.Label>{t('username')}</Form.Label>
              <Form.Control type="text" name="user__username" value={filters.user__username} onChange={handleFilterChange} />
            </Form.Group>
          </Col>
          <Col md={3} className="d-flex align-items-end">
            <Button variant="primary" type="submit">{t('filter')}</Button>
          </Col>
        </Row>
      </Form>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('timestamp')}</th>
            <th>{t('username')}</th>
            <th>{t('action')}</th>
            <th>{t('modelName')}</th>
            <th>{t('objectId')}</th>
            <th>{t('description')}</th>
            <th>{t('ipAddress')}</th>
          </tr>
        </thead>
        <tbody>
          {logs.length === 0 ? (
            <tr>
              <td colSpan="7" className="text-center">{t('noAuditLogs')}</td>
            </tr>
          ) : (
            logs.map((log) => (
              <tr key={log.id}>
                <td>{new Date(log.timestamp).toLocaleString()}</td>
                <td>{log.user_username || log.user_full_name || '-'}</td>
                <td><Badge bg="secondary">{log.action}</Badge></td>
                <td>{log.model_name}</td>
                <td>{log.object_id}</td>
                <td>{log.description}</td>
                <td>{log.ip_address || '-'}</td>
              </tr>
            ))
          )}
        </tbody>
      </Table>

      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        onPageChange={(page) => fetchLogs(page)}
      />
    </div>
  )
}

export default AuditLogsList
