import React, { useState, useEffect } from 'react'
import { Table, Spinner, Alert, Button, Badge, Modal, Form, Row, Col, Tabs, Tab } from 'react-bootstrap'
import { useTranslation } from 'react-i18next'
import { getProducts, getStockMovements, createProduct } from '../api/inventory'
import { getAccounts } from '../api/accounts'
import { getErrorMessage } from '../utils/errorHandler'
import Pagination from '../components/Pagination'

const initialProductForm = {
  sku: '',
  name_ar: '',
  name_en: '',
  description: '',
  unit: 'piece',
  valuation_method: 'Weighted Average',
  selling_price: '',
  reorder_level: '0',
  inventory_account: '',
  cogs_account: '',
}

const InventoryList = () => {
  const { t } = useTranslation()
  const [products, setProducts] = useState([])
  const [movements, setMovements] = useState([])
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [formData, setFormData] = useState(initialProductForm)
  const [activeTab, setActiveTab] = useState('products')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalCount, setTotalCount] = useState(0)

  const fetchData = async (page = 1) => {
    setLoading(true)
    setError('')
    try {
      const [productsData, movementsData, accountsData] = await Promise.all([
        getProducts(page),
        getStockMovements(1, 100), // يمكن إبقاء الحركات بدون ترقيم كبير مؤقتاً
        getAccounts(),
      ])
      setProducts(productsData.results)
      setCurrentPage(productsData.current_page || 1)
      setTotalPages(productsData.total_pages || 1)
      setTotalCount(productsData.count || 0)
      setMovements(movementsData.results || movementsData)
      setAccounts(accountsData.results || accountsData)
    } catch (err) {
      setError(t('failedLoadInventory'))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData(1)
  }, [])

  const handleOpenCreate = () => {
    setFormData(initialProductForm)
    setShowModal(true)
  }

  const handleCloseModal = () => {
    setShowModal(false)
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const getProductSku = (productId) => {
    const product = products.find((p) => p.id === productId)
    return product ? product.sku : productId
  }

  const valuationMethodLabel = (method) => (method === 'FIFO' ? t('fifo') : t('weightedAverage'))

  const movementTypeLabel = (type) => {
    const map = {
      Purchase: t('purchase'),
      Sale: t('sale'),
      Adjustment: t('adjustment'),
      Transfer: t('transfer'),
      Opening: t('opening'),
    }
    return map[type] || type
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        sku: formData.sku,
        name_ar: formData.name_ar,
        name_en: formData.name_en || null,
        description: formData.description || null,
        unit: formData.unit,
        valuation_method: formData.valuation_method,
        selling_price: parseFloat(formData.selling_price) || 0,
        reorder_level: parseFloat(formData.reorder_level) || 0,
        inventory_account: Number(formData.inventory_account),
        cogs_account: Number(formData.cogs_account),
      }
      await createProduct(payload)
      setShowModal(false)
      fetchData()
    } catch (err) {
      setError(getErrorMessage(err, t('failedSaveProduct')))
    } finally {
      setSubmitting(false)
    }
  }

  if (loading && products.length === 0) {
    return <Spinner animation="border" variant="primary" />
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h4>{t('inventory')}</h4>
        <div>
          <Button variant="outline-primary" size="sm" onClick={() => fetchData(currentPage)} className="me-2">
            {t('update')}
          </Button>
          <Button variant="primary" size="sm" onClick={handleOpenCreate}>
            {t('addProduct')}
          </Button>
        </div>
      </div>

      {error && <Alert variant="danger">{error}</Alert>}

      <Tabs activeKey={activeTab} onSelect={(k) => setActiveTab(k)} className="mb-3">
        <Tab eventKey="products" title={t('products')}>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>{t('sku')}</th>
                <th>{t('productName')}</th>
                <th>{t('unit')}</th>
                <th>{t('valuationMethod')}</th>
                <th>{t('averageCost')}</th>
                <th>{t('sellingPrice')}</th>
                <th>{t('currentStock')}</th>
              </tr>
            </thead>
            <tbody>
              {products.length === 0 ? (
                <tr>
                  <td colSpan="7" className="text-center">{t('noProducts')}</td>
                </tr>
              ) : (
                products.map((prod) => (
                  <tr key={prod.id}>
                    <td>{prod.sku}</td>
                    <td>{prod.name_ar || prod.name_en}</td>
                    <td>{prod.unit}</td>
                    <td>{valuationMethodLabel(prod.valuation_method)}</td>
                    <td>{prod.average_cost}</td>
                    <td>{prod.selling_price}</td>
                    <td>{prod.current_stock}</td>
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
        </Tab>
        <Tab eventKey="movements" title={t('stockMovements')}>
          <Table striped bordered hover responsive>
            <thead>
              <tr>
                <th>{t('productName')}</th>
                <th>{t('movementType')}</th>
                <th>{t('movementQuantity')}</th>
                <th>{t('unitCost')}</th>
                <th>{t('movementDate')}</th>
                <th>{t('reference')}</th>
              </tr>
            </thead>
            <tbody>
              {movements.length === 0 ? (
                <tr>
                  <td colSpan="6" className="text-center">{t('noMovements')}</td>
                </tr>
              ) : (
                movements.map((mov) => (
                  <tr key={mov.id}>
                    <td>{getProductSku(mov.product)}</td>
                    <td>{movementTypeLabel(mov.movement_type)}</td>
                    <td>{mov.quantity}</td>
                    <td>{mov.unit_cost}</td>
                    <td>{mov.date}</td>
                    <td>{mov.reference_type} {mov.reference_id && `#${mov.reference_id}`}</td>
                  </tr>
                ))
              )}
            </tbody>
          </Table>
        </Tab>
      </Tabs>

      {/* نموذج إضافة منتج */}
      <Modal show={showModal} onHide={handleCloseModal} centered size="lg">
        <Form onSubmit={handleSubmit}>
          <Modal.Header closeButton>
            <Modal.Title>{t('addProduct')}</Modal.Title>
          </Modal.Header>
          <Modal.Body>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('sku')} *</Form.Label>
                  <Form.Control type="text" name="sku" value={formData.sku} onChange={handleChange} required />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('nameAr')} *</Form.Label>
                  <Form.Control type="text" name="name_ar" value={formData.name_ar} onChange={handleChange} required />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('nameEn')}</Form.Label>
                  <Form.Control type="text" name="name_en" value={formData.name_en} onChange={handleChange} />
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('unit')}</Form.Label>
                  <Form.Control type="text" name="unit" value={formData.unit} onChange={handleChange} />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('valuationMethod')}</Form.Label>
                  <Form.Select name="valuation_method" value={formData.valuation_method} onChange={handleChange}>
                    <option value="Weighted Average">{t('weightedAverage')}</option>
                    <option value="FIFO">{t('fifo')}</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('sellingPrice')}</Form.Label>
                  <Form.Control type="number" step="0.01" name="selling_price" value={formData.selling_price} onChange={handleChange} />
                </Form.Group>
              </Col>
            </Row>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('inventoryAccount')} *</Form.Label>
                  <Form.Select name="inventory_account" value={formData.inventory_account} onChange={handleChange} required>
                    <option value="">{t('selectAccount')}</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>{acc.code} - {acc.name_ar || acc.name_en}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>{t('cogsAccount')} *</Form.Label>
                  <Form.Select name="cogs_account" value={formData.cogs_account} onChange={handleChange} required>
                    <option value="">{t('selectAccount')}</option>
                    {accounts.map((acc) => (
                      <option key={acc.id} value={acc.id}>{acc.code} - {acc.name_ar || acc.name_en}</option>
                    ))}
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            <Form.Group className="mb-3">
              <Form.Label>{t('description')}</Form.Label>
              <Form.Control type="text" name="description" value={formData.description} onChange={handleChange} />
            </Form.Group>
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

export default InventoryList
