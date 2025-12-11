const API_URL = import.meta.env.VITE_API_URL

class ApiService {
  async getAuthHeaders(getToken) {
    const token = await getToken()
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

  async getTutorByUser(getToken, userId) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/tutor/by-user/${userId}`, {
      method: 'GET',
      headers
    })
    return response
  }

  async getSessions(getToken, tutorId) {
    const headers = await this.getAuthHeaders(getToken)
    const url = tutorId ? `${API_URL}/api/tutor/sessions?tutor_id=${tutorId}` : `${API_URL}/api/tutor/sessions`
    const response = await fetch(url, {
      method: 'GET',
      headers
    })
    return response
  }

  async getAvailability(getToken, tutorId) {
    const headers = await this.getAuthHeaders(getToken)
    const url = tutorId ? `${API_URL}/api/availability?tutor_id=${tutorId}` : `${API_URL}/api/availability`
    const response = await fetch(url, {
      method: 'GET',
      headers
    })
    return response
  }

  async createAvailability(getToken, data) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/availability`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    })
    return response
  }

  async getTutors(getToken) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/tutors`, {
      method: 'GET',
      headers
    })
    return response
  }

  async bookSession(getToken, data) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/sessions/book`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    })
    return response
  }

  async createSessionNote(getToken, data) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/session-notes`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    })
    return response
  }

  async updateSessionNote(getToken, noteId, data) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/session-notes/${noteId}`, {
      method: 'PUT',
      headers,
      body: JSON.stringify(data)
    })
    return response
  }

  async getSessionNote(getToken, sessionId) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/sessions/${sessionId}/note`, {
      method: 'GET',
      headers
    })
    return response
  }

  async getProfessorSessions(getToken) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/professor/sessions`, {
      method: 'GET',
      headers
    })
    return response
  }

  async getProfessorDashboard(getToken, classFilter = null, tutorFilter = null) {
    const headers = await this.getAuthHeaders(getToken)
    const params = new URLSearchParams()
    if (classFilter) params.append('class', classFilter)
    if (tutorFilter) params.append('tutor', tutorFilter)
    const queryString = params.toString()
    const url = `${API_URL}/api/professor/dashboard${queryString ? `?${queryString}` : ''}`
    const response = await fetch(url, {
      method: 'GET',
      headers
    })
    return response
  }

  async getTutorDashboard(getToken) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/tutor/dashboard`, {
      method: 'GET',
      headers
    })
    return response
  }

  async submitFeedback(getToken, data) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/feedback`, {
      method: 'POST',
      headers,
      body: JSON.stringify(data)
    })
    return response
  }

  async getSessionFeedback(getToken, sessionId) {
    const headers = await this.getAuthHeaders(getToken)
    const response = await fetch(`${API_URL}/api/sessions/${sessionId}/feedback`, {
      method: 'GET',
      headers
    })
    return response
  }

  async getRecommendedTutors(getToken, params = {}) {
    const headers = await this.getAuthHeaders(getToken)
    const queryParams = new URLSearchParams()
    if (params.day !== undefined) queryParams.append('day', params.day)
    if (params.time) queryParams.append('time', params.time)
    if (params.session_type) queryParams.append('session_type', params.session_type)
    if (params.limit) queryParams.append('limit', params.limit)
    const queryString = queryParams.toString()
    const url = `${API_URL}/api/matching/recommend${queryString ? `?${queryString}` : ''}`
    const response = await fetch(url, {
      method: 'GET',
      headers
    })
    return response
  }
}

export default new ApiService()

