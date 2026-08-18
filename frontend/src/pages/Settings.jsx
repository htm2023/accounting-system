import React from 'react'
import { Container, Card, Row, Col, Badge } from 'react-bootstrap'
import { useSelector } from 'react-redux'
import { useTranslation } from 'react-i18next'

const Settings = () => {
  const user = useSelector((state) => state.auth.user)
  const { t, i18n } = useTranslation()

  return (
    <Container className="mt-2">
      <h2>{t('settings')}</h2>

      <Card className="mt-3">
        <Card.Body>
          <Card.Title>{t('aboutSystem')}</Card.Title>
          <Card.Text className="text-muted">{t('systemDescription')}</Card.Text>
          <Row className="mt-3">
            <Col md={4}>
              <div className="text-muted small">{t('version')}</div>
              <div className="fw-bold">1.0.0</div>
            </Col>
            <Col md={4}>
              <div className="text-muted small">{t('interfaceLanguage')}</div>
              <div className="fw-bold">{i18n.language === 'ar' ? 'العربية' : 'English'}</div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {user && (
        <Card className="mt-3">
          <Card.Body>
            <Card.Title>{t('accountInfo')}</Card.Title>
            <Row className="mt-3">
              <Col md={4}>
                <div className="text-muted small">{t('fullName')}</div>
                <div className="fw-bold">{user.full_name || '-'}</div>
              </Col>
              <Col md={4}>
                <div className="text-muted small">{t('username')}</div>
                <div className="fw-bold">{user.username}</div>
              </Col>
              <Col md={4}>
                <div className="text-muted small">{t('role')}</div>
                <Badge bg="primary" className="badge-status">{user.role}</Badge>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}
    </Container>
  )
}

export default Settings
