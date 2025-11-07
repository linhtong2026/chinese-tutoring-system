const API_URL = import.meta.env.VITE_API_URL

class ApiService {
  async getAuthHeaders(getToken) {
    const token = await getToken()
    console.log('JWT Token:', token)
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    }
  }

  async getUser(getToken) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/user`, {
      method: 'GET',
      headers
    })
    return response
  }

  async completeOnboarding(getToken, data) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/user/onboarding`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    })
    return response
  }

  async getTutorSessions(getToken, params = {}) {
    const headers = await this.getAuthHeaders(getToken)
    const queryParams = new URLSearchParams(params).toString()
    const url = `${API_URL}/api/tutor/sessions${queryParams ? `?${queryParams}` : ''}`
    const response = await fetch(url, {
      method: 'GET',
      headers
    })
    return response
  }

  async getStudentSessions(getToken) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/student/sessions`, {
      method: 'GET',
      headers
    })
    return response
  }
}

export default new ApiService()

