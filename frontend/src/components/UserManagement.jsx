import { useState, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import api from '@/services/api'

function UserManagement({ userData }) {
  const { getToken } = useAuth()
  const [email, setEmail] = useState('')
  const [role, setRole] = useState('tutor')
  const [invitations, setInvitations] = useState([])
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState(null)
  const [fetchingInvitations, setFetchingInvitations] = useState(true)

  useEffect(() => {
    fetchInvitations()
  }, [])

  const fetchInvitations = async () => {
    try {
      const response = await api.getInvitations(getToken)
      if (response.ok) {
        const data = await response.json()
        setInvitations(data.invitations || [])
      }
    } catch (error) {
      console.error('Error fetching invitations:', error)
    } finally {
      setFetchingInvitations(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setMessage(null)

    try {
      const response = await api.sendInvitation(getToken, email, role)
      const data = await response.json()

      if (response.ok) {
        setMessage({ type: 'success', text: `Invitation sent to ${email}` })
        setEmail('')
        setRole('tutor')
        fetchInvitations()
      } else {
        setMessage({ type: 'error', text: data.error || 'Failed to send invitation' })
      }
    } catch (error) {
      setMessage({ type: 'error', text: 'An error occurred. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadgeClass = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800'
      case 'accepted':
        return 'bg-green-100 text-green-800'
      case 'expired':
        return 'bg-red-100 text-red-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const formatDate = (dateString) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  if (userData?.role !== 'professor') {
    return (
      <div className="p-6">
        <Card className="p-6">
          <p className="text-gray-600">You do not have permission to access this page.</p>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">User Management</h1>
      </div>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Send Invitation</h2>
        
        {message && (
          <div 
            className={`mb-4 p-4 rounded-md ${
              message.type === 'success' 
                ? 'bg-green-50 text-green-800 border border-green-200' 
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}
          >
            {message.text}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="tutor@example.com"
              required
              disabled={loading}
              className="mt-1"
            />
          </div>

          <div>
            <Label htmlFor="role">Role</Label>
            <Select value={role} onValueChange={setRole} disabled={loading}>
              <SelectTrigger className="mt-1">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="tutor">Tutor</SelectItem>
                <SelectItem value="professor">Professor</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" disabled={loading} className="w-full">
            {loading ? 'Sending...' : 'Send Invitation'}
          </Button>
        </form>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-4">Invitation History</h2>
        
        {fetchingInvitations ? (
          <p className="text-gray-500">Loading invitations...</p>
        ) : invitations.length === 0 ? (
          <p className="text-gray-500">No invitations sent yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 font-semibold">Email</th>
                  <th className="text-left py-3 px-4 font-semibold">Role</th>
                  <th className="text-left py-3 px-4 font-semibold">Status</th>
                  <th className="text-left py-3 px-4 font-semibold">Invited By</th>
                  <th className="text-left py-3 px-4 font-semibold">Sent Date</th>
                  <th className="text-left py-3 px-4 font-semibold">Expires</th>
                </tr>
              </thead>
              <tbody>
                {invitations.map((invitation) => (
                  <tr key={invitation.id} className="border-b hover:bg-gray-50">
                    <td className="py-3 px-4">{invitation.email}</td>
                    <td className="py-3 px-4 capitalize">{invitation.role}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusBadgeClass(invitation.status)}`}>
                        {invitation.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">{invitation.invited_by_name || 'Unknown'}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{formatDate(invitation.created_at)}</td>
                    <td className="py-3 px-4 text-sm text-gray-600">{formatDate(invitation.expires_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  )
}

export default UserManagement
