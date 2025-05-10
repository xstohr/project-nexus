import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Dashboard - Nexus',
  description: 'Overview of your workspaces and tasks',
}

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Dashboard</h1>
        <p className="text-gray-500">Welcome back! Here's an overview of your workspaces and tasks.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="rounded-lg border bg-white p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Workspaces</h2>
          <div className="space-y-4">
            {/* TODO: Add workspace list */}
            <p className="text-gray-500">No workspaces yet</p>
            <Link
              href="/workspaces/new"
              className="text-primary-600 hover:text-primary-700"
            >
              Create a workspace →
            </Link>
          </div>
        </div>

        <div className="rounded-lg border bg-white p-6">
          <h2 className="text-xl font-semibold mb-4">Recent Tasks</h2>
          <div className="space-y-4">
            {/* TODO: Add task list */}
            <p className="text-gray-500">No tasks yet</p>
            <Link
              href="/tasks/new"
              className="text-primary-600 hover:text-primary-700"
            >
              Create a task →
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
} 