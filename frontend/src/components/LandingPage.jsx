import { SignInButton, SignUpButton } from '@clerk/clerk-react'
import { Calendar, Users, BookOpen, Clock, CheckCircle, MessageCircle } from 'lucide-react'

function LandingPage() {
  return (
    <div className="auth-container" style={{ padding: '80px 20px' }}>
      <div className="max-w-6xl w-full px-6">
        <div className="text-center mb-20">
          <h1 className="text-5xl mb-8" style={{ 
            fontWeight: 400, 
            textTransform: 'uppercase', 
            letterSpacing: '2px',
            color: '#000000'
          }}>
            Chinese Tutoring System
          </h1>
          <p className="text-lg mb-3" style={{ color: '#666666', letterSpacing: '0.5px' }}>
            East Asian Studies Department
          </p>
          <p className="text-base mb-16" style={{ color: '#666666' }}>
            Colby College
          </p>
          
          <div className="flex gap-4 justify-center">
            <SignInButton mode="modal">
              <button className="btn btn-secondary">
                Sign In
              </button>
            </SignInButton>
            <SignUpButton mode="modal">
              <button className="btn btn-primary">
                Get Started
              </button>
            </SignUpButton>
          </div>
        </div>

        <div className="mb-20 pb-20" style={{ borderBottom: '1px solid #000000' }}>
          <h2 className="text-2xl mb-12 text-center" style={{ 
            fontWeight: 400, 
            textTransform: 'uppercase', 
            letterSpacing: '1px',
            color: '#000000'
          }}>
            Features
          </h2>
          <div className="grid md:grid-cols-3 gap-8">
            <div className="p-8" style={{ border: '1px solid #000000', background: '#ffffff' }}>
              <Calendar className="mb-6" size={32} style={{ color: '#000000' }} />
              <h3 className="text-base mb-4" style={{ 
                fontWeight: 400, 
                textTransform: 'uppercase', 
                letterSpacing: '0.5px',
                color: '#000000'
              }}>
                Smart Scheduling
              </h3>
              <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                Intelligent matching system finds tutors based on your availability and learning needs
              </p>
            </div>

            <div className="p-8" style={{ border: '1px solid #000000', background: '#ffffff' }}>
              <Users className="mb-6" size={32} style={{ color: '#000000' }} />
              <h3 className="text-base mb-4" style={{ 
                fontWeight: 400, 
                textTransform: 'uppercase', 
                letterSpacing: '0.5px',
                color: '#000000'
              }}>
                Expert Tutors
              </h3>
              <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                Connect with experienced Chinese language tutors from the department
              </p>
            </div>

            <div className="p-8" style={{ border: '1px solid #000000', background: '#ffffff' }}>
              <BookOpen className="mb-6" size={32} style={{ color: '#000000' }} />
              <h3 className="text-base mb-4" style={{ 
                fontWeight: 400, 
                textTransform: 'uppercase', 
                letterSpacing: '0.5px',
                color: '#000000'
              }}>
                Track Progress
              </h3>
              <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                Monitor your learning journey with session history and feedback
              </p>
            </div>

            <div className="p-8" style={{ border: '1px solid #000000', background: '#ffffff' }}>
              <Clock className="mb-6" size={32} style={{ color: '#000000' }} />
              <h3 className="text-base mb-4" style={{ 
                fontWeight: 400, 
                textTransform: 'uppercase', 
                letterSpacing: '0.5px',
                color: '#000000'
              }}>
                Flexible Hours
              </h3>
              <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                Book tutoring sessions that fit your schedule at any time
              </p>
            </div>

            <div className="p-8" style={{ border: '1px solid #000000', background: '#ffffff' }}>
              <MessageCircle className="mb-6" size={32} style={{ color: '#000000' }} />
              <h3 className="text-base mb-4" style={{ 
                fontWeight: 400, 
                textTransform: 'uppercase', 
                letterSpacing: '0.5px',
                color: '#000000'
              }}>
                Feedback System
              </h3>
              <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                Receive personalized feedback after each tutoring session
              </p>
            </div>

            <div className="p-8" style={{ border: '1px solid #000000', background: '#ffffff' }}>
              <CheckCircle className="mb-6" size={32} style={{ color: '#000000' }} />
              <h3 className="text-base mb-4" style={{ 
                fontWeight: 400, 
                textTransform: 'uppercase', 
                letterSpacing: '0.5px',
                color: '#000000'
              }}>
                Easy Management
              </h3>
              <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                Manage all your sessions from one centralized dashboard
              </p>
            </div>
          </div>
        </div>

        <div className="mb-20">
          <h2 className="text-2xl mb-12 text-center" style={{ 
            fontWeight: 400, 
            textTransform: 'uppercase', 
            letterSpacing: '1px',
            color: '#000000'
          }}>
            How It Works
          </h2>
          <div className="grid md:grid-cols-2 gap-10 max-w-4xl mx-auto">
            <div className="flex gap-5">
              <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center" style={{ 
                border: '1px solid #000000',
                background: '#000000',
                color: '#ffffff',
                fontWeight: 400
              }}>
                1
              </div>
              <div>
                <h3 className="text-base mb-2" style={{ 
                  fontWeight: 400, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px',
                  color: '#000000'
                }}>
                  Create Account
                </h3>
                <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                  Sign up and complete your profile
                </p>
              </div>
            </div>

            <div className="flex gap-5">
              <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center" style={{ 
                border: '1px solid #000000',
                background: '#000000',
                color: '#ffffff',
                fontWeight: 400
              }}>
                2
              </div>
              <div>
                <h3 className="text-base mb-2" style={{ 
                  fontWeight: 400, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px',
                  color: '#000000'
                }}>
                  Set Availability
                </h3>
                <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                  Tell us when you're available
                </p>
              </div>
            </div>

            <div className="flex gap-5">
              <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center" style={{ 
                border: '1px solid #000000',
                background: '#000000',
                color: '#ffffff',
                fontWeight: 400
              }}>
                3
              </div>
              <div>
                <h3 className="text-base mb-2" style={{ 
                  fontWeight: 400, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px',
                  color: '#000000'
                }}>
                  Book Sessions
                </h3>
                <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                  Review and book with matched tutors
                </p>
              </div>
            </div>

            <div className="flex gap-5">
              <div className="flex-shrink-0 w-12 h-12 flex items-center justify-center" style={{ 
                border: '1px solid #000000',
                background: '#000000',
                color: '#ffffff',
                fontWeight: 400
              }}>
                4
              </div>
              <div>
                <h3 className="text-base mb-2" style={{ 
                  fontWeight: 400, 
                  textTransform: 'uppercase', 
                  letterSpacing: '0.5px',
                  color: '#000000'
                }}>
                  Learn & Grow
                </h3>
                <p style={{ fontSize: '14px', lineHeight: '1.8', color: '#666666' }}>
                  Attend sessions and track progress
                </p>
              </div>
            </div>
          </div>
        </div>

        <div className="text-center pt-20" style={{ borderTop: '1px solid #000000' }}>
          <SignUpButton mode="modal">
            <button className="btn btn-primary">
              Get Started Today
            </button>
          </SignUpButton>
        </div>
      </div>
    </div>
  )
}

export default LandingPage
