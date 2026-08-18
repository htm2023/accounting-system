import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { useSelector } from 'react-redux'
import { getUsers, createUser, updateUser, deleteUser } from '../api/users'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialFormState = {
  username: '',
  full_name: '',
  email: '',
  password: '',
  role: 'Viewer',
  is_active: true,
}

const roleLabel = (t, role) => {
  const map = { Admin: t('admin'), Accountant: t('accountant'), Viewer: t('viewer') }
  return map[role] || role
}

const UsersList = () => {
  const { t } = useTranslation()
  const currentUser = useSelector((state) => state.auth.user)
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [editingUser, setEditingUser] = useState(null)
  const [formData, setFormData] = useState(initialFormState)
  const [submitting, setSubmitting] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchUsers = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const data = await getUsers(page)
      setUsers(data.results || data)
      setCurrentPage(data.current_page || 1)
      setTotalPages(data.total_pages || 1)
      setTotalCount(data.count || 0)
    } catch (err) {
      setError(t('failedLoadUsers'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchUsers(1)
  }, [])

  const handleOpenCreate = () => {
    setEditingUser(null)
    setFormData(initialFormState)
    setShowModal(true)
  }

  const handleOpenEdit = (user) => {
    setEditingUser(user)
    setFormData({
      username: user.username,
      full_name: user.full_name || '',
      email: user.email || '',
      password: '',
      role: user.role,
      is_active: user.is_active,
    })
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
    setEditingUser(null)
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
    const payload = { ...formData }
    if (editingUser && !payload.password) {
      delete payload.password
    }
    try {
      if (editingUser) {
        await updateUser(editingUser.id, payload)
      } else {
        await createUser(payload)
      }
      setShowModal(false)
      setEditingUser(null)
      fetchUsers(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveUser')))
    } finally {
      setSubmitting(false)
    }
  }

  const handleDelete = async (id) => {
    if (!window.confirm(t('confirmDeleteUser'))) return
    setError('')
    try {
      await deleteUser(id)
      fetchUsers(currentPage)
    } catch (err) {
      setError(getErrorMessage(err, t('failedDeleteUser')))
    }
  }

  if (loading && users.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('users')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchUsers(currentPage)} className="me-2">
            {t('update')}
          </Button>
          <Button variant="primary" size="sm" onClick={handleOpenCreate}>
            {t('addUser')}
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Table striped bordered hover responsive>
        <thead>
          <tr>
            <th>{t('username')}</th>
            <th>{t('fullName')}</th>
            <th>{t('email')}</th>
            <th>{t('role')}</th>
            <th>{t('isActive')}</th>
            <th>{t('actions')}</th>
          </tr>
        </thead>
        <tbody>
          {users.length === 0 ? (
            <tr>
              <td colSpan="6" className="text-center">{t('noUsers')}</td>
            </tr>
          ) : (
            users.map((user) => (
              <tr key={user.id}>
                <td>{user.username}</td>
                <td>{user.full_name || '-'}</td>
                <td>{user.email || '-'}</td>
                <td><Badge bg="info" className="badge-status">{roleLabel(t, user.role)}</Badge></td>
                <td>
                  {user.is_active ? <Badge bg="success" className="badge-status">{t('active')}</Badge> : <Badge bg="danger" className="badge-status">{t('inactive')}</Badge>}
                </td>
                <td>
                  <Button variant="outline-secondary" size="sm" className="me-2" onClick={() => handleOpenEdit(user)}>
                    {t('edit')}
                  </Button>
                  <Button
                    variant="outline-danger"
                    size="sm"
                    onClick={() => handleDelete(user.id)}
                    disabled={user.id === currentUser?.id}
                  >
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
        onPageChange={(page) => fetchUsers(page)}
      />

      <Modal show={showModal} onHide={handleCloseModal} centered size="lg">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{editingUser ? t('editUser') : t('addUser')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('username')} *</Form.Label>
                  <Form.Control
                    type="text"
                    name="username"
                    value={formData.username}
                    onChange={handleChange}
                    required
                    disabled={!!editingUser}
                  />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('fullName')}</Form.Label>
                  <Form.Control
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                  />
                </Form.Group>
              </Col>
            </Row>
            <Row>
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
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('newPassword')} {editingUser ? '' : '*'}</Form.Label>
                  <Form.Control
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required={!editingUser}
                  />
                  {editingUser && <Form.Text muted>{t('leaveBlankToKeep')}</Form.Text>}
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('role')} *</Form.Label>
                  <Form.Select name="role" value={formData.role} onChange={handleChange} required>
                    <option value="Admin">{t('admin')}</option>
                    <option value="Accountant">{t('accountant')}</option>
                    <option value="Viewer">{t('viewer')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6} className="d-flex align-items-center">
                <Form.Check
                  type="checkbox"
                  label={t('isActive')}
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleChange}
                  className="mt-4"
                />
              </Col>
            </Row>
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

export default UsersList
