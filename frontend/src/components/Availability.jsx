import { useState, useMemo, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Calendar, ChevronLeft, ChevronRight, Monitor, MapPin, User, Clock, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import api from '@/services/api'

const formatDateKey = (date) => {
  const nycDate = new Date(date.toLocaleString('en-US', { timeZone: 'America/New_York' }))
  const year = nycDate.getFullYear()
  const month = String(nycDate.getMonth() + 1).padStart(2, '0')
  const day = String(nycDate.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function Availability({ userData }) {
  const { getToken } = useAuth()
  const [currentDate, setCurrentDate] = useState(new Date())
  const [viewMode, setViewMode] = useState('month')
  const [tutors, setTutors] = useState([])
  const [selectedTutor, setSelectedTutor] = useState(null)
  const [availabilities, setAvailabilities] = useState([])
  const [sessions, setSessions] = useState([])
  const [selectedSession, setSelectedSession] = useState(null)
  const [isBookingDialogOpen, setIsBookingDialogOpen] = useState(false)

  useEffect(() => {
    const fetchTutors = async () => {
      try {
        const response = await api.getAllTutors(getToken)
        if (response.ok) {
          const data = await response.json()
          setTutors(data.tutors || [])
          if (data.tutors && data.tutors.length > 0) {
            setSelectedTutor(data.tutors[0])
          }
        }
      } catch (error) {
        console.error('Error fetching tutors:', error)
      }
    }

    fetchTutors()
  }, [getToken])

  useEffect(() => {
    const fetchTutorData = async () => {
      if (!selectedTutor) return

      try {
        const [availabilityResponse, sessionsResponse] = await Promise.all([
          api.getAvailability(getToken, selectedTutor.id),
          api.getSessions(getToken, selectedTutor.user_id)
        ])

        if (availabilityResponse.ok) {
          const data = await availabilityResponse.json()
          setAvailabilities(data.availabilities || [])
        }

        if (sessionsResponse.ok) {
          const data = await sessionsResponse.json()
          setSessions(data.sessions || [])
        }
      } catch (error) {
        console.error('Error fetching tutor data:', error)
      }
    }

    fetchTutorData()
  }, [selectedTutor, getToken])

  const monthYear = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  const navigateMonth = (direction) => {
    const newDate = new Date(currentDate)
    newDate.setMonth(newDate.getMonth() + direction)
    setCurrentDate(newDate)
  }

  const getMonthDays = () => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const daysInMonth = lastDay.getDate()
    const startDayOfWeek = firstDay.getDay()

    const days = []
    for (let i = 0; i < startDayOfWeek; i++) {
      days.push(null)
    }
    for (let i = 1; i <= daysInMonth; i++) {
      days.push(new Date(year, month, i))
    }
    return days
  }

  const monthDays = getMonthDays()

  const getTimeSlotsForDay = (date) => {
    if (!date) return []
    
    const dateKey = formatDateKey(date)
    const dayOfWeek = date.getDay()
    const slots = []

    availabilities.forEach(av => {
      if (!av.start_time || !av.end_time) return

      const parseNYCTime = (isoString) => {
        const match = isoString.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):\d{2}/)
        if (match) {
          const [, year, month, day, hours, minutes] = match.map(Number)
          const nycDate = new Date(year, month - 1, day, hours, minutes)
          return { hours, minutes, date: nycDate, year, month, day }
        }
        const dt = new Date(isoString)
        const year = dt.getUTCFullYear()
        const month = dt.getUTCMonth() + 1
        const day = dt.getUTCDate()
        const hours = dt.getUTCHours()
        const minutes = dt.getUTCMinutes()
        const nycDate = new Date(year, month - 1, day, hours, minutes)
        return { hours, minutes, date: nycDate, year, month, day }
      }

      const startNYC = parseNYCTime(av.start_time)
      const endNYC = parseNYCTime(av.end_time)

      let appliesToThisDay = false

      if (av.is_recurring) {
        if (av.day_of_week === dayOfWeek) {
          appliesToThisDay = true
        }
      } else {
        const avDateKey = `${startNYC.year}-${String(startNYC.month).padStart(2, '0')}-${String(startNYC.day).padStart(2, '0')}`
        if (avDateKey === dateKey) {
          appliesToThisDay = true
        }
      }

      if (appliesToThisDay) {
        const startMinutes = startNYC.hours * 60 + startNYC.minutes
        const endMinutes = endNYC.hours * 60 + endNYC.minutes
        const numSlots = Math.floor((endMinutes - startMinutes) / 20)

        for (let i = 0; i < numSlots; i++) {
          const slotMinutes = startMinutes + (i * 20)
          const slotHour24 = Math.floor(slotMinutes / 60) % 24
          const slotMin = slotMinutes % 60

          const slotHour12 = slotHour24 === 0 ? 12 : (slotHour24 > 12 ? slotHour24 - 12 : slotHour24)
          const ampm = slotHour24 >= 12 ? 'PM' : 'AM'
          const slotTime = `${slotHour12}:${String(slotMin).padStart(2, '0')} ${ampm}`

          const sessionInSlot = sessions.find(s => {
            if (!s.start_time) return false

            const sessionTimeMatch = s.start_time.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):\d{2}/)
            if (!sessionTimeMatch) return false

            const [, sYear, sMonth, sDay, sHour, sMin] = sessionTimeMatch.map(Number)
            const sessionDateKey = `${sYear}-${String(sMonth).padStart(2, '0')}-${String(sDay).padStart(2, '0')}`

            if (sessionDateKey !== dateKey) return false

            const slotStartMinutes = startMinutes + (i * 20)
            const slotEndMinutes = slotStartMinutes + 20
            const sessionStartMinutes = sHour * 60 + sMin

            return sessionStartMinutes >= slotStartMinutes && sessionStartMinutes < slotEndMinutes
          })

          slots.push({
            id: `slot-${av.id}-${slotMinutes}`,
            time: slotTime,
            timeSort: slotMinutes,
            type: av.session_type,
            isAvailable: !sessionInSlot || sessionInSlot.status === 'available',
            isBooked: sessionInSlot && sessionInSlot.status === 'booked',
            session: sessionInSlot
          })
        }
      }
    })

    slots.sort((a, b) => a.timeSort - b.timeSort)

    const slotMap = new Map()
    for (const slot of slots) {
      const key = slot.timeSort.toString()
      if (!slotMap.has(key)) {
        slotMap.set(key, slot)
      } else {
        const existing = slotMap.get(key)
        if (slot.isBooked && !existing.isBooked) {
          slotMap.set(key, slot)
        }
      }
    }

    return Array.from(slotMap.values())
  }

  const handleSlotClick = (slot, date) => {
    if (!slot.isAvailable || slot.isBooked) return
    
    setSelectedSession({
      ...slot,
      date: date,
      tutorName: selectedTutor?.user?.name || 'Unknown',
      tutorEmail: selectedTutor?.user?.email || ''
    })
    setIsBookingDialogOpen(true)
  }

  const handleBookSession = async () => {
    if (!selectedSession || !selectedSession.session) return

    try {
      const response = await api.bookSession(getToken, selectedSession.session.id)
      if (response.ok) {
        const updatedSessions = sessions.map(s => 
          s.id === selectedSession.session.id ? { ...s, status: 'booked', student_id: userData.id } : s
        )
        setSessions(updatedSessions)
        setIsBookingDialogOpen(false)
        setSelectedSession(null)
      } else {
        const error = await response.json()
        alert(`Error booking session: ${error.error || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Error booking session:', error)
      alert('Failed to book session')
    }
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Availability
          </h1>
          <p className="text-muted-foreground">
            View tutor availability and book sessions
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant={viewMode === 'month' ? 'default' : 'outline'}
            onClick={() => setViewMode('month')}
          >
            Month View
          </Button>
          <Button
            variant={viewMode === 'week' ? 'default' : 'outline'}
            onClick={() => setViewMode('week')}
          >
            Week View
          </Button>
        </div>
      </div>

      <Card className="p-6 mb-6">
        <div>
          <h2 className="text-lg font-semibold text-foreground mb-2">Select Tutor</h2>
          <p className="text-sm text-muted-foreground mb-4">Choose a tutor to view their availability</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {tutors.map((tutor) => {
            const tutorClasses = 'CN126, CN127'
            
            return (
              <div
                key={tutor.id}
                onClick={() => setSelectedTutor(tutor)}
                className={cn(
                  "p-4 border rounded-lg cursor-pointer transition-all",
                  selectedTutor?.id === tutor.id
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                )}
              >
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                    <User className="w-5 h-5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-foreground">{tutor.user?.name || 'Unknown'}</h3>
                    <p className="text-xs text-muted-foreground mb-2">{tutorClasses}</p>
                    <div className="flex gap-3 items-center">
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Monitor className="w-3 h-3" />
                      </div>
                      <div className="flex items-center gap-1 text-xs text-muted-foreground">
                        <MapPin className="w-3 h-3" />
                      </div>
                    </div>
                  </div>
                </div>
                {selectedTutor?.id === tutor.id && (
                  <div className="mt-3 text-xs font-medium text-primary">
                    Selected
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      <div className="mb-6 flex items-center gap-4">
        <Calendar className="w-5 h-5 text-foreground" />
        <span className="text-lg font-medium text-foreground">
          {monthYear}
        </span>
        <span className="text-sm text-muted-foreground">
          - {selectedTutor?.user?.name || 'Select a tutor'}
        </span>
        <div className="flex gap-2 ml-auto">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigateMonth(-1)}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigateMonth(1)}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <Card className="p-6">
        <div className="grid grid-cols-7 gap-2 mb-4">
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((day) => (
            <div key={day} className="text-xs font-medium text-muted-foreground text-center py-2">
              {day}
            </div>
          ))}
        </div>
        <div className="grid grid-cols-7 gap-2">
          {monthDays.map((day, index) => {
            const timeSlots = day ? getTimeSlotsForDay(day) : []
            const now = new Date()
            const isToday = day && formatDateKey(day) === formatDateKey(new Date())
            const today = new Date()
            today.setHours(0, 0, 0, 0)
            const dayDate = day ? new Date(day) : null
            if (dayDate) dayDate.setHours(0, 0, 0, 0)
            const isPastDate = dayDate && dayDate < today
            const isTodayDate = dayDate && dayDate.getTime() === today.getTime()
            
            return (
              <div
                key={index}
                className={cn(
                  "min-h-[120px] p-2 border rounded-lg",
                  !day ? "bg-muted/30" : isPastDate ? "bg-muted/50" : "bg-card",
                  isToday && "border-primary"
                )}
              >
                {day && (
                  <>
                    <div className={cn(
                      "text-sm font-medium mb-2 text-center",
                      isToday ? "text-primary" : isPastDate ? "text-foreground/30" : "text-foreground"
                    )}>
                      {day.getDate()}
                    </div>
                    <div className="space-y-1">
                      {timeSlots.length > 0 ? (
                        timeSlots.slice(0, 3).map((slot) => {
                          const slotDateTime = new Date(day)
                          const timeMatch = slot.time.match(/(\d+):(\d+)\s*(AM|PM)/)
                          if (timeMatch) {
                            let hours = parseInt(timeMatch[1])
                            const minutes = parseInt(timeMatch[2])
                            const period = timeMatch[3]
                            if (period === 'PM' && hours !== 12) hours += 12
                            if (period === 'AM' && hours === 12) hours = 0
                            slotDateTime.setHours(hours, minutes, 0, 0)
                          }
                          const isPastSlot = isPastDate || (isTodayDate && slotDateTime < now)
                          
                          return (
                            <div
                              key={slot.id}
                              onClick={() => !isPastSlot && handleSlotClick(slot, day)}
                              className={cn(
                                "p-1 rounded text-[9px] flex items-center gap-1",
                                isPastSlot
                                  ? "bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed opacity-50"
                                  : slot.isBooked
                                  ? "bg-green-100 text-green-800 border border-green-200 cursor-not-allowed"
                                  : slot.isAvailable
                                  ? "bg-blue-100 text-blue-800 border border-blue-200 hover:bg-blue-200 cursor-pointer"
                                  : "bg-gray-100 text-gray-500 border border-gray-200 cursor-not-allowed"
                              )}
                            >
                              {slot.type === 'online' ? (
                                <Monitor className="w-2 h-2 flex-shrink-0" />
                              ) : (
                                <MapPin className="w-2 h-2 flex-shrink-0" />
                              )}
                              <span className="truncate">{slot.time}</span>
                            </div>
                          )
                        })
                      ) : (
                        <div className="text-[9px] text-muted-foreground text-center py-2">
                          No slots
                        </div>
                      )}
                      {timeSlots.length > 3 && (
                        <div className="text-[8px] text-muted-foreground text-center">
                          +{timeSlots.length - 3} more
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            )
          })}
        </div>

        <div className="mt-6 flex gap-6">
          <div className="flex items-center gap-2">
            <Monitor className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Online</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">In-Person</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-blue-100 border border-blue-200 rounded"></div>
            <span className="text-sm text-muted-foreground">Available</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-100 border border-green-200 rounded"></div>
            <span className="text-sm text-muted-foreground">Booked</span>
          </div>
        </div>
      </Card>

      <Dialog open={isBookingDialogOpen} onOpenChange={setIsBookingDialogOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Book Session</DialogTitle>
            <DialogDescription>
              Review the session details and confirm your booking
            </DialogDescription>
          </DialogHeader>
          
          {selectedSession && (
            <div className="space-y-4 py-4">
              <div className="flex items-start gap-3 p-4 bg-muted rounded-lg">
                <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                  <User className="w-5 h-5 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground">{selectedSession.tutorName}</h3>
                  <p className="text-sm text-muted-foreground">{selectedSession.tutorEmail}</p>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-3 p-3 border rounded-lg">
                  <Calendar className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Date</p>
                    <p className="text-sm text-muted-foreground">
                      {selectedSession.date?.toLocaleDateString('en-US', { 
                        weekday: 'long', 
                        year: 'numeric', 
                        month: 'long', 
                        day: 'numeric' 
                      })}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 border rounded-lg">
                  <Clock className="w-5 h-5 text-muted-foreground" />
                  <div>
                    <p className="text-sm font-medium text-foreground">Time</p>
                    <p className="text-sm text-muted-foreground">{selectedSession.time}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3 p-3 border rounded-lg">
                  {selectedSession.type === 'online' ? (
                    <Monitor className="w-5 h-5 text-muted-foreground" />
                  ) : (
                    <MapPin className="w-5 h-5 text-muted-foreground" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-foreground">Session Type</p>
                    <p className="text-sm text-muted-foreground capitalize">
                      {selectedSession.type === 'online' ? 'Online' : 'In-Person'}
                    </p>
                  </div>
                </div>
              </div>

              <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                <p className="text-sm text-blue-800">
                  This session is 20 minutes long. You will receive a confirmation email after booking.
                </p>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                setIsBookingDialogOpen(false)
                setSelectedSession(null)
              }}
            >
              Cancel
            </Button>
            <Button type="button" onClick={handleBookSession}>
              Confirm Booking
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Availability

