import { Routes, Route } from 'react-router-dom'
import Sidebar from '../components/Layout/Sidebar'
import Header from '../components/Layout/Header'
import Home from './Home'
import ChatPage from './ChatPage'
import InventoryPage from './InventoryPage'
import SalesPage from './SalesPage'
import AnalyticsPage from './AnalyticsPage'
import ApprovalsPage from './ApprovalsPage'
import AlertsPage from './AlertsPage'
import ShareShopPage from './ShareShopPage'

export default function Dashboard() {
  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 ml-[220px] flex flex-col min-h-screen">
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/"             element={<Home />} />
            <Route path="/chat"         element={<ChatPage />} />
            <Route path="/customer-bot" element={<ShareShopPage />} />
            <Route path="/inventory"    element={<InventoryPage />} />
            <Route path="/sales"        element={<SalesPage />} />
            <Route path="/analytics"    element={<AnalyticsPage />} />
            <Route path="/approvals"    element={<ApprovalsPage />} />
            <Route path="/alerts"       element={<AlertsPage />} />
          </Routes>
        </main>
      </div>
    </div>
  )
}
