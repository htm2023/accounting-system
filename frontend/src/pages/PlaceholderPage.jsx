import React from 'react'
import { Card } from 'react-bootstrap'

const PlaceholderPage = ({ title }) => {
  return (
    <Card>
      <Card.Body>
        <Card.Title>{title}</Card.Title>
        <Card.Text>
          هذه الصفحة قيد الإنشاء، وستُستكمل في الخطوات القادمة.
        </Card.Text>
      </Card.Body>
    </Card>
  )
}

export default PlaceholderPage
