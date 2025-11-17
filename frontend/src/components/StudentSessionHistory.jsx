import { useState, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Search, Eye, Clock, Monitor, MapPin, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import api from '@/services/api'

function StudentSessionHistory({ userData }) {
  const { getToken } = useAuth()
  const [sessions, setSessions] = useState([])
  const [filteredSessions, setFilteredSessions] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false)
  const [selectedSession, setSelectedSession] = useState(null)
  const [sessionNote, setSessionNote] = useState(null)

  useEffect(() => {
    const fetchSessions = async () => {
      if (!userData?.id) return

      try {
        const response = await api.getStudentSessions(getToken)
        if (response.ok) {
          const data = await response.json()
          const now = new Date()
          const pastSessions = (data.sessions || []).filter(session => {
            const sessionStart = new Date(session.start_time)
            return sessionStart < now && session.status === 'booked'
          })
          setSessions(pastSessions)
          setFilteredSessions(pastSessions)
        }
      } catch (error) {
        console.error('Error fetching sessions:', error)
      }
    }

    if (userData?.role === 'student') {
      fetchSessions()
      const intervalId = setInterval(fetchSessions, 30000)
      return () => clearInterval(intervalId)
    }
  }, [userData?.id, userData?.role, getToken])

  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredSessions(sessions)
    } else {
      const term = searchTerm.toLowerCase()
      const filtered = sessions.filter(session => 
        session.course?.toLowerCase().includes(term)
      )
      setFilteredSessions(filtered)
    }
  }, [searchTerm, sessions])

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: '2-digit', 
      day: '2-digit' 
    }).replace(/\//g, '-')
  }

  const formatTime = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: false 
    })
  }

  const calculateDuration = (startTime, endTime) => {
    const start = new Date(startTime)
    const end = new Date(endTime)
    const diff = Math.round((end - start) / (1000 * 60))
    return `${diff}m`
  }

  const handleViewFeedback = async (session) => {
    setSelectedSession(session)
    
    try {
      const noteResponse = await api.getSessionNote(getToken, session.id)
      if (noteResponse.ok) {
        const noteData = await noteResponse.json()
        setSessionNote(noteData.note || null)
      } else {
        setSessionNote(null)
      }
    } catch (error) {
      console.error('Error fetching session note:', error)
      setSessionNote(null)
    }
    
    setIsFeedbackModalOpen(true)
  }

  if (userData?.role !== 'student') {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">This page is only available for students.</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-foreground mb-2">
          My Session History
        </h1>
        <p className="text-muted-foreground">
          View your past tutoring sessions and feedback
        </p>
      </div>

      <div className="mb-6 relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder="Search sessions by course..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10"
        />
      </div>

      <Card className="p-6">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-foreground mb-2">
            All Sessions
          </h2>
          <p className="text-sm text-muted-foreground">
            Your completed tutoring sessions
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-2 text-sm font-medium text-foreground w-32">Date</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Course</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Duration</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Type</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredSessions.length > 0 ? (
                filteredSessions.map((session) => (
                  <tr key={session.id} className="border-b border-border hover:bg-muted/50">
                    <td className="py-3 px-2">
                      <div className="flex items-start gap-1.5">
                        <Calendar className="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                        <div className="flex flex-col text-sm">
                          <span className="font-medium text-foreground">{formatDate(session.start_time)}</span>
                          <span className="text-muted-foreground">{formatTime(session.start_time)}</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground">
                      {session.course || '-'}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-1 text-sm text-foreground">
                        <Clock className="w-3 h-3 text-muted-foreground" />
                        {calculateDuration(session.start_time, session.end_time)}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {session.session_type === 'online' ? (
                          <>
                            <Monitor className="w-4 h-4 text-muted-foreground" />
                            <span className="text-sm text-foreground">Online</span>
                          </>
                        ) : (
                          <>
                            <MapPin className="w-4 h-4 text-muted-foreground" />
                            <span className="text-sm text-foreground">In-Person</span>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleViewFeedback(session)}
                      >
                        <Eye className="w-4 h-4 mr-1" />
                        View Feedback
                      </Button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-sm text-muted-foreground">
                    {searchTerm ? 'No sessions found matching your search' : 'No past sessions yet'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={isFeedbackModalOpen} onOpenChange={(open) => {
        setIsFeedbackModalOpen(open)
        if (!open) {
          setSelectedSession(null)
          setSessionNote(null)
        }
      }}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Session Feedback</DialogTitle>
            <DialogDescription>
              {selectedSession 
                ? `Session on ${formatDate(selectedSession.start_time)} at ${formatTime(selectedSession.start_time)}`
                : 'Session details'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            {selectedSession && (
              <div className="grid gap-2">
                <div className="flex gap-4 text-sm">
                  <div>
                    <span className="text-muted-foreground">Course: </span>
                    <span className="text-foreground font-medium">{selectedSession.course || '-'}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Duration: </span>
                    <span className="text-foreground font-medium">{calculateDuration(selectedSession.start_time, selectedSession.end_time)}</span>
                  </div>
                </div>
              </div>
            )}

            {sessionNote ? (
              <>
                {sessionNote.attendance_status && (
                  <div className="grid gap-2">
                    <span className="text-sm font-medium text-foreground">Attendance</span>
                    <div className="text-sm text-muted-foreground capitalize">
                      {sessionNote.attendance_status}
                    </div>
                  </div>
                )}

                <div className="grid gap-2">
                  <span className="text-sm font-medium text-foreground">Tutor Feedback</span>
                  {sessionNote.student_feedback ? (
                    <div className="text-sm text-foreground bg-muted p-3 rounded-md">
                      {sessionNote.student_feedback}
                    </div>
                  ) : (
                    <div className="text-sm text-muted-foreground italic">
                      No feedback provided yet
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="text-sm text-muted-foreground text-center py-4">
                No feedback available for this session
              </div>
            )}
          </div>
          <DialogFooter>
            <Button
              type="button"
              onClick={() => {
                setIsFeedbackModalOpen(false)
                setSelectedSession(null)
                setSessionNote(null)
              }}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default StudentSessionHistory

