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
}

export default new ApiService()

