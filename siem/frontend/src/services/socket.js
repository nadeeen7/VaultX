import { io } from 'socket.io-client';

// Connect to backend WebSocket server
// In dev, Vite proxy handles /socket.io; in production, use explicit URL
const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || import.meta.env.VITE_API_URL || 'http://localhost:5001';

export const socket = io(SOCKET_URL, {
  autoConnect: true,
  reconnection: true,
  reconnectionAttempts: 15,
  reconnectionDelay: 2000,
  reconnectionDelayMax: 10000,
  transports: ['websocket', 'polling'],
});

socket.on('connect', () => {
  console.log('[SIEM Socket.IO] Connected to real-time event server.');
});

socket.on('disconnect', () => {
  console.log('[SIEM Socket.IO] Disconnected from event server.');
});

socket.on('connect_error', (err) => {
  console.warn('[SIEM Socket.IO] Connection error:', err.message);
});
