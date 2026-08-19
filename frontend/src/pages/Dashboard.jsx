import React, { useEffect, useState } from 'react'
import { Container, Row, Col, Card, Spinner } from 'react-bootstrap'
import { useSelector } from 'react-redux'
import { useTranslation } from 'react-i18next'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { getAccounts } from '../api/accounts'
import { getJournalEntries } from '../api/journalEntries'
import { getInvoices } from '../api/invoices'
import { getReceiptPayments } from '../api/payments'
import { getParties } from '../api/parties'
import { getProducts } from '../api/inventory'

const STATS = [
  { key: 'accounts', icon: 'bi-diagram-3', fetcher: getAccounts, label: 'accounts' },
  { key: 'journalEntries', icon: 'bi-journal-text', fetcher: getJournalEntries, label: 'journalEntries' },
  { key: 'invoices', icon: 'bi-receipt', fetcher: getInvoices, label: 'invoices' },
  { key: 'payments', icon: 'bi-cash-coin', fetcher: getReceiptPayments, label: 'payments', chartLabel: 'paymentsShort' },
  { key: 'parties', icon: 'bi-people', fetcher: getParties, label: 'parties' },
  { key: 'products', icon: 'bi-box-seam', fetcher: getProducts, label: 'products' },
]

const Dashboard = () => {
  const user = useSelector((state) => state.auth.user)
  const { t } = useTranslation()
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let active = true
    const loadStats = async () => {
      const results = await Promise.allSettled(STATS.map((s) => s.fetcher(1, 1)))
      if (!active) return
      const computed = STATS.map((s, i) => ({
        ...s,
        count: results[i].status === 'fulfilled' ? (results[i].value.count ?? 0) : null,
      }))
      setStats(computed)
      setLoading(false)
    }
    loadStats()
    return () => { active = false }
  }, [])

  const chartData = (stats || [])
    .filter((s) => s.count !== null)
    .map((s) => ({ name: t(s.chartLabel || s.label), [t('total')]: s.count }))

  return (
    <Container fluid className="mt-2">
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

      {loading ? (
        <div className="text-center my-5">
          <Spinner animation="border" variant="primary" />
        </div>
      ) : (
        <>
          <Row className="mt-4 g-3">
            {stats.filter((s) => s.count !== null).map((s) => (
              <Col key={s.key} xs={6} md={4} lg={2}>
                <Card className="card-stat h-100">
                  <Card.Body className="d-flex align-items-center gap-3">
                    <div className="stat-icon">
                      <i className={`bi ${s.icon}`}></i>
                    </div>
                    <div>
                      <div className="value">{s.count}</div>
                      <div className="text-muted small">{t(s.label)}</div>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>

          {chartData.length > 0 && (
            <Card className="chart-card mt-4">
              <Card.Body>
                <Card.Title>{t('overview')}</Card.Title>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" />
                    <YAxis allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey={t('total')} fill="#4f46e5" radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card.Body>
            </Card>
          )}
        </>
      )}
    </Container>
  )
}

export default Dashboard
