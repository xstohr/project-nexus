import { Metadata } from 'next'
import Link from 'next/link'
import { Button } from '@/components/ui/button'

export const metadata: Metadata = {
  title: 'Workspaces - Nexus',
  description: 'Manage your workspaces',
}

export default function WorkspacesPage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Workspaces</h1>
          <p className="text-gray-500">Create and manage your workspaces</p>
        </div>
        <Link href="/workspaces/new">
          <Button>Create Workspace</Button>
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* TODO: Add workspace cards */}
        <div className="rounded-lg border bg-white p-6">
          <h3 className="text-lg font-semibold mb-2">No Workspaces Yet</h3>
          <p className="text-gray-500 mb-4">
            Create your first workspace to get started
          </p>
          <Link
            href="/workspaces/new"
            className="text-primary-600 hover:text-primary-700"
          >
            Create a workspace →
          </Link>
        </div>
      </div>
    </div>
  )
} 