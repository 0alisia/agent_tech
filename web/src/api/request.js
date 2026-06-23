import axios from 'axios'

const service = axios.create({
  baseURL: '/api',
  timeout: 60000
})

service.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

service.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response && error.response.status === 401) {
      localStorage.removeItem('token')
      location.href = '/#/login'
    }
    return Promise.reject(error)
  }
)

export default service
