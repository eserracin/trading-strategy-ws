import axios from 'axios';
import { toast } from 'react-toastify';
import { navigateTo } from '../components/common/Navigation';


const axiosClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 🔁 Interceptor de solicitud: agrega token automáticamente
axiosClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 🚨 Interceptor de respuesta: maneja errores
axiosClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const { status, data } = error.response;
    if (status === 401) {
      toast.error('Unauthorized access. Please log in again.');
      localStorage.removeItem('token');
      navigateTo('/login');
    } else if (status === 403) {
      toast.error('Forbidden access. You do not have permission to perform this action.');
    } else if (status >= 500) {
      toast.error('Server error. Please try again later.');
    } else if (data && data.message) {
      toast.error(data.message);
    } else {
      toast.error('An unexpected error occurred. Please try again.');
    }
    return Promise.reject(error);
  }
);

export default axiosClient;