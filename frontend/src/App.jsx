import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'
import AccountsList from './pages/AccountsList'
import JournalEntriesList from './pages/JournalEntriesList'
import PartiesList from './pages/PartiesList'
import InvoicesList from './pages/InvoicesList'
import PaymentsList from './pages/PaymentsList'
import InventoryList from './pages/InventoryList'
import ReportsList from './pages/ReportsList'
import AuditLogsList from './pages/AuditLogsList'
import Currencies from './pages/Currencies'
import CostCenters from './pages/CostCenters'
import Payslips from './pages/Payslips'
import Employees from './pages/Employees'
import FixedAssets from './pages/FixedAssets'
import DepreciationSchedules from './pages/DepreciationSchedules'
import UsersList from './pages/UsersList'
import Settings from './pages/Settings'

const App = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          element={
            <PrivateRoute>
              <Layout />
            </PrivateRoute>
          }
        >
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route
            path="/accounts"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <AccountsList />
              </PrivateRoute>
            }
          />
          <Route
            path="/journal-entries"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <JournalEntriesList />
              </PrivateRoute>
            }
          />
          <Route
            path="/parties"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <PartiesList />
              </PrivateRoute>
            }
          />
          <Route
            path="/invoices"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <InvoicesList />
              </PrivateRoute>
            }
          />
          <Route
            path="/payments"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <PaymentsList />
              </PrivateRoute>
            }
          />
          <Route
            path="/inventory"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <InventoryList />
              </PrivateRoute>
            }
          />
          <Route
            path="/reports"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant', 'Viewer']}>
                <ReportsList />
              </PrivateRoute>
            }
          />
          <Route
            path="/audit-logs"
            element={
              <PrivateRoute allowedRoles={['Admin']}>
                <AuditLogsList />
              </PrivateRoute>
            }
          />
          <Route
            path="/users"
            element={
              <PrivateRoute allowedRoles={['Admin']}>
                <UsersList />
              </PrivateRoute>
            }
          />
          <Route
            path="/currencies"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <Currencies />
              </PrivateRoute>
            }
          />
          <Route
            path="/cost-centers"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <CostCenters />
              </PrivateRoute>
            }
          />
          <Route
            path="/payslips"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <Payslips />
              </PrivateRoute>
            }
          />
          <Route
            path="/employees"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <Employees />
              </PrivateRoute>
            }
          />
          <Route
            path="/fixed-assets"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <FixedAssets />
              </PrivateRoute>
            }
          />
          <Route
            path="/depreciation-schedules"
            element={
              <PrivateRoute allowedRoles={['Admin', 'Accountant']}>
                <DepreciationSchedules />
              </PrivateRoute>
            }
          />
          <Route path="/settings" element={<Settings />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
