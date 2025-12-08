import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAuth, SignedIn, SignedOut, SignInButton } from '@clerk/clerk-react'
import { Star, Send, CheckCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

const API_URL = import.meta.env.VITE_API_URL

function FeedbackPage() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const { getToken, isSignedIn } = useAuth()
  const [session, setSession] = useState(null)
  const [rating, setRating] = useState(0)
  const [hoveredRating, setHoveredRating] = useState(0)
  const [comment, setComment] = useState('')
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState(null)
  const [existingFeedback, setExistingFeedback] = useState(null)

  useEffect(() => {
    const fetchSession = async () => {
      if (!isSignedIn) {
        setLoading(false)
        return
      }

      try {
        const token = await getToken()
        const response = await fetch(`${API_URL}/api/sessions/${sessionId}`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        })

        if (response.ok) {
          const data = await response.json()
          setSession(data.session)
          
          const feedbackResponse = await fetch(`${API_URL}/api/sessions/${sessionId}/feedback`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            }
          })
          
          if (feedbackResponse.ok) {
            const feedbackData = await feedbackResponse.json()
            if (feedbackData.feedback) {
              setExistingFeedback(feedbackData.feedback)
              setRating(feedbackData.feedback.rating || 0)
              setComment(feedbackData.feedback.comment || '')
            }
          }
        } else {
          setError('Session not found')
        }
      } catch (err) {
        console.error('Error fetching session:', err)
        setError('Failed to load session')
      }
      setLoading(false)
    }

    fetchSession()
  }, [sessionId, getToken, isSignedIn])

  const handleSubmit = async () => {
    if (rating === 0) {
      setError('Please select a rating')
      return
    }

    setSubmitting(true)
    setError(null)

    try {
      const token = await getToken()
      const response = await fetch(`${API_URL}/api/feedback`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          session_id: parseInt(sessionId),
          rating,
          comment
        })
      })

      if (response.ok) {
        setSubmitted(true)
      } else {
        const data = await response.json()
        setError(data.error || 'Failed to submit feedback')
      }
    } catch (err) {
      console.error('Error submitting feedback:', err)
      setError('Failed to submit feedback')
    }
    setSubmitting(false)
  }

  const formatDate = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      weekday: 'long',
      year: 'numeric', 
      month: 'long', 
      day: 'numeric'
    })
  }

  const formatTime = (dateString) => {
    const date = new Date(dateString)
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true 
    })
  }

  const renderSingleStar = (starIndex, displayRating) => {
    const fillPercentage = Math.min(Math.max(displayRating - (starIndex - 1), 0), 1) * 100
    return (
      <div className="relative w-10 h-10">
        <Star className="w-10 h-10 text-gray-300 absolute inset-0" />
        <div className="absolute inset-0 overflow-hidden" style={{ width: `${fillPercentage}%` }}>
          <Star className="w-10 h-10 fill-yellow-400 text-yellow-400" />
        </div>
        <div 
          className="absolute inset-y-0 left-0 w-1/2 cursor-pointer z-10"
          onMouseEnter={() => setHoveredRating(starIndex - 0.5)}
          onClick={() => setRating(starIndex - 0.5)}
        />
        <div 
          className="absolute inset-y-0 right-0 w-1/2 cursor-pointer z-10"
          onMouseEnter={() => setHoveredRating(starIndex)}
          onClick={() => setRating(starIndex)}
        />
      </div>
    )
  }

  if (submitted) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <Card className="max-w-md w-full p-8 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-foreground mb-2">Thank You!</h1>
          <p className="text-muted-foreground mb-6">Your feedback has been submitted successfully.</p>
          <Button onClick={() => navigate('/')}>
            Return to Dashboard
          </Button>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-lg w-full p-8">
        <SignedOut>
          <div className="text-center">
            <h1 className="text-2xl font-bold text-foreground mb-4">Session Feedback</h1>
            <p className="text-muted-foreground mb-6">Please sign in to leave feedback for your tutoring session.</p>
            <SignInButton mode="modal">
              <Button size="lg">Sign In to Continue</Button>
            </SignInButton>
          </div>
        </SignedOut>

        <SignedIn>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="text-muted-foreground mt-4">Loading session...</p>
            </div>
          ) : error && !session ? (
            <div className="text-center py-8">
              <p className="text-destructive mb-4">{error}</p>
              <Button variant="outline" onClick={() => navigate('/')}>
                Return to Dashboard
              </Button>
            </div>
          ) : session ? (
            <>
              <h1 className="text-2xl font-bold text-foreground mb-2">How was your session?</h1>
              <p className="text-muted-foreground mb-6">We'd love to hear your feedback!</p>

              <div className="bg-muted/50 rounded-lg p-4 mb-6">
                <p className="text-sm text-muted-foreground">Session Details</p>
                <p className="font-medium text-foreground">{session.course || 'Chinese Tutoring'}</p>
                <p className="text-sm text-muted-foreground">
                  {formatDate(session.start_time)} at {formatTime(session.start_time)}
                </p>
              </div>

              {existingFeedback && (
                <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4 mb-6">
                  <p className="text-sm text-yellow-800 dark:text-yellow-200">
                    You've already submitted feedback for this session. You can update it below.
                  </p>
                </div>
              )}

              <div className="mb-6">
                <label className="block text-sm font-medium text-foreground mb-3">Rating</label>
                <div 
                  className="flex gap-2 justify-center"
                  onMouseLeave={() => setHoveredRating(0)}
                >
                  {[1, 2, 3, 4, 5].map((star) => {
                    const displayRating = hoveredRating || rating
                    return (
                      <div key={star} className="transition-transform hover:scale-110">
                        {renderSingleStar(star, displayRating)}
                      </div>
                    )
                  })}
                </div>
                <p className="text-center text-sm text-muted-foreground mt-2">
                  {rating === 0 ? 'Select a rating' : `${rating} star${rating !== 1 ? 's' : ''}`}
                </p>
              </div>

              <div className="mb-6">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Comments (optional)
                </label>
                <textarea
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  placeholder="Share your experience..."
                  rows={4}
                  className="w-full px-3 py-2 border border-input rounded-md bg-background text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              {error && (
                <p className="text-destructive text-sm mb-4">{error}</p>
              )}

              <Button
                onClick={handleSubmit}
                disabled={submitting || rating === 0}
                className="w-full"
                size="lg"
              >
                {submitting ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Submitting...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    {existingFeedback ? 'Update Feedback' : 'Submit Feedback'}
                  </>
                )}
              </Button>
            </>
          ) : null}
        </SignedIn>
      </Card>
    </div>
  )
}

export default FeedbackPage

