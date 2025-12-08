import { useState, useEffect } from 'react'
import { useAuth } from '@clerk/clerk-react'
import { Calendar, Clock, Users, TrendingUp } from 'lucide-react'
import { Card } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Bar, Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import api from '@/services/api'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

function Dashboard({ userData }) {
  const { getToken } = useAuth()
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedClass, setSelectedClass] = useState(null)
  const [selectedTutor, setSelectedTutor] = useState(null)

  const isProfessor = userData?.role === 'professor'
  const isTutor = userData?.role === 'tutor'

  useEffect(() => {
    if (!userData) return
    
    const role = userData.role
    if (role !== 'professor' && role !== 'tutor') return

    let isCancelled = false
    
    const fetchDashboard = async (isInitial = false) => {
      try {
        let response
        if (role === 'professor') {
          response = await api.getProfessorDashboard(getToken, selectedClass, selectedTutor)
        } else {
          response = await api.getTutorDashboard(getToken)
        }
        
        if (!isCancelled && response && response.ok) {
          const data = await response.json()
          setDashboardData(data)
          if (isInitial) setLoading(false)
        }
      } catch (error) {
        if (!isCancelled) {
          console.error('Error fetching dashboard:', error)
          if (isInitial) setLoading(false)
        }
      }
    }

    fetchDashboard(true)
    
    const intervalId = setInterval(() => fetchDashboard(false), 30000)
    
    return () => {
      isCancelled = true
      clearInterval(intervalId)
    }
  }, [userData?.role, selectedClass, selectedTutor])

  if (loading || !dashboardData) {
    return (
      <div className="p-8">
        <div className="text-center text-muted-foreground">Loading dashboard...</div>
      </div>
    )
  }

  const { stats, weekly_data, monthly_attendance, course_distribution, top_students, filters } = dashboardData
  const hasFilters = isProfessor && filters
  
  const weeklyChartData = {
    labels: weekly_data.map(d => d.week),
    datasets: [
      {
        label: 'Hours',
        data: weekly_data.map(d => d.hours),
        backgroundColor: 'rgba(34, 197, 94, 0.5)',
        borderColor: 'rgba(34, 197, 94, 1)',
        borderWidth: 2,
      },
      {
        label: 'Sessions',
        data: weekly_data.map(d => d.sessions),
        backgroundColor: 'rgba(59, 130, 246, 0.5)',
        borderColor: 'rgba(59, 130, 246, 1)',
        borderWidth: 2,
      }
    ]
  }

  const weeklyChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
      }
    }
  }

  const attendanceChartData = {
    labels: monthly_attendance.map(m => m.month),
    datasets: [
      {
        label: 'Attendance %',
        data: monthly_attendance.map(m => m.rate),
        borderColor: 'rgba(59, 130, 246, 1)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
      }
    ]
  }

  const attendanceChartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function(value) {
            return value + '%'
          }
        }
      }
    }
  }

  return (
    <div className="p-8">
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold text-foreground mb-2">Dashboard</h1>
            <p className="text-muted-foreground">
              {isProfessor ? 'Monitor tutoring program activity and insights' : 'Track your tutoring sessions and performance'}
            </p>
          </div>
          {hasFilters && (
            <div className="flex gap-3">
              <Select value={selectedClass || 'all'} onValueChange={(val) => setSelectedClass(val === 'all' ? null : val)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by class" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Classes</SelectItem>
                  {filters.classes.map(cls => (
                    <SelectItem key={cls} value={cls}>{cls}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={selectedTutor || 'all'} onValueChange={(val) => setSelectedTutor(val === 'all' ? null : val)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by tutor" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Tutors</SelectItem>
                  {filters.tutors.map(tutor => (
                    <SelectItem key={tutor.id} value={tutor.id.toString()}>{tutor.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Total Sessions</p>
              <p className="text-3xl font-bold text-foreground">{stats.total_sessions}</p>
              <p className="text-xs text-muted-foreground mt-1">{isTutor ? 'Your sessions' : 'Booked sessions'}</p>
            </div>
            <Calendar className="w-8 h-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Hours Logged</p>
              <p className="text-3xl font-bold text-foreground">{stats.total_hours}</p>
              <p className="text-xs text-muted-foreground mt-1">{isTutor ? 'Your tutoring hours' : 'Across all courses'}</p>
            </div>
            <Clock className="w-8 h-8 text-muted-foreground" />
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground mb-1">Active Students</p>
              <p className="text-3xl font-bold text-foreground">{stats.active_students}</p>
              <p className="text-xs text-muted-foreground mt-1">{isTutor ? 'Your students' : 'This semester'}</p>
            </div>
            <Users className="w-8 h-8 text-muted-foreground" />
          </div>
        </Card>

        {isProfessor && (
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground mb-1">Avg Rating</p>
                <p className="text-3xl font-bold text-foreground">{stats.avg_rating || 'N/A'}</p>
                <p className="text-xs text-muted-foreground mt-1">From student feedback</p>
              </div>
              <TrendingUp className="w-8 h-8 text-muted-foreground" />
            </div>
          </Card>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-foreground mb-2">Sessions & Hours by Week</h2>
          <p className="text-sm text-muted-foreground mb-6">
            {isTutor ? 'Track your tutoring activity over time' : 'Track tutoring activity over time'}
          </p>
          
          <div style={{ height: '300px' }}>
            <Bar data={weeklyChartData} options={weeklyChartOptions} />
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold text-foreground mb-2">Attendance Rate</h2>
          <p className="text-sm text-muted-foreground mb-6">
            {isTutor ? 'Your monthly attendance percentage' : 'Monthly attendance percentage'}
          </p>
          
          <div style={{ height: '250px' }}>
            <Line data={attendanceChartData} options={attendanceChartOptions} />
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h2 className="text-lg font-semibold text-foreground mb-2">Course Distribution</h2>
          <p className="text-sm text-muted-foreground mb-4">
            {isTutor ? 'Your sessions by course' : 'Sessions by course'}
          </p>
          
          <div className="space-y-3">
            {Object.keys(course_distribution).length > 0 ? (
              Object.entries(course_distribution)
                .sort((a, b) => b[1] - a[1])
                .map(([course, count]) => (
                  <div key={course} className="flex items-center justify-between">
                    <span className="text-sm text-foreground">{course}</span>
                    <div className="flex items-center gap-3">
                      <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-primary rounded-full"
                          style={{ width: `${(count / stats.total_sessions) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm text-muted-foreground w-8 text-right">{count}</span>
                    </div>
                  </div>
                ))
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No course data available</p>
            )}
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-lg font-semibold text-foreground mb-2">
            {isTutor ? 'Students You\'ve Tutored' : 'Student Attendance'}
          </h2>
          <p className="text-sm text-muted-foreground mb-4">Top students by session count</p>
          
          <div className="space-y-3">
            {top_students.length > 0 ? (
              top_students.map((student, index) => (
                <div key={student.name} className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm font-medium">
                    {student.name.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium text-foreground">{student.name}</div>
                    <div className="text-xs text-muted-foreground">{student.count} sessions</div>
                  </div>
                  <div className="text-sm font-semibold text-foreground">#{index + 1}</div>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground text-center py-4">No student data available</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  )
}

export default Dashboard

