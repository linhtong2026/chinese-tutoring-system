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

const formatDateKey = (date) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}


function Sessions({ userData }) {
  const { getToken } = useAuth()
  const [currentDate, setCurrentDate] = useState(new Date())
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [sessions, setSessions] = useState([])
  const [availabilities, setAvailabilities] = useState([])
  const [tutorId, setTutorId] = useState(null)
  const [formData, setFormData] = useState({
    date: '',
    dateNative: '',
    startTime: '',
    endTime: '',
    sessionType: 'online',
    recurring: false
  })
  const [tutors, setTutors] = useState([])
  const [selectedTutor, setSelectedTutor] = useState(null)
  const [isBookingModalOpen, setIsBookingModalOpen] = useState(false)
  const [selectedSlot, setSelectedSlot] = useState(null)
  const [viewMode, setViewMode] = useState('month')
  const [selectedSession, setSelectedSession] = useState(null)
  const [isNoteModalOpen, setIsNoteModalOpen] = useState(false)
  const [isDaySlotsModalOpen, setIsDaySlotsModalOpen] = useState(false)
  const [daySlotsModalData, setDaySlotsModalData] = useState({ date: null, slots: [] })

  const getWeekStart = (date) => {
    const d = new Date(date)
    d.setHours(0, 0, 0, 0)
    return d
  }

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

  const weekDays = getWeekDays()

  useEffect(() => {
    const fetchData = async () => {
      if (!userData?.id) return
      
      try {
        if (userData.role === 'professor') {
          const response = await api.getProfessorSessions(getToken)
          if (response.ok) {
            const data = await response.json()
            setSessions(data.sessions || [])
          }
        } else if (userData.role === 'tutor') {
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
        } else if (userData.role === 'student') {
          const [tutorsResponse, sessionsResponse] = await Promise.all([
            api.getTutors(getToken),
            api.getStudentSessions(getToken)
          ])
          
          if (tutorsResponse.ok) {
            const tutorsData = await tutorsResponse.json()
            const fetchedTutors = tutorsData.tutors || []
            setTutors(fetchedTutors)
            if (fetchedTutors.length > 0) {
              setSelectedTutor((prevSelected) => {
                if (prevSelected) {
                  const stillExists = fetchedTutors.find((tutor) => tutor.id === prevSelected.id)
                  if (stillExists) {
                    return stillExists
                  }
                }
                return fetchedTutors[0]
              })
            } else {
              setSelectedTutor(null)
            }
          }
          
          if (sessionsResponse.ok) {
            const sessionsData = await sessionsResponse.json()
            setSessions(sessionsData.sessions || [])
          }
        }
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }

    fetchData()
    
    const intervalId = setInterval(() => {
      fetchData()
    }, 10000)
    
    return () => clearInterval(intervalId)
  }, [userData?.id, userData?.role, getToken])
  
  useEffect(() => {
    const fetchTutorAvailability = async () => {
      if (userData?.role === 'student' && selectedTutor?.id) {
        try {
          const [availabilityResponse, tutorSessionsResponse] = await Promise.all([
            api.getAvailability(getToken, selectedTutor.id),
            api.getSessions(getToken, selectedTutor.user_id)
          ])
          
          if (availabilityResponse.ok) {
            const availabilityData = await availabilityResponse.json()
            setAvailabilities(availabilityData.availabilities || [])
          }
          
          if (tutorSessionsResponse.ok) {
            const tutorSessionsData = await tutorSessionsResponse.json()
            setSessions(prevSessions => {
              const allSessions = [...prevSessions]
              const tutorSessions = tutorSessionsData.sessions || []
              
              tutorSessions.forEach(ts => {
                if (!allSessions.find(s => s.id === ts.id)) {
                  allSessions.push(ts)
                }
              })
              
              return allSessions
            })
          }
        } catch (error) {
          console.error('Error fetching tutor availability:', error)
        }
      }
    }
    
    fetchTutorAvailability()
    
    const intervalId = setInterval(() => {
      fetchTutorAvailability()
    }, 10000)
    
    return () => clearInterval(intervalId)
  }, [selectedTutor?.id, selectedTutor?.user_id, userData?.role, getToken])

  const monthYear = currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
  const daySlotsModalDateLabel = daySlotsModalData.date
    ? daySlotsModalData.date.toLocaleDateString('en-US', {
        weekday: 'long',
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      })
    : ''

  const monthlyAvailability = useMemo(() => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const entries = []
    const daysOrder = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    availabilities.forEach(av => {
      if (!av.start_time || !av.end_time) return
      
      // Parse times from ISO string - backend sends UTC time (which we treat as NYC time)
      const parseNYCTime = (isoString) => {
        // Backend sends UTC time like "2024-01-15T20:00:00+00:00" or "2024-01-15T20:00:00Z"
        // Extract time components directly from the string (treating UTC as NYC time)
        const match = isoString.match(/T(\d{2}):(\d{2}):\d{2}/)
        if (match) {
          const hour24 = parseInt(match[1], 10)
          const minute = parseInt(match[2], 10)
          const hour12 = hour24 === 0 ? 12 : (hour24 > 12 ? hour24 - 12 : hour24)
          const ampm = hour24 >= 12 ? 'PM' : 'AM'
          return `${hour12}:${String(minute).padStart(2, '0')} ${ampm}`
        }
        // Fallback
        const dt = new Date(isoString)
        const hour24 = dt.getUTCHours()
        const minute = dt.getUTCMinutes()
        const hour12 = hour24 === 0 ? 12 : (hour24 > 12 ? hour24 - 12 : hour24)
        const ampm = hour24 >= 12 ? 'PM' : 'AM'
        return `${hour12}:${String(minute).padStart(2, '0')} ${ampm}`
      }
      
      const startTime12 = parseNYCTime(av.start_time)
      const endTime12 = parseNYCTime(av.end_time)
      
      // Get date from UTC time (treating UTC as NYC)
      const startTime = new Date(av.start_time)
      const startDateMatch = av.start_time.match(/(\d{4})-(\d{2})-(\d{2})T/)
      const startYear = startDateMatch ? parseInt(startDateMatch[1], 10) : startTime.getUTCFullYear()
      const startMonth = startDateMatch ? parseInt(startDateMatch[2], 10) - 1 : startTime.getUTCMonth()
      const startDay = startDateMatch ? parseInt(startDateMatch[3], 10) : startTime.getUTCDate()
      
      if (av.is_recurring) {
        const dayName = daysOrder[av.day_of_week]
        // For recurring, use the date from start_time (treating UTC as NYC)
        const dateInNYC = new Date(startYear, startMonth, startDay)
        entries.push({
          id: av.id,
          date: dateInNYC.getDate(),
          dateObj: dateInNYC,
          startTime: startTime12,
          endTime: endTime12,
          type: av.session_type || null,
          isRecurring: true,
          dayName: dayName,
          dayOfWeek: av.day_of_week
        })
      } else {
        // For non-recurring, check if it's in the current month (treating UTC as NYC)
        const dateInNYC = new Date(startYear, startMonth, startDay)
        if (dateInNYC.getFullYear() === year && dateInNYC.getMonth() === month) {
          entries.push({
            id: av.id,
            date: dateInNYC.getDate(),
            dateObj: dateInNYC,
            startTime: startTime12,
            endTime: endTime12,
            type: av.session_type || null,
            isRecurring: false,
            dayName: dateInNYC.toLocaleDateString('en-US', { weekday: 'long' })
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
    
    const sessionMap = new Map()
    sessions.forEach(session => {
      if (!session.start_time) return
      const sessionTimeMatch = session.start_time.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):\d{2}/)
      if (!sessionTimeMatch) return
      const [, sYear, sMonth, sDay, sHour, sMin] = sessionTimeMatch.map(Number)
      const sessionDateKey = `${sYear}-${String(sMonth).padStart(2, '0')}-${String(sDay).padStart(2, '0')}`
      if (sessionDateKey === dateKey) {
        const sessionMinutes = sHour * 60 + sMin
        const sessionKey = `${sessionDateKey}-${sessionMinutes}`
        if (!sessionMap.has(sessionKey) || session.status === 'booked') {
          sessionMap.set(sessionKey, session)
        }
      }
    })
    
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
        const baseDate = new Date(date)
        baseDate.setHours(startNYC.hours, startNYC.minutes, 0, 0)
        
        const endDate = new Date(date)
        endDate.setHours(endNYC.hours, endNYC.minutes, 0, 0)
        
        const timeSlots = generateTimeSlots(baseDate, endDate, 20)
        
        timeSlots.forEach((slot, slotIndex) => {
          const slotMinutes = startNYC.hours * 60 + startNYC.minutes + (slotIndex * 20)
          const slotHour24 = Math.floor(slotMinutes / 60) % 24
          const slotMin = slotMinutes % 60
          
          const slotHour12 = slotHour24 === 0 ? 12 : (slotHour24 > 12 ? slotHour24 - 12 : slotHour24)
          const ampm = slotHour24 >= 12 ? 'PM' : 'AM'
          const slotTime = `${slotHour12}:${String(slotMin).padStart(2, '0')} ${ampm}`
          
          const slotStartMinutes = startNYC.hours * 60 + startNYC.minutes + (slotIndex * 20)
          const slotEndMinutes = slotStartMinutes + 20
          
          let sessionInSlot = null
          for (const session of sessionMap.values()) {
            const sessionTimeMatch = session.start_time.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):\d{2}/)
            if (!sessionTimeMatch) continue
            const [, , , , sHour, sMin] = sessionTimeMatch.map(Number)
            const sessionStartMinutes = sHour * 60 + sMin
            if (sessionStartMinutes >= slotStartMinutes && sessionStartMinutes < slotEndMinutes) {
              sessionInSlot = session
              break
            }
          }
          
          slots.push({
            id: `slot-${av.id}-${slot.start.getTime()}`,
            time: slotTime,
            timeSort: slot.start.getTime(),
            type: av.session_type,
            isAvailable: !sessionInSlot,
            availability: av,
            slotIndex: slotIndex,
            session: sessionInSlot ? {
              id: sessionInSlot.id,
              status: sessionInSlot.status === 'booked' ? 'booked' : 'available',
              type: sessionInSlot.session_type,
              student_id: sessionInSlot.student_id
            } : null
          })
        })
      }
    })
    
    sessionMap.forEach(session => {
      const sessionTimeMatch = session.start_time.match(/(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):\d{2}/)
      if (!sessionTimeMatch) return
      const [, sYear, sMonth, sDay, sHour, sMin] = sessionTimeMatch.map(Number)
      const sessionDateKey = `${sYear}-${String(sMonth).padStart(2, '0')}-${String(sDay).padStart(2, '0')}`
      if (sessionDateKey !== dateKey) return
      
      const alreadyInSlots = slots.some(slot => 
        slot.session && slot.session.id === session.id
      )
      
      if (!alreadyInSlots) {
        const slotHour12 = sHour === 0 ? 12 : (sHour > 12 ? sHour - 12 : sHour)
        const ampm = sHour >= 12 ? 'PM' : 'AM'
        const slotTime = `${slotHour12}:${String(sMin).padStart(2, '0')} ${ampm}`
        
        const baseDate = new Date(date)
        baseDate.setHours(sHour, sMin, 0, 0)
        
        slots.push({
          id: `slot-session-${session.id}`,
          time: slotTime,
          timeSort: baseDate.getTime(),
          type: session.session_type,
          isAvailable: false,
          availability: null,
          slotIndex: 0,
          session: {
            id: session.id,
            status: session.status,
            type: session.session_type,
            student_id: session.student_id
          }
        })
      }
    })
    
    slots.sort((a, b) => a.timeSort - b.timeSort)
    
    const slotMap = new Map()
    
    for (const slot of slots) {
      const slotKey = slot.timeSort.toString()
      
      if (slotMap.has(slotKey)) {
        const existingSlot = slotMap.get(slotKey)
        
        if (slot.session && !existingSlot.session) {
          existingSlot.session = slot.session
          existingSlot.isAvailable = false
        } else if (slot.session && existingSlot.session) {
          if (slot.session.id !== existingSlot.session.id) {
            if (slot.session.status === 'booked' && existingSlot.session.status !== 'booked') {
              existingSlot.session = slot.session
              existingSlot.isAvailable = false
            }
          }
        }
      } else {
        slotMap.set(slotKey, slot)
      }
    }
    
    return Array.from(slotMap.values())
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
    
    console.log('Form submitted:', formData)
    console.log('Tutor ID:', tutorId)
    
    if (!tutorId) {
      console.error('Missing tutorId')
      alert('Tutor ID is missing. Please refresh the page.')
      return
    }
    
    if (!formData.startTime || !formData.endTime || !formData.date || !formData.sessionType) {
      console.error('Missing form data:', { 
        startTime: formData.startTime, 
        endTime: formData.endTime, 
        date: formData.date, 
        sessionType: formData.sessionType 
      })
      alert('Please fill in all required fields.')
      return
    }
    
    try {
      const [month, day, year] = formData.date.split('/')
      if (!month || !day || !year || month.length !== 2 || day.length !== 2 || year.length !== 4) {
        alert('Please enter a valid date in mm/dd/yyyy format.')
        return
      }
      
      const selectedDate = new Date(year, month - 1, day)
      const today = new Date()
      today.setHours(0, 0, 0, 0)
      
      if (selectedDate < today) {
        alert('Cannot select a date in the past.')
        return
      }
      
      const [startHour, startMin] = formData.startTime.split(':').map(Number)
      const [endHour, endMin] = formData.endTime.split(':').map(Number)
      
      const dateStr = `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`
      
      const startTimeStr = `${dateStr}T${String(startHour).padStart(2, '0')}:${String(startMin).padStart(2, '0')}:00`
      const endTimeStr = `${dateStr}T${String(endHour).padStart(2, '0')}:${String(endMin).padStart(2, '0')}:00`
      
      const dateObj = new Date(year, month - 1, day)
      const dayOfWeek = dateObj.getDay()
      
      const availabilityData = {
        tutor_id: tutorId,
        day_of_week: dayOfWeek,
        start_time: startTimeStr,
        end_time: endTimeStr,
        session_type: formData.sessionType,
        is_recurring: formData.recurring
      }
      
      console.log('Calling API with data:', availabilityData)
      const response = await api.createAvailability(getToken, availabilityData)
      console.log('API Response status:', response.status)
      
      if (response.ok) {
        const data = await response.json()
        console.log('Availability created:', data)
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
        alert(`Error: ${errorData.error || 'Failed to create availability'}`)
      }
    } catch (error) {
      console.error('Error creating availability:', error)
      alert(`Error: ${error.message}`)
    }
  }
  
  const handleBookSession = async (slot, date) => {
    if (!slot.isAvailable || slot.session) return
    
    setSelectedSlot({ ...slot, date })
    setIsBookingModalOpen(true)
  }
  
  const handleViewAllSlots = (date, slots) => {
    if (!date || !Array.isArray(slots)) return
    setDaySlotsModalData({
      date: new Date(date),
      slots
    })
    setIsDaySlotsModalOpen(true)
  }
  
  const confirmBooking = async (course) => {
    if (!selectedSlot || !selectedTutor) return
    
    try {
      const av = selectedSlot.availability
      if (!av || !av.start_time) {
        alert('Availability data is missing')
        return
      }
      
      const dateKey = formatDateKey(selectedSlot.date)
      const [year, month, day] = dateKey.split('-')
      
      const avStartTime = av.start_time.split('T')[1]
      const [avStartHour, avStartMin] = avStartTime.split(':').map(Number)
      
      const slotStartMinutes = avStartHour * 60 + avStartMin + (selectedSlot.slotIndex * 20)
      const slotEndMinutes = slotStartMinutes + 20
      
      const startHour = Math.floor(slotStartMinutes / 60)
      const startMin = slotStartMinutes % 60
      const endHour = Math.floor(slotEndMinutes / 60)
      const endMin = slotEndMinutes % 60
      
      const startTimeStr = `${year}-${month}-${day}T${String(startHour).padStart(2, '0')}:${String(startMin).padStart(2, '0')}:00`
      const endTimeStr = `${year}-${month}-${day}T${String(endHour).padStart(2, '0')}:${String(endMin).padStart(2, '0')}:00`
      
      const availabilityId = av.id
      
      const bookingData = {
        availability_id: availabilityId,
        start_time: startTimeStr,
        end_time: endTimeStr,
        course: course || ''
      }
      
      const response = await api.bookSession(getToken, bookingData)
      
      if (response.ok) {
        setIsBookingModalOpen(false)
        setSelectedSlot(null)
        
        const [availabilityResponse, tutorSessionsResponse] = await Promise.all([
          api.getAvailability(getToken, selectedTutor.id),
          api.getSessions(getToken, selectedTutor.user_id)
        ])
        
        if (availabilityResponse.ok) {
          const availabilityData = await availabilityResponse.json()
          setAvailabilities(availabilityData.availabilities || [])
        }
        
        if (tutorSessionsResponse.ok) {
          const tutorSessionsData = await tutorSessionsResponse.json()
          setSessions(tutorSessionsData.sessions || [])
        }
      } else {
        const errorData = await response.json()
        alert(`Error: ${errorData.error || 'Failed to book session'}`)
      }
    } catch (error) {
      console.error('Error booking session:', error)
      alert(`Error: ${error.message}`)
    }
  }

  const handleViewNote = (session) => {
    setSelectedSession(session)
    setIsNoteModalOpen(true)
  }

  if (userData?.role === 'professor') {
    return (
      <div className="p-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground mb-2">
            All Sessions
          </h1>
          <p className="text-muted-foreground">
            View all tutoring sessions and notes
          </p>
        </div>

        <Card className="p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Date</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Time</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Tutor</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Student</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Course</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Type</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-foreground">Notes</th>
                </tr>
              </thead>
              <tbody>
                {sessions.length > 0 ? (
                  sessions.map((session) => {
                    const startDate = session.start_time ? new Date(session.start_time) : null
                    const endDate = session.end_time ? new Date(session.end_time) : null
                    
                    return (
                      <tr key={session.id} className="border-b border-border hover:bg-muted/50">
                        <td className="py-3 px-4 text-sm text-foreground">
                          {startDate ? startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }) : '-'}
                        </td>
                        <td className="py-3 px-4 text-sm text-foreground">
                          {startDate && endDate 
                            ? `${startDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })} - ${endDate.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })}`
                            : '-'
                          }
                        </td>
                        <td className="py-3 px-4 text-sm text-foreground">
                          {session.tutor_name || '-'}
                        </td>
                        <td className="py-3 px-4 text-sm text-foreground">
                          {session.student_name || '-'}
                        </td>
                        <td className="py-3 px-4 text-sm text-foreground">
                          {session.course || '-'}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {session.session_type === 'online' ? (
                              <Monitor className="w-4 h-4 text-muted-foreground" />
                            ) : (
                              <MapPin className="w-4 h-4 text-muted-foreground" />
                            )}
                            <span className="text-sm text-foreground capitalize">{session.session_type}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          <span className={cn(
                            "text-xs px-2 py-1 rounded",
                            session.status === 'booked' 
                              ? "bg-green-100 text-green-800" 
                              : "bg-blue-100 text-blue-800"
                          )}>
                            {session.status}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          {session.note ? (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleViewNote(session)}
                            >
                              View
                            </Button>
                          ) : (
                            <span className="text-sm text-muted-foreground">No notes</span>
                          )}
                        </td>
                      </tr>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-sm text-muted-foreground">
                      No sessions found
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        <Dialog open={isNoteModalOpen} onOpenChange={setIsNoteModalOpen}>
          <DialogContent className="sm:max-w-[600px]">
            <DialogHeader>
              <DialogTitle>Session Notes</DialogTitle>
              <DialogDescription>
                View session details and notes
              </DialogDescription>
            </DialogHeader>
            {selectedSession && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Tutor</Label>
                    <p className="text-sm text-foreground mt-1">{selectedSession.tutor_name || '-'}</p>
                  </div>
                  <div>
                    <Label>Student</Label>
                    <p className="text-sm text-foreground mt-1">{selectedSession.student_name || '-'}</p>
                  </div>
                  <div>
                    <Label>Date</Label>
                    <p className="text-sm text-foreground mt-1">
                      {selectedSession.start_time 
                        ? new Date(selectedSession.start_time).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' })
                        : '-'
                      }
                    </p>
                  </div>
                  <div>
                    <Label>Course</Label>
                    <p className="text-sm text-foreground mt-1">{selectedSession.course || '-'}</p>
                  </div>
                </div>
                
                {selectedSession.note && (
                  <>
                    <div>
                      <Label>Attendance Status</Label>
                      <p className="text-sm text-foreground mt-1">{selectedSession.note.attendance_status || '-'}</p>
                    </div>
                    <div>
                      <Label>Session Notes</Label>
                      <p className="text-sm text-foreground mt-1 whitespace-pre-wrap">
                        {selectedSession.note.notes || '-'}
                      </p>
                    </div>
                    <div>
                      <Label>Student Feedback</Label>
                      <p className="text-sm text-foreground mt-1 whitespace-pre-wrap">
                        {selectedSession.note.student_feedback || '-'}
                      </p>
                    </div>
                  </>
                )}
              </div>
            )}
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setIsNoteModalOpen(false)}
              >
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  if (userData?.role === 'student') {
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

        {tutors.length > 0 && (
          <Card className="p-6 mb-6">
            <h2 className="text-lg font-semibold text-foreground mb-4">Select Tutor</h2>
            <p className="text-sm text-muted-foreground mb-4">Choose a tutor to view their availability</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {tutors.map((tutor) => {
                const tutorName = tutor.user?.name?.trim();
                const tutorEmail = tutor.user?.email;
                const displayName = (tutorName && tutorName.length > 0) ? tutorName : (tutorEmail || 'Tutor');
                const displayInitial = (displayName[0] || 'T').toUpperCase();
                
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
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-muted flex items-center justify-center">
                      <span className="text-lg font-semibold">{displayInitial}</span>
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-foreground">{displayName}</div>
                      <div className="text-sm text-muted-foreground">{tutor.user?.class_name || 'CN126, CN127'}</div>
                      <div className="flex items-center gap-2 mt-1">
                        {tutor.session_type === 'online' ? (
                          <><Monitor className="w-3 h-3" /><span className="text-xs">Online</span></>
                        ) : tutor.session_type === 'in-person' ? (
                          <><MapPin className="w-3 h-3" /><span className="text-xs">In-Person</span></>
                        ) : (
                          <><Monitor className="w-3 h-3" /><MapPin className="w-3 h-3" /></>
                        )}
                      </div>
                    </div>
                    {selectedTutor?.id === tutor.id && (
                      <div className="text-xs font-medium px-2 py-1 bg-primary text-primary-foreground rounded">
                        Selected
                      </div>
                    )}
                  </div>
                </div>
                );
              })}
            </div>
          </Card>
        )}

        {selectedTutor && (
          <>
            <div className="mb-6 flex items-center gap-4">
              <Calendar className="w-5 h-5 text-foreground" />
              <span className="text-lg font-medium text-foreground">
                {monthYear} - {selectedTutor.user?.name}
              </span>
              <div className="flex gap-2 ml-auto">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => viewMode === 'month' ? navigateMonth(-1) : navigateWeek(-1)}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => viewMode === 'month' ? navigateMonth(1) : navigateWeek(1)}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <Card className="p-6">
              {viewMode === 'month' ? (
                <>
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
                                    
                                    const isBookedByMe = slot.session && slot.session.status === 'booked' && slot.session.student_id === userData?.id
                                    const isBookedByOthers = slot.session && slot.session.status === 'booked' && slot.session.student_id !== userData?.id
                                    
                                    return (
                                      <div
                                        key={slot.id}
                                        onClick={() => !isPastSlot && slot.isAvailable && !slot.session && handleBookSession(slot, day)}
                                        className={cn(
                                          "p-1 rounded text-[9px] flex items-center gap-1",
                                          isPastSlot
                                            ? "bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed opacity-50"
                                            : isBookedByMe
                                            ? "bg-green-100 text-green-800 border border-green-300 cursor-not-allowed"
                                            : isBookedByOthers
                                            ? "bg-gray-200 text-gray-800 border border-gray-300 cursor-not-allowed"
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
                                  <button
                                    type="button"
                                    onClick={() => handleViewAllSlots(day, timeSlots)}
                                    className="text-[8px] text-primary hover:underline text-center w-full mt-1"
                                  >
                                    +{timeSlots.length - 3} more
                                  </button>
                                )}
                              </div>
                            </>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </>
              ) : (
                <div className="grid grid-cols-7 gap-4">
                  {weekDays.map((day, index) => {
                    const timeSlots = getTimeSlotsForDay(day)
                    const now = new Date()
                    const today = new Date()
                    today.setHours(0, 0, 0, 0)
                    const dayDate = new Date(day)
                    dayDate.setHours(0, 0, 0, 0)
                    const isPastDate = dayDate < today
                    const isToday = dayDate.getTime() === today.getTime()
                    
                    return (
                      <div
                        key={index}
                        className={cn(
                          "flex flex-col p-3 border border-border rounded-lg",
                          isPastDate ? "bg-muted/50" : "bg-card"
                        )}
                      >
                        <div className={cn(
                          "text-xs font-medium mb-1 text-center",
                          isPastDate ? "text-muted-foreground/50" : "text-muted-foreground"
                        )}>
                          {formatDayName(day)}
                        </div>
                        <div className={cn(
                          "text-lg font-bold mb-3 text-center",
                          isPastDate ? "text-foreground/30" : "text-foreground"
                        )}>
                          {formatDayNumber(day)}
                        </div>
                        <div className="space-y-2">
                          {timeSlots.length > 0 ? (
                            timeSlots.map((slot) => {
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
                              const isPastSlot = isPastDate || (isToday && slotDateTime < now)
                              
                              const isBookedByMe = slot.session && slot.session.status === 'booked' && slot.session.student_id === userData?.id
                              const isBookedByOthers = slot.session && slot.session.status === 'booked' && slot.session.student_id !== userData?.id
                              
                              return (
                                <div
                                  key={slot.id}
                                  onClick={() => !isPastSlot && slot.isAvailable && !slot.session && handleBookSession(slot, day)}
                                  className={cn(
                                    "p-1.5 rounded text-[10px] flex items-center gap-1.5",
                                    isPastSlot
                                      ? "bg-gray-100 text-gray-400 border border-gray-200 cursor-not-allowed opacity-50"
                                      : isBookedByMe
                                      ? "bg-green-100 text-green-800 border border-green-300 cursor-not-allowed"
                                      : isBookedByOthers
                                      ? "bg-gray-200 text-gray-800 border border-gray-300 cursor-not-allowed"
                                      : slot.isAvailable
                                      ? "bg-blue-100 text-blue-800 border border-blue-200 cursor-pointer hover:bg-blue-200"
                                      : "bg-gray-100 text-gray-600 border border-gray-200 cursor-not-allowed"
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
                                      {isBookedByMe ? 'Booked by you' : slot.session && slot.session.status === 'booked' ? 'Booked' : 'Available'}
                                    </div>
                                  </div>
                                </div>
                              )
                            })
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
              )}

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
                  <div className="w-4 h-4 bg-green-100 border border-green-300 rounded"></div>
                  <span className="text-sm text-muted-foreground">Booked by you</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-gray-200 border border-gray-300 rounded"></div>
                  <span className="text-sm text-muted-foreground">Booked</span>
                </div>
              </div>
            </Card>
          </>
        )}

        <Dialog open={isDaySlotsModalOpen} onOpenChange={setIsDaySlotsModalOpen}>
          <DialogContent className="sm:max-w-[500px]">
            <DialogHeader>
              <DialogTitle>All availability for {selectedTutor?.user?.name}</DialogTitle>
              <DialogDescription>
                {daySlotsModalDateLabel || 'Select a date to view all slots'}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-2 max-h-[360px] overflow-y-auto">
              {daySlotsModalData.slots.length > 0 ? (
                daySlotsModalData.slots.map((slot, index) => {
                  const now = new Date()
                  const baseDate = daySlotsModalData.date ? new Date(daySlotsModalData.date) : null
                  const baseDay = baseDate
                    ? new Date(baseDate.getFullYear(), baseDate.getMonth(), baseDate.getDate())
                    : null
                  const today = new Date()
                  today.setHours(0, 0, 0, 0)
                  const isPastDate = baseDay ? baseDay < today : false
                  
                  let isPastSlot = false
                  if (baseDate) {
                    const slotDateTime = new Date(baseDate)
                    const timeMatch = slot.time.match(/(\d+):(\d+)\s*(AM|PM)/)
                    if (timeMatch) {
                      let hours = parseInt(timeMatch[1])
                      const minutes = parseInt(timeMatch[2])
                      const period = timeMatch[3]
                      if (period === 'PM' && hours !== 12) hours += 12
                      if (period === 'AM' && hours === 12) hours = 0
                      slotDateTime.setHours(hours, minutes, 0, 0)
                    }
                    isPastSlot =
                      isPastDate ||
                      (baseDay && baseDay.getTime() === today.getTime() && slotDateTime < now)
                  }
                  
                  const isBookedByMe = slot.session && slot.session.status === 'booked' && slot.session.student_id === userData?.id
                  const isBookedByOthers = slot.session && slot.session.status === 'booked' && slot.session.student_id !== userData?.id
                  
                  return (
                    <div
                      key={`${slot.id}-${index}`}
                      onClick={() => !isPastSlot && slot.isAvailable && !slot.session && handleBookSession(slot, daySlotsModalData.date)}
                      className={cn(
                        "p-2 rounded text-sm flex items-center gap-2 border",
                        isPastSlot
                          ? "bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed opacity-50"
                          : isBookedByMe
                          ? "bg-green-100 text-green-800 border-green-300 cursor-not-allowed"
                          : isBookedByOthers
                          ? "bg-gray-200 text-gray-800 border-gray-300 cursor-not-allowed"
                          : slot.isAvailable
                          ? "bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-200 cursor-pointer"
                          : "bg-gray-100 text-gray-500 border-gray-200 cursor-not-allowed"
                      )}
                    >
                      {slot.type === 'online' ? (
                        <Monitor className="w-3.5 h-3.5 flex-shrink-0" />
                      ) : (
                        <MapPin className="w-3.5 h-3.5 flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate text-sm">{slot.time}</div>
                        <div className="text-xs opacity-75">
                          {isBookedByMe ? 'Booked by you' : slot.session && slot.session.status === 'booked' ? 'Booked' : slot.isAvailable ? 'Available' : 'Unavailable'}
                        </div>
                      </div>
                    </div>
                  )
                })
              ) : (
                <div className="text-sm text-muted-foreground">
                  No availability for this day.
                </div>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsDaySlotsModalOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        <Dialog open={isBookingModalOpen} onOpenChange={setIsBookingModalOpen}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Book Session</DialogTitle>
              <DialogDescription>
                Confirm your session booking with {selectedTutor?.user?.name}
              </DialogDescription>
            </DialogHeader>
            <form onSubmit={(e) => {
              e.preventDefault()
              const formData = new FormData(e.target)
              confirmBooking(formData.get('course'))
            }}>
              <div className="grid gap-4 py-4">
                <div className="grid gap-2">
                  <Label>Date & Time</Label>
                  <div className="text-sm text-muted-foreground">
                    {selectedSlot?.date && formatDateKey(selectedSlot.date)} at {selectedSlot?.time}
                  </div>
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="course">Course (Optional)</Label>
                  <Select
                    onValueChange={(value) => {
                      const form = document.querySelector('form')
                      if (form) {
                        let hiddenInput = form.querySelector('input[name="course"]')
                        if (!hiddenInput) {
                          hiddenInput = document.createElement('input')
                          hiddenInput.type = 'hidden'
                          hiddenInput.name = 'course'
                          form.appendChild(hiddenInput)
                        }
                        hiddenInput.value = value
                      }
                    }}
                  >
                    <SelectTrigger id="course">
                      <SelectValue placeholder="Select a course (optional)" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CN115">CN115</SelectItem>
                      <SelectItem value="CN125">CN125</SelectItem>
                      <SelectItem value="CN126">CN126</SelectItem>
                      <SelectItem value="CN127">CN127</SelectItem>
                      <SelectItem value="CN128">CN128</SelectItem>
                      <SelectItem value="CN135">CN135</SelectItem>
                      <SelectItem value="CN235">CN235</SelectItem>
                      <SelectItem value="CN321">CN321</SelectItem>
                      <SelectItem value="CN322">CN322</SelectItem>
                      <SelectItem value="CN335">CN335</SelectItem>
                      <SelectItem value="CN434">CN434</SelectItem>
                      <SelectItem value="CN455">CN455</SelectItem>
                    </SelectContent>
                  </Select>
                  <input type="hidden" name="course" value="" />
                </div>
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setIsBookingModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  Confirm Booking
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    )
  }

  return (
    <div className="p-8">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">
            Sessions
          </h1>
          <p className="text-muted-foreground">
            Manage your tutoring schedule and time slots
          </p>
        </div>
        <div className="flex gap-2">
          <div className="flex gap-2 mr-4">
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
          <Button onClick={() => setIsModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Availability
          </Button>
        </div>
      </div>

      {/* Calendar Navigation */}
      <div className="mb-6 flex items-center gap-4">
        <Calendar className="w-5 h-5 text-foreground" />
        <span className="text-lg font-medium text-foreground">
          {monthYear}
        </span>
        <div className="flex gap-2 ml-auto">
          <Button
            variant="outline"
            size="icon"
            onClick={() => viewMode === 'month' ? navigateMonth(-1) : navigateWeek(-1)}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={() => viewMode === 'month' ? navigateMonth(1) : navigateWeek(1)}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <Card className="p-6">
        {viewMode === 'month' ? (
          <>
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
                                  className={cn(
                                    "p-1 rounded text-[9px] flex items-center gap-1",
                                    isPastSlot
                                      ? "bg-gray-100 text-gray-400 border border-gray-200 opacity-50"
                                      : slot.session && slot.session.status === 'booked'
                                      ? "bg-gray-100 text-gray-800 border border-gray-200"
                                      : slot.session
                                      ? "bg-blue-100 text-blue-800 border border-blue-200"
                                      : "bg-blue-100 text-blue-800 border border-blue-200"
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
          </>
        ) : (
          <div className="grid grid-cols-7 gap-4">
            {weekDays.map((day, index) => {
              const timeSlots = getTimeSlotsForDay(day)
              const now = new Date()
              const today = new Date()
              today.setHours(0, 0, 0, 0)
              const dayDate = new Date(day)
              dayDate.setHours(0, 0, 0, 0)
              const isPastDate = dayDate < today
              const isToday = dayDate.getTime() === today.getTime()
              
              return (
                <div
                  key={index}
                  className={cn(
                    "flex flex-col p-3 border border-border rounded-lg",
                    isPastDate ? "bg-muted/50" : "bg-card"
                  )}
                >
                  <div className={cn(
                    "text-xs font-medium mb-1 text-center",
                    isPastDate ? "text-muted-foreground/50" : "text-muted-foreground"
                  )}>
                    {formatDayName(day)}
                  </div>
                  <div className={cn(
                    "text-lg font-bold mb-3 text-center",
                    isPastDate ? "text-foreground/30" : "text-foreground"
                  )}>
                    {formatDayNumber(day)}
                  </div>
                  <div className="space-y-2">
                    {timeSlots.length > 0 ? (
                      timeSlots.map((slot) => {
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
                        const isPastSlot = isPastDate || (isToday && slotDateTime < now)
                        
                        return (
                          <div
                            key={slot.id}
                            className={cn(
                              "p-1.5 rounded text-[10px] flex items-center gap-1.5",
                              isPastSlot
                                ? "bg-gray-100 text-gray-400 border border-gray-200 opacity-50"
                                : slot.session && slot.session.status === 'booked'
                                ? "bg-gray-200 text-gray-800 border border-gray-300"
                                : slot.session
                                ? "bg-blue-100 text-blue-800 border border-blue-200"
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
                                {slot.session && slot.session.status === 'booked' ? 'Booked' : slot.session ? 'Available Session' : 'Available'}
                              </div>
                            </div>
                          </div>
                        )
                      })
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
        )}

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
            <div className="w-4 h-4 bg-gray-200 border border-gray-300 rounded"></div>
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
                    placeholder="mm/dd/yyyy"
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
                    min={new Date().toISOString().split('T')[0]}
                    onChange={(e) => {
                      const nativeDate = e.target.value
                      if (nativeDate) {
                        const date = new Date(nativeDate)
                        const month = (date.getMonth() + 1).toString().padStart(2, '0')
                        const day = date.getDate().toString().padStart(2, '0')
                        const year = date.getFullYear()
                        setFormData({ 
                          ...formData, 
                          date: `${month}/${day}/${year}`,
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
                        // Convert mm/dd/yyyy to YYYY-MM-DD for native input
                        if (formData.date) {
                          const [month, day, year] = formData.date.split('/')
                          if (month && day && year) {
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

