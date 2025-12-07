import { useState, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Search, Edit, Clock, Monitor, MapPin, Calendar } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import api from '@/services/api'

function SessionHistory({ userData }) {
  const { getToken } = useAuth()
  const [sessions, setSessions] = useState([])
  const [filteredSessions, setFilteredSessions] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [selectedStudent, setSelectedStudent] = useState(null)
  const [isLogModalOpen, setIsLogModalOpen] = useState(false)
  const [selectedSession, setSelectedSession] = useState(null)
  const [sessionNote, setSessionNote] = useState({ attendance_status: '', notes: '', student_feedback: '' })
  const [existingNote, setExistingNote] = useState(null)

  useEffect(() => {
    const fetchSessions = async () => {
      if (!userData?.id) return

      try {
        const response = await api.getSessions(getToken, userData.id)
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

    if (userData?.role === 'tutor') {
      fetchSessions()
      const intervalId = setInterval(fetchSessions, 30000)
      return () => clearInterval(intervalId)
    }
  }, [userData?.id, userData?.role, getToken])

  useEffect(() => {
    let filtered = sessions

    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase()
      filtered = filtered.filter(session => 
        session.course?.toLowerCase().includes(term) ||
        session.student_name?.toLowerCase().includes(term)
      )
    }

    if (selectedCourse && selectedCourse !== 'all') {
      filtered = filtered.filter(session => session.course === selectedCourse)
    }

    if (selectedStudent && selectedStudent !== 'all') {
      filtered = filtered.filter(session => session.student_name === selectedStudent)
    }

    setFilteredSessions(filtered)
  }, [searchTerm, selectedCourse, selectedStudent, sessions])

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

  const handleLogSession = async (session) => {
    setSelectedSession(session)
    
    try {
      const noteResponse = await api.getSessionNote(getToken, session.id)
      if (noteResponse.ok) {
        const noteData = await noteResponse.json()
        if (noteData.note) {
          setExistingNote(noteData.note)
          setSessionNote({
            attendance_status: noteData.note.attendance_status || '',
            notes: noteData.note.notes || '',
            student_feedback: noteData.note.student_feedback || ''
          })
        } else {
          setExistingNote(null)
          setSessionNote({ attendance_status: '', notes: '', student_feedback: '' })
        }
      } else {
        setExistingNote(null)
        setSessionNote({ attendance_status: '', notes: '', student_feedback: '' })
      }
    } catch (error) {
      console.error('Error fetching session note:', error)
      setExistingNote(null)
      setSessionNote({ attendance_status: '', notes: '', student_feedback: '' })
    }
    
    setIsLogModalOpen(true)
  }


  const handleSaveLog = async () => {
    if (!selectedSession) return

    try {
      const logData = {
        session_id: selectedSession.id,
        attendance_status: sessionNote.attendance_status,
        notes: sessionNote.notes,
        student_feedback: sessionNote.student_feedback
      }

      let response
      if (existingNote) {
        response = await api.updateSessionNote(getToken, existingNote.id, logData)
      } else {
        response = await api.createSessionNote(getToken, logData)
      }

      if (response.ok) {
        setIsLogModalOpen(false)
        setSelectedSession(null)
        setSessionNote({ attendance_status: '', notes: '', student_feedback: '' })
        setExistingNote(null)
      } else {
        const errorData = await response.json()
        alert(`Error: ${errorData.error || 'Failed to save session log'}`)
      }
    } catch (error) {
      console.error('Error saving session log:', error)
      alert(`Error: ${error.message}`)
    }
  }

  if (userData?.role !== 'tutor') {
    return (
      <div className="p-8">
        <p className="text-muted-foreground">This page is only available for tutors.</p>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Tutoring Sessions
          </h1>
          <p className="text-muted-foreground">
            Track and log your tutoring sessions
          </p>
        </div>
      </div>

      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            type="text"
            placeholder="Search sessions by course or student..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-3">
          <Select value={selectedCourse || 'all'} onValueChange={(val) => setSelectedCourse(val === 'all' ? null : val)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by course" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Courses</SelectItem>
              {Array.from(new Set(sessions.map(s => s.course).filter(Boolean))).sort().map(course => (
                <SelectItem key={course} value={course}>{course}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Select value={selectedStudent || 'all'} onValueChange={(val) => setSelectedStudent(val === 'all' ? null : val)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Filter by student" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Students</SelectItem>
              {Array.from(new Set(sessions.map(s => s.student_name).filter(Boolean))).sort().map(student => (
                <SelectItem key={student} value={student}>{student}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Card className="p-6">
        <div className="mb-4">
          <h2 className="text-xl font-semibold text-foreground mb-2">
            All Sessions
          </h2>
          <p className="text-sm text-muted-foreground">
            Centralized session records and notes
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-2 text-sm font-medium text-foreground w-32">Date</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Course</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Student Name</th>
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
                    <td className="py-3 px-4 text-sm text-foreground">
                      {session.student_name || 'Unknown'}
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
                        onClick={() => handleLogSession(session)}
                      >
                        <Edit className="w-4 h-4 mr-1" />
                        Notes
                      </Button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
                    {searchTerm ? 'No sessions found matching your search' : 'No past sessions yet'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Dialog open={isLogModalOpen} onOpenChange={(open) => {
        setIsLogModalOpen(open)
        if (!open) {
          setSelectedSession(null)
          setSessionNote({ attendance_status: '', notes: '', student_feedback: '' })
          setExistingNote(null)
        }
      }}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Session Log</DialogTitle>
            <DialogDescription>
              {selectedSession 
                ? `Session on ${formatDate(selectedSession.start_time)} at ${formatTime(selectedSession.start_time)}`
                : 'Add notes for a tutoring session'}
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
                    <span className="text-muted-foreground">Student: </span>
                    <span className="text-foreground font-medium">{selectedSession.student_name || 'Unknown'}</span>
                  </div>
                </div>
              </div>
            )}
            
            <div className="grid gap-2">
              <Label htmlFor="attendance">Attendance Status</Label>
              <Select
                value={sessionNote.attendance_status}
                onValueChange={(value) => setSessionNote({ ...sessionNote, attendance_status: value })}
              >
                <SelectTrigger id="attendance">
                  <SelectValue placeholder="Select attendance status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="present">Present</SelectItem>
                  <SelectItem value="absent">Absent</SelectItem>
                  <SelectItem value="late">Late</SelectItem>
                  <SelectItem value="excused">Excused</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="notes">
                Session Notes <span className="text-xs text-muted-foreground">(Not visible to students)</span>
              </Label>
              <textarea
                id="notes"
                value={sessionNote.notes}
                onChange={(e) => setSessionNote({ ...sessionNote, notes: e.target.value })}
                placeholder="Add notes about this session..."
                className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="student_feedback">
                Student Feedback <span className="text-xs text-muted-foreground">(Visible to students)</span>
              </Label>
              <textarea
                id="student_feedback"
                value={sessionNote.student_feedback}
                onChange={(e) => setSessionNote({ ...sessionNote, student_feedback: e.target.value })}
                placeholder="Add feedback for the student..."
                className="min-h-[100px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsLogModalOpen(false)
                setSelectedSession(null)
                setSessionNote({ attendance_status: '', notes: '', student_feedback: '' })
                setExistingNote(null)
              }}
            >
              Cancel
            </Button>
            <Button onClick={handleSaveLog}>
              Save Log
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default SessionHistory

