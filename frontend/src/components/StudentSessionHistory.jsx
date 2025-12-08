import { useState, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Search, Eye, Clock, Monitor, MapPin, Calendar, Star, Send } from 'lucide-react'
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
  const [feedbackMap, setFeedbackMap] = useState({})
  const [isRatingModalOpen, setIsRatingModalOpen] = useState(false)
  const [ratingSession, setRatingSession] = useState(null)
  const [pendingRating, setPendingRating] = useState(0)
  const [ratingComment, setRatingComment] = useState('')
  const [submittingRating, setSubmittingRating] = useState(false)
  const [hoveredRating, setHoveredRating] = useState({})
  const [modalHoveredRating, setModalHoveredRating] = useState(0)

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

          const feedbacks = {}
          for (const session of pastSessions) {
            if (session.feedback) {
              feedbacks[session.id] = session.feedback
            }
          }
          setFeedbackMap(feedbacks)
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

  const handleStarClick = (session, rating) => {
    setRatingSession(session)
    setPendingRating(rating)
    const existingFeedback = feedbackMap[session.id]
    setRatingComment(existingFeedback?.comment || '')
    setIsRatingModalOpen(true)
  }

  const handleSubmitRating = async () => {
    if (!ratingSession || pendingRating === 0) return

    setSubmittingRating(true)
    try {
      const response = await api.submitFeedback(getToken, {
        session_id: ratingSession.id,
        rating: pendingRating,
        comment: ratingComment
      })

      if (response.ok) {
        const data = await response.json()
        setFeedbackMap(prev => ({
          ...prev,
          [ratingSession.id]: data.feedback
        }))
        setIsRatingModalOpen(false)
        setRatingSession(null)
        setPendingRating(0)
        setRatingComment('')
        setModalHoveredRating(0)
      }
    } catch (error) {
      console.error('Error submitting rating:', error)
    }
    setSubmittingRating(false)
  }

  const renderTableStar = (starIndex, displayRating, session) => {
    const fillPercentage = Math.min(Math.max(displayRating - (starIndex - 1), 0), 1) * 100
    return (
      <div className="relative w-5 h-5">
        <Star className="w-5 h-5 text-gray-300 absolute inset-0" />
        <div className="absolute inset-0 overflow-hidden" style={{ width: `${fillPercentage}%` }}>
          <Star className="w-5 h-5 fill-yellow-400 text-yellow-400" />
        </div>
        <div 
          className="absolute inset-y-0 left-0 w-1/2 cursor-pointer z-10"
          onMouseEnter={() => setHoveredRating(prev => ({ ...prev, [session.id]: starIndex - 0.5 }))}
          onClick={() => handleStarClick(session, starIndex - 0.5)}
        />
        <div 
          className="absolute inset-y-0 right-0 w-1/2 cursor-pointer z-10"
          onMouseEnter={() => setHoveredRating(prev => ({ ...prev, [session.id]: starIndex }))}
          onClick={() => handleStarClick(session, starIndex)}
        />
      </div>
    )
  }

  const renderModalStar = (starIndex, displayRating) => {
    const fillPercentage = Math.min(Math.max(displayRating - (starIndex - 1), 0), 1) * 100
    return (
      <div className="relative w-10 h-10">
        <Star className="w-10 h-10 text-gray-300 absolute inset-0" />
        <div className="absolute inset-0 overflow-hidden" style={{ width: `${fillPercentage}%` }}>
          <Star className="w-10 h-10 fill-yellow-400 text-yellow-400" />
        </div>
        <div 
          className="absolute inset-y-0 left-0 w-1/2 cursor-pointer z-10"
          onMouseEnter={() => setModalHoveredRating(starIndex - 0.5)}
          onClick={() => setPendingRating(starIndex - 0.5)}
        />
        <div 
          className="absolute inset-y-0 right-0 w-1/2 cursor-pointer z-10"
          onMouseEnter={() => setModalHoveredRating(starIndex)}
          onClick={() => setPendingRating(starIndex)}
        />
      </div>
    )
  }

  const renderStars = (session) => {
    const existingRating = feedbackMap[session.id]?.rating || 0
    const displayRating = hoveredRating[session.id] ?? existingRating
    return (
      <div 
        className="flex gap-0.5"
        onMouseLeave={() => setHoveredRating(prev => ({ ...prev, [session.id]: null }))}
      >
        {[1, 2, 3, 4, 5].map((star) => (
          <div key={star} className="transition-transform hover:scale-110">
            {renderTableStar(star, displayRating, session)}
          </div>
        ))}
      </div>
    )
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
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Rating</th>
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
                      {renderStars(session)}
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
                  <td colSpan={6} className="py-8 text-center text-sm text-muted-foreground">
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

      <Dialog open={isRatingModalOpen} onOpenChange={(open) => {
        setIsRatingModalOpen(open)
        if (!open) {
          setRatingSession(null)
          setPendingRating(0)
          setRatingComment('')
          setModalHoveredRating(0)
        }
      }}>
        <DialogContent className="sm:max-w-[400px]">
          <DialogHeader>
            <DialogTitle>Rate Your Session</DialogTitle>
            <DialogDescription>
              {ratingSession 
                ? `Session on ${formatDate(ratingSession.start_time)} - ${ratingSession.course || 'Chinese Tutoring'}`
                : 'Leave your rating'}
            </DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div 
              className="flex justify-center gap-2"
              onMouseLeave={() => setModalHoveredRating(0)}
            >
              {[1, 2, 3, 4, 5].map((star) => {
                const displayRating = modalHoveredRating || pendingRating
                return (
                  <div key={star} className="transition-transform hover:scale-110">
                    {renderModalStar(star, displayRating)}
                  </div>
                )
              })}
            </div>
            <p className="text-center text-sm text-muted-foreground">
              {pendingRating === 0 ? 'Select a rating' : `${pendingRating} star${pendingRating !== 1 ? 's' : ''}`}
            </p>
            <div className="grid gap-2">
              <label className="text-sm font-medium text-foreground">
                Comments (optional)
              </label>
              <textarea
                value={ratingComment}
                onChange={(e) => setRatingComment(e.target.value)}
                placeholder="Share your experience..."
                rows={3}
                className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsRatingModalOpen(false)
                setRatingSession(null)
                setPendingRating(0)
                setRatingComment('')
                setModalHoveredRating(0)
              }}
            >
              Cancel
            </Button>
            <Button
              onClick={handleSubmitRating}
              disabled={submittingRating || pendingRating === 0}
            >
              {submittingRating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Submitting...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  {feedbackMap[ratingSession?.id] ? 'Update Rating' : 'Submit Rating'}
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default StudentSessionHistory

