import { Metadata } from 'next'
import Link from 'next/link'
import { DashboardNav } from '@/components/dashboard/nav'

export const metadata: Metadata = {
  title: 'Dashboard - Nexus',
  description: 'Manage your workspaces and tasks',
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen">
      <DashboardNav />
      <main className="flex-1 p-8">
        {children}
      </main>
    </div>
  )
} 