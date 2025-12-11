import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton, useUser, useAuth } from '@clerk/clerk-react'
import { useState, useEffect } from 'react'
import { Routes, Route } from 'react-router-dom'
import OnboardingForm from './components/OnboardingForm'
import Layout from './components/Layout'
import Sessions from './components/Sessions'
import SessionHistory from './components/SessionHistory'
import StudentSessionHistory from './components/StudentSessionHistory'
import Dashboard from './components/Dashboard'
import FeedbackPage from './components/FeedbackPage'
import UserManagement from './components/UserManagement'
import api from './services/api'

function App() {
  const { user, isLoaded } = useUser()
  const { getToken } = useAuth()
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [checkingOnboarding, setCheckingOnboarding] = useState(true)
  const [userData, setUserData] = useState(null)
  const [currentPage, setCurrentPage] = useState('sessions')

  useEffect(() => {
    const checkOnboarding = async () => {
      if (isLoaded && user) {
        try {
          const response = await api.getUser(getToken)
          
          if (response.ok) {
            const data = await response.json()
            setUserData(data.user)
            setShowOnboarding(!data.onboarding_complete)
            if (data.user?.role === 'professor' || data.user?.role === 'tutor') {
              setCurrentPage('dashboard')
            }
          } else {
            setShowOnboarding(true)
          }
        } catch (error) {
          console.error('Error checking onboarding:', error)
          setShowOnboarding(true)
        }
        setCheckingOnboarding(false)
      } else if (isLoaded && !user) {
        setCheckingOnboarding(false)
      }
    }
    
    checkOnboarding()
  }, [user, isLoaded, getToken])

  const handleOnboardingComplete = async () => {
    await user.reload()
    setShowOnboarding(false)
    // Refresh user data
    const response = await api.getUser(getToken)
    if (response.ok) {
      const data = await response.json()
      setUserData(data.user)
    }
  }

  const renderPageContent = () => {
    switch (currentPage) {
      case 'dashboard':
        return <Dashboard userData={userData} />
      case 'sessions':
        return <Sessions userData={userData} />
      case 'history':
        return userData?.role === 'student' 
          ? <StudentSessionHistory userData={userData} />
          : <SessionHistory userData={userData} />
      case 'users':
        return <UserManagement userData={userData} />
      default:
        if (userData?.role === 'professor' || userData?.role === 'tutor') {
          return <Dashboard userData={userData} />
        }
        return <Sessions userData={userData} />
    }
  }

  if (checkingOnboarding) {
    return (
      <div className="loading-container">
        <div className="loader">Loading...</div>
      </div>
    )
  }

  const mainAppContent = (
    <div className="app">
      <SignedOut>
        <div className="auth-container">
          <h1>Chinese Tutoring System</h1>
          <div className="auth-buttons">
            <SignInButton mode="modal" />
            <SignUpButton mode="modal" />
          </div>
        </div>
      </SignedOut>
      
      <SignedIn>
        {showOnboarding ? (
          <OnboardingForm onComplete={handleOnboardingComplete} />
        ) : userData?.role === 'tutor' ? (
          <Layout 
            currentPage={currentPage} 
            onPageChange={setCurrentPage}
            userData={userData}
          >
            {renderPageContent()}
          </Layout>
        ) : userData?.role === 'student' ? (
          <Layout 
            currentPage={currentPage} 
            onPageChange={setCurrentPage}
            userData={userData}
          >
            {renderPageContent()}
          </Layout>
        ) : userData?.role === 'professor' ? (
          <Layout 
            currentPage={currentPage} 
            onPageChange={setCurrentPage}
            userData={userData}
          >
            {renderPageContent()}
          </Layout>
        ) : (
          <div className="dashboard">
            <header className="dashboard-header">
              <h1>Chinese Tutoring System</h1>
              <UserButton />
            </header>
            <main className="dashboard-content">
              <p>Welcome! Your dashboard will appear here.</p>
            </main>
          </div>
        )}
      </SignedIn>
    </div>
  )

  return (
    <Routes>
      <Route path="/feedback/:sessionId" element={<FeedbackPage />} />
      <Route path="*" element={mainAppContent} />
    </Routes>
  )
}

export default App
