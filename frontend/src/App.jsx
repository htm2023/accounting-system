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
          <Route path="/accounts" element={<AccountsList />} />
          <Route path="/journal-entries" element={<JournalEntriesList />} />
          <Route path="/parties" element={<PartiesList />} />
          <Route path="/invoices" element={<InvoicesList />} />
          <Route path="/payments" element={<PaymentsList />} />
          <Route path="/inventory" element={<InventoryList />} />
          <Route path="/reports" element={<ReportsList />} />
          <Route path="/audit-logs" element={<AuditLogsList />} />
          <Route path="/currencies" element={<Currencies />} />
          <Route path="/cost-centers" element={<CostCenters />} />
          <Route path="/payslips" element={<Payslips />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/fixed-assets" element={<FixedAssets />} />
          <Route path="/depreciation-schedules" element={<DepreciationSchedules />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
