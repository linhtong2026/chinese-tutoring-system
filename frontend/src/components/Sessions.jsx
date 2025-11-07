import { useState, useMemo } from 'react'
import { Calendar, ChevronLeft, ChevronRight, Monitor, MapPin } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { cn } from '@/lib/utils'

function Sessions() {
  const [currentDate, setCurrentDate] = useState(new Date())

  // Get the start of the week (Sunday)
  const getWeekStart = (date) => {
    const d = new Date(date)
    const day = d.getDay()
    const diff = d.getDate() - day
    return new Date(d.setDate(diff))
  }

  // Get all days of the current week
  const getWeekDays = () => {
    const start = getWeekStart(currentDate)
    const days = []
    for (let i = 0; i < 7; i++) {
      const day = new Date(start)
      day.setDate(start.getDate() + i)
      days.push(day)
    }
    return days
  }

  // Format date as YYYY-MM-DD for comparison
  const formatDateKey = (date) => {
    return date.toISOString().split('T')[0]
  }

  const weekDays = getWeekDays()

  // Mock sessions data
  const mockSessions = useMemo(() => {
    const sessions = {}
    
    // Add some mock sessions for different days
    // Monday - Available online session
    if (weekDays[1]) {
      const mondayKey = formatDateKey(weekDays[1])
      sessions[mondayKey] = [
        { id: 1, time: '10:00 AM', status: 'available', type: 'online' },
        { id: 2, time: '2:00 PM', status: 'booked', type: 'online' },
      ]
    }
    
    // Wednesday - Available in-person and booked online
    if (weekDays[3]) {
      const wednesdayKey = formatDateKey(weekDays[3])
      sessions[wednesdayKey] = [
        { id: 3, time: '11:00 AM', status: 'available', type: 'in-person' },
        { id: 4, time: '3:00 PM', status: 'booked', type: 'online' },
      ]
    }
    
    // Friday - Multiple sessions
    if (weekDays[5]) {
      const fridayKey = formatDateKey(weekDays[5])
      sessions[fridayKey] = [
        { id: 5, time: '9:00 AM', status: 'available', type: 'in-person' },
        { id: 6, time: '1:00 PM', status: 'booked', type: 'in-person' },
        { id: 7, time: '4:00 PM', status: 'available', type: 'online' },
      ]
    }
    
    return sessions
  }, [weekDays])

  const monthYear = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  const navigateWeek = (direction) => {
    const newDate = new Date(currentDate)
    newDate.setDate(newDate.getDate() + (direction * 7))
    setCurrentDate(newDate)
  }

  const formatDayName = (date) => {
    return date.toLocaleDateString('en-US', { weekday: 'short' })
  }

  const formatDayNumber = (date) => {
    return date.getDate()
  }

  const getSessionsForDay = (date) => {
    const dateKey = formatDateKey(date)
    return mockSessions[dateKey] || []
  }

  return (
    <div className="p-8">
      {/* Header Section */}
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Sessions
          </h1>
          <p className="text-muted-foreground">
            Manage your tutoring schedule and time slots
          </p>
        </div>
      </div>

      {/* Calendar Navigation */}
      <div className="mb-6 flex items-center gap-4">
        <Calendar className="w-5 h-5 text-foreground" />
        <span className="text-lg font-medium text-foreground">
          {monthYear}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigateWeek(-1)}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => navigateWeek(1)}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Weekly Calendar Grid */}
      <Card className="p-6">
        <div className="grid grid-cols-7 gap-4">
          {weekDays.map((day, index) => {
            const daySessions = getSessionsForDay(day)
            return (
              <div
                key={index}
                className="flex flex-col p-3 border border-border rounded-lg bg-card min-h-[180px]"
              >
                <div className="text-xs font-medium text-muted-foreground mb-1 text-center">
                  {formatDayName(day)}
                </div>
                <div className="text-lg font-bold text-foreground mb-3 text-center">
                  {formatDayNumber(day)}
                </div>
                <div className="flex-1 space-y-1.5">
                  {daySessions.length > 0 ? (
                    daySessions.map((session) => (
                      <div
                        key={session.id}
                        className={cn(
                          "p-1.5 rounded text-[10px] flex items-center gap-1.5",
                          session.status === 'available'
                            ? "bg-green-100 text-green-800 border border-green-200"
                            : "bg-blue-100 text-blue-800 border border-blue-200"
                        )}
                      >
                        {session.type === 'online' ? (
                          <Monitor className="w-2.5 h-2.5 flex-shrink-0" />
                        ) : (
                          <MapPin className="w-2.5 h-2.5 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate text-[10px]">{session.time}</div>
                          <div className="text-[9px] opacity-75">
                            {session.status === 'available' ? 'Available' : 'Booked'}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-muted-foreground text-center py-3">
                      No sessions
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Legend */}
        <div className="mt-6 flex gap-6">
          <div className="flex items-center gap-2">
            <Monitor className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Online</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">In-Person</span>
          </div>
        </div>
      </Card>
    </div>
  )
}

export default Sessions

