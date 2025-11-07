import { useState, useMemo, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Calendar, ChevronLeft, ChevronRight, Monitor, MapPin, Plus, CalendarIcon } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'
import api from '@/services/api'

function Sessions({ userData }) {
  const { getToken } = useAuth()
  const [currentDate, setCurrentDate] = useState(new Date())
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [sessions, setSessions] = useState([])
  const [availabilities, setAvailabilities] = useState([])
  const [tutorId, setTutorId] = useState(null)
  const [formData, setFormData] = useState({
    date: '',
    dateNative: '', // For native date picker
    startTime: '',
    endTime: '',
    sessionType: 'online',
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

  useEffect(() => {
    const fetchTutorAndData = async () => {
      if (!userData?.id) return
      
      try {
        const tutorResponse = await api.getTutorByUser(getToken, userData.id)
        if (tutorResponse.ok) {
          const tutorData = await tutorResponse.json()
          const tutor = tutorData.tutor
          setTutorId(tutor.id)
          
          const [sessionsResponse, availabilityResponse] = await Promise.all([
            api.getSessions(getToken, userData.id),
            api.getAvailability(getToken, tutor.id)
          ])
          
          if (sessionsResponse.ok) {
            const sessionsData = await sessionsResponse.json()
            setSessions(sessionsData.sessions || [])
          }
          
          if (availabilityResponse.ok) {
            const availabilityData = await availabilityResponse.json()
            setAvailabilities(availabilityData.availabilities || [])
          }
        } else {
          const errorData = await tutorResponse.json()
          console.error('Error fetching tutor:', errorData)
        }
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }

    fetchTutorAndData()
  }, [userData?.id, getToken])

  const monthYear = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })

  const monthlyAvailability = useMemo(() => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const entries = []
    const daysOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    availabilities.forEach(av => {
      if (!av.start_time || !av.end_time) return
      
      const startTime = new Date(av.start_time)
      const endTime = new Date(av.end_time)
      
      const startTime12 = startTime.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
      const endTime12 = endTime.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      })
      
      if (av.is_recurring) {
        const dayName = daysOrder[av.day_of_week]
        const startDate = new Date(startTime)
        entries.push({
          id: av.id,
          date: startDate.getDate(),
          dateObj: startDate,
          startTime: startTime12,
          endTime: endTime12,
          type: av.session_type || null,
          isRecurring: true,
          dayName: dayName,
          dayOfWeek: av.day_of_week
        })
      } else {
        const dateObj = new Date(startTime)
        if (dateObj.getFullYear() === year && dateObj.getMonth() === month) {
          entries.push({
            id: av.id,
            date: dateObj.getDate(),
            dateObj: dateObj,
            startTime: startTime12,
            endTime: endTime12,
            type: av.session_type || null,
            isRecurring: false,
            dayName: dateObj.toLocaleDateString('en-US', { weekday: 'long' })
          })
        }
      }
    })
    
    entries.sort((a, b) => {
      if (a.isRecurring && !b.isRecurring) return -1
      if (!a.isRecurring && b.isRecurring) return 1
      if (a.isRecurring && b.isRecurring) {
        return a.dayOfWeek - b.dayOfWeek
      }
      if (a.date !== b.date) return a.date - b.date
      return a.startTime.localeCompare(b.startTime)
    })
    
    return entries
  }, [availabilities, currentDate])

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

  const generateTimeSlots = (startTime, endTime, intervalMinutes = 20) => {
    const slots = []
    const start = new Date(startTime)
    const end = new Date(endTime)
    
    let current = new Date(start)
    
    while (current < end) {
      const slotEnd = new Date(current.getTime() + intervalMinutes * 60000)
      if (slotEnd > end) break
      
      slots.push({
        start: new Date(current),
        end: new Date(slotEnd)
      })
      
      current = slotEnd
    }
    
    return slots
  }

  const getTimeSlotsForDay = (date) => {
    const dateKey = formatDateKey(date)
    const dayOfWeek = date.getDay()
    const slots = []
    
    availabilities.forEach(av => {
      if (!av.start_time || !av.end_time) return
      
      const avStartTime = new Date(av.start_time)
      const avEndTime = new Date(av.end_time)
      
      let appliesToThisDay = false
      
      if (av.is_recurring) {
        if (av.day_of_week === dayOfWeek) {
          appliesToThisDay = true
        }
      } else {
        const avDate = new Date(avStartTime)
        if (formatDateKey(avDate) === dateKey) {
          appliesToThisDay = true
        }
      }
      
      if (appliesToThisDay) {
        const baseDate = new Date(date)
        baseDate.setHours(avStartTime.getHours(), avStartTime.getMinutes(), 0, 0)
        
        const endDate = new Date(date)
        endDate.setHours(avEndTime.getHours(), avEndTime.getMinutes(), 0, 0)
        
        const timeSlots = generateTimeSlots(baseDate, endDate, 20)
        
        timeSlots.forEach(slot => {
          const slotTime = slot.start.toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true
          })
          
          const sessionInSlot = sessions.find(s => {
            if (!s.start_time || !s.end_time) return false
            const sessionStart = new Date(s.start_time)
            const slotDateKey = formatDateKey(sessionStart)
            
            return slotDateKey === dateKey &&
                   sessionStart >= slot.start &&
                   sessionStart < slot.end
          })
          
          slots.push({
            id: `slot-${av.id}-${slot.start.getTime()}`,
            time: slotTime,
            timeSort: slot.start.getTime(),
            type: av.session_type,
            isAvailable: !sessionInSlot,
            session: sessionInSlot ? {
              id: sessionInSlot.id,
              status: sessionInSlot.status === 'available' ? 'available' : 'booked',
              type: sessionInSlot.session_type
            } : null
          })
        })
      }
    })
    
    slots.sort((a, b) => a.timeSort - b.timeSort)
    
    return slots
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

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!tutorId || !formData.startTime || !formData.endTime || !formData.date || !formData.sessionType) {
      return
    }
    
    try {
      const [day, month, year] = formData.date.split('/')
      const dateObj = new Date(year, month - 1, day)
      const dayOfWeek = dateObj.getDay()
      
      const [startHour, startMin] = formData.startTime.split(':').map(Number)
      const [endHour, endMin] = formData.endTime.split(':').map(Number)
      
      const startDateTime = new Date(dateObj)
      startDateTime.setHours(startHour, startMin, 0, 0)
      
      const endDateTime = new Date(dateObj)
      endDateTime.setHours(endHour, endMin, 0, 0)
      
      const availabilityData = {
        tutor_id: tutorId,
        day_of_week: dayOfWeek,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        session_type: formData.sessionType,
        is_recurring: formData.recurring
      }
      
      const response = await api.createAvailability(getToken, availabilityData)
      
      if (response.ok) {
        const data = await response.json()
        setAvailabilities([...availabilities, data.availability])
        setIsModalOpen(false)
        setFormData({
          date: '',
          dateNative: '',
          startTime: '',
          endTime: '',
          sessionType: 'online',
          recurring: false
        })
      } else {
        const errorData = await response.json()
        console.error('Error creating availability:', errorData)
      }
    } catch (error) {
      console.error('Error creating availability:', error)
    }
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
            const timeSlots = getTimeSlotsForDay(day)
            return (
              <div
                key={index}
                className="flex flex-col p-3 border border-border rounded-lg bg-card min-h-[500px]"
              >
                <div className="text-xs font-medium text-muted-foreground mb-1 text-center">
                  {formatDayName(day)}
                </div>
                <div className="text-lg font-bold text-foreground mb-3 text-center">
                  {formatDayNumber(day)}
                </div>
                <div className="flex-1 space-y-2 overflow-y-auto max-h-[500px]">
                  {timeSlots.length > 0 ? (
                    timeSlots.map((slot) => (
                      <div
                        key={slot.id}
                        className={cn(
                          "p-1.5 rounded text-[10px] flex items-center gap-1.5",
                          slot.session
                            ? "bg-green-100 text-green-800 border border-green-200"
                            : "bg-blue-100 text-blue-800 border border-blue-200"
                        )}
                      >
                        {slot.type === 'online' ? (
                          <Monitor className="w-2.5 h-2.5 flex-shrink-0" />
                        ) : (
                          <MapPin className="w-2.5 h-2.5 flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                          <div className="font-medium truncate text-[10px]">{slot.time}</div>
                          <div className="text-[9px] opacity-75">
                            {slot.session ? 'Booked' : 'Available'}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="text-xs text-muted-foreground text-center py-3">
                      No availability
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

      {/* Monthly Availability Table */}
      <Card className="mt-8 p-6">
        <h2 className="text-xl font-semibold text-foreground mb-4">
          This Month Availability
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Start Date</th>
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
                      {entry.date}
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground">
                      {entry.isRecurring ? `Every ${entry.dayName}` : entry.dayName}
                    </td>
                    <td className="py-3 px-4 text-sm text-foreground">
                      {entry.startTime} - {entry.endTime}
                    </td>
                    <td className="py-3 px-4">
                      {entry.type ? (
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
                      ) : (
                        <span className="text-sm text-muted-foreground">—</span>
                      )}
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

              {/* Session Type Selection */}
              <div className="grid gap-2">
                <Label htmlFor="session-type">Session Type</Label>
                <Select
                  value={formData.sessionType}
                  onValueChange={(value) => setFormData({ ...formData, sessionType: value })}
                >
                  <SelectTrigger id="session-type">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="online">Online</SelectItem>
                    <SelectItem value="in-person">In-Person</SelectItem>
                  </SelectContent>
                </Select>
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

