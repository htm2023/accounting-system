import React, { useState } from 'react'
import { Form, Button, Alert, Container, Row, Col, Card } from 'react-bootstrap'
import { useDispatch } from 'react-redux'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import api from '../api/axios'
import { setCredentials } from '../store/authSlice'

const Login = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await api.post('/auth/login/', {
        username,
        password,
      })
      const { access, refresh, user } = response.data
      // حفظ التوكنز وبيانات المستخدم في localStorage (لإعادة التعبئة بعد تحديث الصفحة)
      localStorage.setItem('access_token', access)
      localStorage.setItem('refresh_token', refresh)
      localStorage.setItem('user', JSON.stringify(user))
      // حفظ بيانات المستخدم في Redux
      dispatch(setCredentials({ user, token: access }))
      navigate('/')
    } catch (err) {
      if (err.response && err.response.data) {
        setError(t('loginError'))
      } else {
        setError(t('serverError'))
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container fluid className="bg-light min-vh-100 d-flex align-items-center justify-content-center">
      <Row className="w-100 justify-content-center">
        <Col xs={12} sm={8} md={6} lg={4}>
          <Card>
            <Card.Body className="p-4">
              <h3 className="text-center mb-4">{t('login')}</h3>
              {error && <Alert variant="danger">{error}</Alert>}
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3" controlId="username">
                  <Form.Label>{t('username')}</Form.Label>
                  <Form.Control
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    autoFocus
                  />
                </Form.Group>
                <Form.Group className="mb-3" controlId="password">
                  <Form.Label>{t('password')}</Form.Label>
                  <Form.Control
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                  />
                </Form.Group>
                <Button variant="primary" type="submit" disabled={loading} className="w-100">
                  {loading ? 'جارٍ التحميل...' : t('loginButton')}
                </Button>
              </Form>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </Container>
  )
}

export default Login
