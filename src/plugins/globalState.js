import { reactive, ref } from 'vue'

/*
  globalState.js
  ----------------
  This file provides a global reactive state and utility functions for managing lighting profiles, schedules, and UI alerts in the Vue frontend.
  It centralizes all API interactions with the Flask backend, ensuring reactivity and a single source of truth for the app's data.

  To reduce unnecessary network traffic, the app uses a localStorage-based ping system. Only when a remote client is detected (i.e., another browser tab or device is active),
  does the app start polling the backend for updates (schedules/profiles). This minimizes POST/GET requests and keeps the UI in sync only when needed.
*/

// Singleton state for schedules, profiles, and alerts
const schedules = ref([])
const profiles = ref([])
const alert = reactive({ visible: false, message: '', type: 'success', timeout: 3000 })
const isRemoteClient = ref(true)
let pollInterval = null
let pingInterval = null
let remotePingInterval = null
let remoteCheckInterval = null

// Log an event to event history
export async function logEvent (action, status) {
  try {
    await fetch('/api/logs/event_history', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action, status }),
    })
  } catch {
    // Ignore errors
  }
}

// Show a UI alert with a message and type (success, error, etc.)
function showAlert (message, type = 'success', timeout = 3000) {
  alert.message = message
  alert.type = type
  alert.visible = true
  alert.timeout = timeout
  // Log the alert event
  logEvent(message, type)
  setTimeout(() => { alert.visible = false }, timeout)
}

// Fetch all schedules from the backend and update state
async function fetchSchedules (BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules`)
    if (!res.ok) throw new Error('Failed to fetch schedules')
    const data = await res.json()
    schedules.value = data.schedules || []
    // No alert for successful fetch
  } catch {
    showAlert('Failed to fetch schedules', 'error')
  }
}

// Fetch all profiles from the backend and update state
async function fetchProfiles (BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles`)
    if (!res.ok) throw new Error('Failed to fetch profiles')
    const data = await res.json()
    profiles.value = data.profiles || []
    // No alert for successful fetch
  } catch {
    showAlert('Failed to fetch profiles', 'error')
  }
}

// Create a new schedule via the backend API
async function createSchedule (schedule, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(schedule),
    })
    if (!res.ok) throw new Error('Failed to create schedule')
    await fetchSchedules(BACKEND_URL)
    showAlert('Schedule created', 'success')
  } catch {
    showAlert('Failed to create schedule', 'error')
  }
}

// Update an existing schedule via the backend API
async function updateSchedule (schedule, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(schedule),
    })
    if (!res.ok) throw new Error('Failed to update schedule')
    await fetchSchedules(BACKEND_URL)
    showAlert('Schedule updated', 'success')
  } catch {
    showAlert('Failed to update schedule', 'error')
  }
}

// Delete a schedule by ID via the backend API
async function deleteSchedule (id, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id }),
    })
    if (!res.ok) throw new Error('Failed to delete schedule')
    await fetchSchedules(BACKEND_URL)
    showAlert('Schedule deleted', 'success')
  } catch {
    showAlert('Failed to delete schedule', 'error')
  }
}

// Create a new profile via the backend API
async function createProfile (profile, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })
    if (!res.ok) throw new Error('Failed to create profile')
    await fetchProfiles(BACKEND_URL)
    showAlert('Profile created', 'success')
  } catch {
    showAlert('Failed to create profile', 'error')
  }
}

// Update an existing profile via the backend API
async function updateProfile (profile, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles/${profile.name}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })
    if (!res.ok) throw new Error('Failed to update profile')
    await fetchProfiles(BACKEND_URL)
    showAlert('Profile updated', 'success')
  } catch {
    showAlert('Failed to update profile', 'error')
  }
}

// Delete a profile by name via the backend API
async function deleteProfile (name, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name }),
    })
    if (!res.ok) throw new Error('Failed to delete profile')
    await fetchProfiles(BACKEND_URL)
    showAlert('Profile deleted', 'success')
  } catch {
    showAlert('Failed to delete profile', 'error')
  }
}

// Assign a unique client index (0-4) for up to 5 clients, used for local presence detection
function updateClientPing () {
  const now = Date.now()
  let myIdx = -1
  for (let i = 0; i < 5; i++) {
    const t = localStorage.getItem('data_vue_client_ping_' + i)
    if (!t || now - Number(t) > 2000) {
      myIdx = i
      break
    }
  }
  if (myIdx === -1) myIdx = Math.floor(Math.random() * 5)
  localStorage.setItem('data_vue_client_ping_' + myIdx, now)
  return myIdx
}

// Check if a remote client is present (another device/tab is active)
function isRemoteClientPresent () {
  const now = Date.now()
  const remotePing = localStorage.getItem('data_vue_remote_ping')
  return remotePing && now - Number(remotePing) < 2200
}

// Update the remote ping timestamp (used for remote presence detection)
function updateRemotePing () {
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    localStorage.setItem('data_vue_remote_ping', Date.now())
  }
}

// Start polling schedules/profiles only if a remote client is present
function startPolling (BACKEND_URL) {
  // Setup ping intervals only once
  if (pingInterval || remotePingInterval || remoteCheckInterval) return
  updateClientPing()
  pingInterval = setInterval(() => {
    updateClientPing()
  }, 1000)
  updateRemotePing()
  remotePingInterval = setInterval(() => {
    updateRemotePing()
  }, 1000)
  remoteCheckInterval = setInterval(() => {
    if (isRemoteClientPresent()) {
      if (!pollInterval) {
        pollInterval = setInterval(() => {
          fetchSchedules(BACKEND_URL)
          fetchProfiles(BACKEND_URL)
        }, 1000)
      }
    } else {
      if (pollInterval) {
        clearInterval(pollInterval)
        pollInterval = null
      }
    }
  }, 1200)
}

// Stop all polling and ping intervals (cleanup)
function stopPolling () {
  if (pollInterval) clearInterval(pollInterval)
  if (pingInterval) clearInterval(pingInterval)
  if (remotePingInterval) clearInterval(remotePingInterval)
  if (remoteCheckInterval) clearInterval(remoteCheckInterval)
  pollInterval = null
  pingInterval = null
  remotePingInterval = null
  remoteCheckInterval = null
}

// Ensure polling is stopped when the window unloads
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', stopPolling)
}

// Export the global state and all utility functions for use in components
export function useGlobalState () {
  return {
    schedules,
    profiles,
    alert,
    isRemoteClient,
    fetchSchedules,
    fetchProfiles,
    createSchedule,
    updateSchedule,
    deleteSchedule,
    createProfile,
    updateProfile,
    deleteProfile,
    showAlert,
    startPolling,
    stopPolling,
  }
}
