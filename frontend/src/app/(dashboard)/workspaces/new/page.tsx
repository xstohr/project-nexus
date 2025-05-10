import { Metadata } from 'next'
import { NewWorkspaceForm } from '@/components/workspaces/new-workspace-form'

export const metadata: Metadata = {
  title: 'New Workspace - Nexus',
  description: 'Create a new workspace',
}

export default function NewWorkspacePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">New Workspace</h1>
        <p className="text-gray-500">Create a new workspace for your team</p>
      </div>

      <div className="max-w-2xl">
        <NewWorkspaceForm />
      </div>
    </div>
  )
} 