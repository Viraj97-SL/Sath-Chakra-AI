import axios from 'axios';

const api = axios.create({
  // Get this URL from your Railway Dashboard Settings > Networking
  baseURL: 'https://sath-chakra-ai-production.up.railway.app',
  headers: {
    'Content-Type': 'application/json',
  }
});

export default api;