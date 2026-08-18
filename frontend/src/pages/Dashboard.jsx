import React from 'react'
import { Container, Row, Col, Card } from 'react-bootstrap'
import { useSelector } from 'react-redux'
import { useTranslation } from 'react-i18next'

const Dashboard = () => {
  const user = useSelector((state) => state.auth.user)
  const { t } = useTranslation()

  return (
    <Container className="mt-4">
      <h2>{t('dashboard')}</h2>
      {user && (
        <Card className="mt-3">
          <Card.Body>
            <Card.Title>{t('welcome')}, {user.full_name || user.username}</Card.Title>
            <Card.Text>
              {t('role')}: {user.role}
            </Card.Text>
          </Card.Body>
        </Card>
      )}
    </Container>
  )
}

export default Dashboard
