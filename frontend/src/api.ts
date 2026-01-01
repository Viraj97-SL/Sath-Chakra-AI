import axios from 'axios';

// This links your Frontend to your FastAPI backend
const api = axios.create({
  baseURL: 'http://localhost:8000',
});

export default api;