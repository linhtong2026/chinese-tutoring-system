import { useState } from 'react'
import { useUser, useAuth } from '@clerk/clerk-react'
import api from '../services/api'

function OnboardingForm({ onComplete }) {
  const { user } = useUser()
  const { getToken } = useAuth()
  const [currentStep] = useState(0)
  const [formData, setFormData] = useState({
    language: 'en',
    class_name: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const steps = [
    {
      title: 'Welcome',
      questions: [
        {
          id: 'language',
          type: 'radio',
          label: 'What language would you prefer?',
          options: [
            { value: 'en', label: 'English' },
            { value: 'zh', label: '中文 (Chinese)' }
          ]
        },
        {
          id: 'class_name',
          type: 'text',
          label: 'Which class are you in?',
          placeholder: 'CH322, CH312, etc.'
        }
      ]
    }
  ]

  const handleChange = (questionId, value) => {
    setFormData(prev => ({
      ...prev,
      [questionId]: value
    }))
    setError(null)
  }

  const handleNext = async () => {
    await handleSubmit()
  }

  const handleSubmit = async () => {
    setIsSubmitting(true)
    setError(null)
    
    try {
      const response = await api.completeOnboarding(getToken, {
        language: formData.language,
        class_name: formData.class_name
      })

      const data = await response.json()

      if (!response.ok) {
        setError(data.error || 'Failed to complete onboarding')
        setIsSubmitting(false)
        return
      }

      await user.reload()
      onComplete()
    } catch (error) {
      console.error('Error completing onboarding:', error)
      setError('An error occurred. Please try again.')
      setIsSubmitting(false)
    }
  }

  const currentStepData = steps[currentStep]
  const isLastStep = currentStep === steps.length - 1
  const canProceed = currentStepData.questions.every(q => formData[q.id]) && !isSubmitting

  return (
    <div className="onboarding-container">
      <div className="onboarding-card">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          />
        </div>
        
        <h2 className="step-title">{currentStepData.title}</h2>
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}
        
        <div className="questions-container">
          {currentStepData.questions.map((question) => (
            <div key={question.id} className="question-group">
              <label className="question-label">{question.label}</label>
              {question.type === 'radio' && (
                <div className="radio-group">
                  {question.options.map((option) => (
                    <label key={option.value} className="radio-option">
                      <input
                        type="radio"
                        name={question.id}
                        value={option.value}
                        checked={formData[question.id] === option.value}
                        onChange={(e) => handleChange(question.id, e.target.value)}
                        disabled={isSubmitting}
                      />
                      <span>{option.label}</span>
                    </label>
                  ))}
                </div>
              )}
              {question.type === 'text' && (
                <input
                  type="text"
                  value={formData[question.id]}
                  onChange={(e) => handleChange(question.id, e.target.value)}
                  disabled={isSubmitting}
                  placeholder={question.placeholder}
                  className="text-input"
                />
              )}
            </div>
          ))}
        </div>

        <div className="button-group">
          <button
            type="button"
            onClick={isLastStep ? handleSubmit : handleNext}
            disabled={!canProceed}
            className="btn btn-primary"
          >
            {isSubmitting ? 'Processing...' : isLastStep ? 'Complete' : 'Next'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default OnboardingForm

