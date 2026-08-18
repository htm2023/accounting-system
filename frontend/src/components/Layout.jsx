import React from 'react'
import { Navbar, Nav, Container, Button } from 'react-bootstrap'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useDispatch, useSelector } from 'react-redux'
import { useTranslation } from 'react-i18next'
import { logout } from '../store/authSlice'
import api from '../api/axios'

const Layout = () => {
  const dispatch = useDispatch()
  const navigate = useNavigate()
  const user = useSelector((state) => state.auth.user)
  const { t, i18n } = useTranslation()

  const toggleLanguage = () => {
    const newLang = i18n.language === 'ar' ? 'en' : 'ar'
    i18n.changeLanguage(newLang)
  }

  const handleLogout = async () => {
    try {
      await api.post('/auth/logout/')
    } catch (err) {
      // تجاهل الخطأ إذا انتهت الجلسة أو فشل الاتصال
    }
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    dispatch(logout())
    navigate('/login')
  }

  return (
    <div className="d-flex flex-column min-vh-100">
      {/* الشريط العلوي */}
      <Navbar bg="dark" variant="dark" expand="lg">
        <Container fluid>
          <Navbar.Brand as={NavLink} to="/dashboard">
            {t('appTitle')}
          </Navbar.Brand>
          <Navbar.Toggle aria-controls="main-navbar" />
          <Navbar.Collapse id="main-navbar">
            <Nav className="ms-auto align-items-center">
              <span className="text-light me-3">
                {user?.full_name || user?.username} ({user?.role})
              </span>
              <Button variant="outline-info" size="sm" onClick={toggleLanguage} className="me-2">
                {i18n.language === 'ar' ? 'EN' : 'عربي'}
              </Button>
              <Button variant="outline-light" size="sm" onClick={handleLogout}>
                {t('logout')}
              </Button>
            </Nav>
          </Navbar.Collapse>
        </Container>
      </Navbar>

      <div className="d-flex flex-grow-1">
        {/* الشريط الجانبي */}
        <div className="bg-light p-3" style={{ width: '230px', minHeight: '100%' }}>
          <Nav className="flex-column">
            <NavLink to="/dashboard" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('dashboard')}
            </NavLink>
            <NavLink to="/accounts" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('accounts')}
            </NavLink>
            <NavLink to="/journal-entries" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('journalEntries')}
            </NavLink>
            <NavLink to="/parties" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('parties')}
            </NavLink>
            <NavLink to="/invoices" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('invoices')}
            </NavLink>
            <NavLink to="/payments" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('payments')}
            </NavLink>
            <NavLink to="/inventory" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('inventory')}
            </NavLink>
            <NavLink to="/currencies" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('currencies')}
            </NavLink>
            <NavLink to="/cost-centers" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('costCenters')}
            </NavLink>
            <NavLink to="/employees" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('employees')}
            </NavLink>
            <NavLink to="/payslips" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('payslips')}
            </NavLink>
            <NavLink to="/fixed-assets" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('fixedAssets')}
            </NavLink>
            <NavLink to="/depreciation-schedules" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('depreciationSchedules')}
            </NavLink>
            <NavLink to="/reports" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('reports')}
            </NavLink>
            <NavLink to="/audit-logs" className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}>
              {t('auditLogs')}
            </NavLink>
          </Nav>
        </div>

        {/* المحتوى الرئيسي */}
        <div className="p-4 flex-grow-1">
          <Outlet />
        </div>
      </div>
    </div>
  )
}

export default Layout
