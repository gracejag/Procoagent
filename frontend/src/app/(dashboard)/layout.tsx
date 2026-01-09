'use client'

import { ReactNode } from 'react'
import Sidebar from '@/components/sidebar'
import { ProtectedRoute } from '@/components/protected-route'

interface DashboardLayoutProps {
  children: ReactNode
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-slate-50">
        <Sidebar />
        <main className="ml-64">{children}</main>
      </div>
    </ProtectedRoute>
  )
}
