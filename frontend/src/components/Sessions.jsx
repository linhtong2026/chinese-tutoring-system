import { useState, useMemo } from 'react'
import { Calendar, ChevronLeft, ChevronRight, Monitor, MapPin, Plus, CalendarIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'

function Sessions() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [formData, setFormData] = useState({
    date: '',
    dateNative: '', // For native date picker
    startTime: '',
    endTime: '',
    recurring: false
  })

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

  // Mock availability data (recurring and individual)
  const monthlyAvailability = useMemo(() => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    
    // Recurring availability (day of week, time range)
    const recurring = [
      { dayOfWeek: 1, dayName: 'Monday', startTime: '8:00 PM', endTime: '9:00 PM', type: 'online' },
      { dayOfWeek: 3, dayName: 'Wednesday', startTime: '8:20 PM', endTime: '9:20 PM', type: 'in-person' },
      { dayOfWeek: 5, dayName: 'Friday', startTime: '9:00 PM', endTime: '10:00 PM', type: 'online' },
    ]

    // Individual availability (specific dates)
    const individual = [
      { date: 5, startTime: '8:40 PM', endTime: '9:40 PM', type: 'online' },
      { date: 12, startTime: '8:00 PM', endTime: '9:00 PM', type: 'in-person' },
      { date: 20, startTime: '9:20 PM', endTime: '10:00 PM', type: 'online' },
    ]

    // Generate all availability entries for the month
    const entries = []

    // Add recurring entries (show only once, not for each occurrence)
    recurring.forEach(rec => {
      entries.push({
        date: null, // No specific date for recurring
        dateObj: null,
        startTime: rec.startTime,
        endTime: rec.endTime,
        type: rec.type,
        isRecurring: true,
        dayName: rec.dayName
      })
    })

    // Add individual entries
    individual.forEach(ind => {
      const date = new Date(year, month, ind.date)
      entries.push({
        date: ind.date,
        dateObj: date,
        startTime: ind.startTime,
        endTime: ind.endTime,
        type: ind.type,
        isRecurring: false,
        dayName: date.toLocaleDateString('en-US', { weekday: 'long' })
      })
    })

    // Sort: recurring first (by day name), then individual (by date, then by start time)
    entries.sort((a, b) => {
      if (a.isRecurring && !b.isRecurring) return -1
      if (!a.isRecurring && b.isRecurring) return 1
      if (a.isRecurring && b.isRecurring) {
        // Sort recurring by day name
        const daysOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        return daysOrder.indexOf(a.dayName) - daysOrder.indexOf(b.dayName)
      }
      // Individual entries: sort by date, then by start time
      if (a.date !== b.date) return a.date - b.date
      return a.startTime.localeCompare(b.startTime)
    })

    return entries
  }, [currentDate])

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

  // Generate time options
  const generateTimeOptions = (startHour, startMin, endHour, endMin, interval) => {
    const options = []
    let hour = startHour
    let min = startMin
    
    while (hour < endHour || (hour === endHour && min <= endMin)) {
      const time24 = `${hour.toString().padStart(2, '0')}:${min.toString().padStart(2, '0')}`
      const date = new Date(`2000-01-01T${time24}:00`)
      const time12 = date.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
      options.push({ value: time24, label: time12 })
      
      min += interval
      if (min >= 60) {
        min = 0
        hour++
      }
    }
    
    return options
  }

  const startTimeOptions = generateTimeOptions(20, 0, 21, 40, 20) // 8:00 PM to 9:40 PM
  const endTimeOptions = generateTimeOptions(20, 20, 22, 0, 20) // 8:20 PM to 10:00 PM

  const handleSubmit = (e) => {
    e.preventDefault()
    // TODO: Submit to API
    console.log('Form data:', formData)
    setIsModalOpen(false)
    // Reset form
    setFormData({
      date: '',
      dateNative: '',
      startTime: '',
      endTime: '',
      recurring: false
    })
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
        <Button onClick={() => setIsModalOpen(true)}>
          <Plus className="w-4 h-4 mr-2" />
          Add Availability
        </Button>
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

      {/* Monthly Availability Table */}
      <Card className="mt-8 p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          This Month Availability
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Date</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Day</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Time</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Type</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {monthlyAvailability.length > 0 ? (
                monthlyAvailability.map((entry, index) => (
                  <tr key={index} className="border-b border-border hover:bg-muted/50">
                    <td className="py-3 px-4 text-sm text-foreground">
                      {entry.isRecurring ? '—' : entry.date}
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground">
                      {entry.isRecurring ? `Every ${entry.dayName}` : entry.dayName}
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground">
                      {entry.startTime} - {entry.endTime}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center gap-2">
                        {entry.type === 'online' ? (
                          <Monitor className="w-4 h-4 text-muted-foreground" />
                        ) : (
                          <MapPin className="w-4 h-4 text-muted-foreground" />
                        )}
                        <span className="text-sm text-foreground capitalize">
                          {entry.type === 'online' ? 'Online' : 'In-Person'}
                        </span>
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      <span className={cn(
                        "text-xs px-2 py-1 rounded",
                        entry.isRecurring 
                          ? "bg-blue-100 text-blue-800" 
                          : "bg-purple-100 text-purple-800"
                      )}>
                        {entry.isRecurring ? 'Recurring' : 'Individual'}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-sm text-muted-foreground">
                    No availability set for this month
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Add Availability Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[425px]">
          <DialogHeader>
            <DialogTitle>Add Availability</DialogTitle>
            <DialogDescription>
              Set your available hours for tutoring sessions
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit}>
            <div className="grid gap-4 py-4">
              {/* Date Input */}
              <div className="grid gap-2">
                <Label htmlFor="date">Select Date</Label>
                <div className="relative">
                  <Input
                    id="date"
                    type="text"
                    placeholder="dd/mm/yyyy"
                    value={formData.date}
                    onChange={(e) => {
                      const input = e.target.value
                      // Allow deleting "/" by handling backspace differently
                      // Remove all non-digits, then reformat
                      let digits = input.replace(/\D/g, '')
                      let formatted = ''
                      if (digits.length > 0) {
                        formatted = digits.slice(0, 2)
                        if (digits.length > 2) {
                          formatted += '/' + digits.slice(2, 4)
                          if (digits.length > 4) {
                            formatted += '/' + digits.slice(4, 8)
                          }
                        }
                      }
                      setFormData({ ...formData, date: formatted })
                    }}
                    maxLength={10}
                    className="pr-10"
                  />
                  {/* Hidden native date input for calendar picker */}
                  <input
                    type="date"
                    id="date-native"
                    className="absolute opacity-0 pointer-events-none w-0 h-0"
                    value={formData.dateNative}
                    onChange={(e) => {
                      const nativeDate = e.target.value
                      if (nativeDate) {
                        const date = new Date(nativeDate)
                        const day = date.getDate().toString().padStart(2, '0')
                        const month = (date.getMonth() + 1).toString().padStart(2, '0')
                        const year = date.getFullYear()
                        setFormData({ 
                          ...formData, 
                          date: `${day}/${month}/${year}`,
                          dateNative: nativeDate
                        })
                      } else {
                        setFormData({ ...formData, date: '', dateNative: '' })
                      }
                    }}
                  />
                  <CalendarIcon 
                    className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground cursor-pointer" 
                    onClick={() => {
                      const nativeInput = document.getElementById('date-native')
                      if (nativeInput) {
                        // Convert dd/mm/yyyy to YYYY-MM-DD for native input
                        if (formData.date) {
                          const [day, month, year] = formData.date.split('/')
                          if (day && month && year) {
                            nativeInput.value = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
                          }
                        }
                        nativeInput.showPicker?.() || nativeInput.click()
                      }
                    }}
                  />
                </div>
              </div>

              {/* Time Selection */}
              <div className="grid grid-cols-2 gap-4">
                <div className="grid gap-2">
                  <Label htmlFor="start-time">Start</Label>
                  <Select
                    value={formData.startTime}
                    onValueChange={(value) => setFormData({ ...formData, startTime: value })}
                  >
                    <SelectTrigger id="start-time">
                      <SelectValue placeholder="Select time" />
                    </SelectTrigger>
                    <SelectContent>
                      {startTimeOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="end-time">End</Label>
                  <Select
                    value={formData.endTime}
                    onValueChange={(value) => setFormData({ ...formData, endTime: value })}
                  >
                    <SelectTrigger id="end-time">
                      <SelectValue placeholder="Select time" />
                    </SelectTrigger>
                    <SelectContent>
                      {endTimeOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Recurring Toggle */}
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="recurring">Recurring Weekly</Label>
                  <p className="text-sm text-muted-foreground">
                    Repeat this availability every week
                  </p>
                </div>
                <Switch
                  id="recurring"
                  checked={formData.recurring}
                  onCheckedChange={(checked) => setFormData({ ...formData, recurring: checked })}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsModalOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit">
                Save Availability
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export default Sessions

