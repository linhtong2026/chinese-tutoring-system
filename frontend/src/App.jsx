import { SignedIn, SignedOut, SignInButton, SignUpButton, UserButton, useUser, useAuth } from '@clerk/clerk-react'
import { useState, useEffect } from 'react'
import OnboardingForm from './OnboardingForm'
import api from './services/api'

function App() {
  const { user, isLoaded } = useUser()
  const { getToken } = useAuth()
  const [showOnboarding, setShowOnboarding] = useState(false)
  const [checkingOnboarding, setCheckingOnboarding] = useState(true)

  useEffect(() => {
    const checkOnboarding = async () => {
      if (isLoaded && user) {
        try {
          const response = await api.getUser(getToken)
          
          if (response.ok) {
            const data = await response.json()
            setShowOnboarding(!data.onboarding_complete)
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
  }

  if (checkingOnboarding) {
    return (
      <div className="loading-container">
        <div className="loader">Loading...</div>
      </div>
    )
  }

  return (
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
}

export default App
