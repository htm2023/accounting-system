import React, { useState, useEffect } from 'react'
import { Container, Row, Col, Card, Table, Spinner, Alert, Button, Form, Tabs, Tab } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import {
  getTrialBalance,
  getIncomeStatement,
  getBalanceSheet,
  getCashFlow,
  getPartyStatement,
  exportTrialBalance,
  exportIncomeStatement,
  exportBalanceSheet,
  exportCashFlow,
  exportPartyStatement,
  exportTrialBalancePDF,
  exportIncomeStatementPDF,
  exportBalanceSheetPDF,
  exportCashFlowPDF,
  exportPartyStatementPDF,
} from '../api/reports'
import { getFiscalPeriods } from '../api/fiscal'
import { getParties } from '../api/parties'
import { getErrorMessage } from '../utils/errorHandler'

const ReportsList = () => {
  const { t } = useTranslation()
  const [fiscalPeriods, setFiscalPeriods] = useState([])
  const [parties, setParties] = useState([])
  const [selectedPeriod, setSelectedPeriod] = useState('')
  const [selectedParty, setSelectedParty] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeReport, setActiveReport] = useState('trial-balance')

  const [trialBalance, setTrialBalance] = useState([])
  const [incomeStatement, setIncomeStatement] = useState(null)
  const [balanceSheet, setBalanceSheet] = useState(null)
  const [cashFlow, setCashFlow] = useState(null)
  const [partyStatement, setPartyStatement] = useState(null)

  const fetchFiscalPeriodsAndParties = async () => {
    try {
      const [periodsData, partiesData] = await Promise.all([
        getFiscalPeriods(),
        getParties(),
      ])
      setFiscalPeriods(periodsData.results || periodsData)
      setParties(partiesData.results || partiesData)
    } catch (err) {
      console.error('Failed to load fiscal periods/parties', err)
    }
  }

  useEffect(() => {
    fetchFiscalPeriodsAndParties()
  }, [])

  const fetchReport = async () => {
    setLoading(true)
    setError('')
    try {
      const periodId = selectedPeriod ? Number(selectedPeriod) : null
      switch (activeReport) {
        case 'trial-balance': {
          const data = await getTrialBalance(periodId)
          setTrialBalance(data)
          break
        }
        case 'income-statement': {
          const data = await getIncomeStatement(periodId)
          setIncomeStatement(data)
          break
        }
        case 'balance-sheet': {
          const data = await getBalanceSheet(periodId)
          setBalanceSheet(data)
          break
        }
        case 'cash-flow': {
          const data = await getCashFlow(periodId)
          setCashFlow(data)
          break
        }
        case 'party-statement': {
          if (!selectedParty) {
            setError(t('selectPartyFirst'))
            setLoading(false)
            return
          }
          const data = await getPartyStatement(Number(selectedParty))
          setPartyStatement(data)
          break
        }
        default:
          break
      }
    } catch (err) {
      setError(getErrorMessage(err, t('failedLoadReport')))
    } finally {
      setLoading(false)
    }
  }

  const handleTabChange = (tab) => {
    setActiveReport(tab)
    // مسح البيانات القديمة عند التبديل
    setTrialBalance([])
    setIncomeStatement(null)
    setBalanceSheet(null)
    setCashFlow(null)
    setPartyStatement(null)
    setError('')
  }

  const downloadBlob = (blob, filename) => {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  }

  const handleExport = async (exportFn, filename) => {
    try {
      const blob = await exportFn(selectedPeriod ? Number(selectedPeriod) : null)
      downloadBlob(blob, filename)
    } catch (err) {
      setError(t('failedExport'))
    }
  }

  return (
    <Container fluid>
      <h4 className="mb-3">{t('financialReports')}</h4>

      <Row className="mb-3">
        <Col md={4}>
          <Form.Group>
            <Form.Label>{t('selectPeriod')}</Form.Label>
            <Form.Select value={selectedPeriod} onChange={(e) => setSelectedPeriod(e.target.value)}>
              <option value="">{t('allOpenPeriods')}</option>
              {fiscalPeriods.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </Form.Select>
          </Form.Group>
        </Col>
        {activeReport === 'party-statement' && (
          <Col md={4}>
            <Form.Group>
              <Form.Label>{t('selectParty')} *</Form.Label>
              <Form.Select value={selectedParty} onChange={(e) => setSelectedParty(e.target.value)}>
                <option value="">{t('selectParty')}</option>
                {parties.map((p) => (
                  <option key={p.id} value={p.id}>{p.name_ar || p.name_en}</option>
                ))}
              </Form.Select>
            </Form.Group>
          </Col>
        )}
        <Col md={4} className="d-flex align-items-end">
          <Button variant="primary" onClick={fetchReport} disabled={loading}>
            {loading ? t('loading') : t('viewReport')}
          </Button>
        </Col>
      </Row>

      {error && <Alert variant="danger">{error}</Alert>}

      <Tabs activeKey={activeReport} onSelect={handleTabChange} className="mb-3">
        <Tab eventKey="trial-balance" title={t('trialBalance')}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5>{t('trialBalance')}</h5>
            <div>
              <Button variant="outline-success" size="sm" className="me-2" onClick={() => handleExport(exportTrialBalance, 'trial_balance.xlsx')}>
                {t('exportExcel')}
              </Button>
              <Button variant="outline-primary" size="sm" onClick={() => handleExport(exportTrialBalancePDF, 'trial_balance.pdf')}>
                {t('exportPDF')}
              </Button>
            </div>
          </div>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>{t('accountCode')}</th>
                <th>{t('accountName')}</th>
                <th>{t('accountType')}</th>
                <th>{t('debit')}</th>
                <th>{t('credit')}</th>
                <th>{t('balance')}</th>
              </tr>
            </thead>
            <tbody>
              {trialBalance.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center">{t('noData')}</td>
                </tr>
              ) : (
                trialBalance.map((row, idx) => (
                  <tr key={idx}>
                    <td>{row.account_code}</td>
                    <td>{row.account_name_ar}</td>
                    <td>{row.account_type}</td>
                    <td>{row.total_debit}</td>
                    <td>{row.total_credit}</td>
                    <td>{row.balance}</td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </Tab>

        <Tab eventKey="income-statement" title={t('incomeStatement')}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5>{t('incomeStatement')}</h5>
            <div>
              <Button variant="outline-success" size="sm" className="me-2" onClick={() => handleExport(exportIncomeStatement, 'income_statement.xlsx')}>
                {t('exportExcel')}
              </Button>
              <Button variant="outline-primary" size="sm" onClick={() => handleExport(exportIncomeStatementPDF, 'income_statement.pdf')}>
                {t('exportPDF')}
              </Button>
            </div>
          </div>
          {incomeStatement ? (
            <Card>
              <Card.Body>
                <Card.Title>{t('incomeStatement')}</Card.Title>
                <Table bordered>
                  <tbody>
                    <tr>
                      <td>{t('revenue')}</td>
                      <td>{incomeStatement.revenue}</td>
                    </tr>
                    <tr>
                      <td>{t('expenses')}</td>
                      <td>{incomeStatement.expenses}</td>
                    </tr>
                    <tr>
                      <td><strong>{t('netProfit')}</strong></td>
                      <td><strong>{incomeStatement.net_profit}</strong></td>
                    </tr>
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          ) : (
            <Alert variant="info">{t('pressViewReport')}</Alert>
          )}
        </Tab>

        <Tab eventKey="balance-sheet" title={t('balanceSheet')}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5>{t('balanceSheet')}</h5>
            <div>
              <Button variant="outline-success" size="sm" className="me-2" onClick={() => handleExport(exportBalanceSheet, 'balance_sheet.xlsx')}>
                {t('exportExcel')}
              </Button>
              <Button variant="outline-primary" size="sm" onClick={() => handleExport(exportBalanceSheetPDF, 'balance_sheet.pdf')}>
                {t('exportPDF')}
              </Button>
            </div>
          </div>
          {balanceSheet ? (
            <Card>
              <Card.Body>
                <Card.Title>{t('balanceSheet')}</Card.Title>
                <Table bordered>
                  <tbody>
                    <tr>
                      <td>{t('assets')}</td>
                      <td>{balanceSheet.assets}</td>
                    </tr>
                    <tr>
                      <td>{t('liabilities')}</td>
                      <td>{balanceSheet.liabilities}</td>
                    </tr>
                    <tr>
                      <td>{t('equity')}</td>
                      <td>{balanceSheet.equity}</td>
                    </tr>
                    <tr>
                      <td><strong>{t('totalLiabilitiesEquity')}</strong></td>
                      <td><strong>{balanceSheet.total_liabilities_equity}</strong></td>
                    </tr>
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          ) : (
            <Alert variant="info">{t('pressViewReport')}</Alert>
          )}
        </Tab>

        <Tab eventKey="cash-flow" title={t('cashFlow')}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5>{t('cashFlow')}</h5>
            <div>
              <Button variant="outline-success" size="sm" className="me-2" onClick={() => handleExport(exportCashFlow, 'cash_flow.xlsx')}>
                {t('exportExcel')}
              </Button>
              <Button variant="outline-primary" size="sm" onClick={() => handleExport(exportCashFlowPDF, 'cash_flow.pdf')}>
                {t('exportPDF')}
              </Button>
            </div>
          </div>
          {cashFlow ? (
            <Card>
              <Card.Body>
                <Card.Title>{t('cashFlow')}</Card.Title>
                <Table bordered>
                  <tbody>
                    <tr>
                      <td>{t('cashInflow')}</td>
                      <td>{cashFlow.cash_inflow}</td>
                    </tr>
                    <tr>
                      <td>{t('cashOutflow')}</td>
                      <td>{cashFlow.cash_outflow}</td>
                    </tr>
                    <tr>
                      <td><strong>{t('netCashFlow')}</strong></td>
                      <td><strong>{cashFlow.net_cash_flow}</strong></td>
                    </tr>
                  </tbody>
                </Table>
              </Card.Body>
            </Card>
          ) : (
            <Alert variant="info">{t('pressViewReport')}</Alert>
          )}
        </Tab>

        <Tab eventKey="party-statement" title={t('partyStatement')}>
          <div className="d-flex justify-content-between align-items-center mb-2">
            <h5>{t('partyStatement')}</h5>
            <div>
              <Button variant="outline-success" size="sm" className="me-2" onClick={() => {
                if (!selectedParty) {
                  setError(t('selectPartyFirst'))
                  return
                }
                handleExport(() => exportPartyStatement(Number(selectedParty)), 'party_statement.xlsx')
              }}>
                {t('exportExcel')}
              </Button>
              <Button variant="outline-primary" size="sm" onClick={() => {
                if (!selectedParty) {
                  setError(t('selectPartyFirst'))
                  return
                }
                handleExport(() => exportPartyStatementPDF(Number(selectedParty)), 'party_statement.pdf')
              }}>
                {t('exportPDF')}
              </Button>
            </div>
          </div>
          {partyStatement ? (
            <Card>
              <Card.Body>
                <Card.Title>{t('partyStatement')}: {partyStatement.party}</Card.Title>
                <p>{t('openingBalance')}: {partyStatement.opening_balance}</p>
                <Table bordered striped responsive>
                  <thead>
                    <tr>
                      <th>{t('date')}</th>
                      <th>{t('description')}</th>
                      <th>{t('debit')}</th>
                      <th>{t('credit')}</th>
                      <th>{t('balance')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {partyStatement.entries.map((entry, idx) => (
                      <tr key={idx}>
                        <td>{entry.date}</td>
                        <td>{entry.description}</td>
                        <td>{entry.debit}</td>
                        <td>{entry.credit}</td>
                        <td>{entry.balance}</td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
                <p><strong>{t('closingBalance')}: {partyStatement.closing_balance}</strong></p>
              </Card.Body>
            </Card>
          ) : (
            <Alert variant="info">{t('pressViewReport')}</Alert>
          )}
        </Tab>
      </Tabs>
    </Container>
  )
}

export default ReportsList
