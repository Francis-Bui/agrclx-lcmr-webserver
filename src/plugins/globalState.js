import { ref, reactive, computed, watch } from 'vue'

// Singleton state
const schedules = ref([])
const profiles = ref([])
const alert = reactive({ visible: false, message: '', type: 'success', timeout: 3000 })
const isRemoteClient = ref(true) // Set this based on your app's logic if needed
let pollInterval = null
let pingInterval = null
let remotePingInterval = null
let remoteCheckInterval = null

function showAlert(message, type = 'success', timeout = 3000) {
  alert.message = message
  alert.type = type
  alert.visible = true
  alert.timeout = timeout
  setTimeout(() => { alert.visible = false }, timeout)
}

async function fetchSchedules(BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules`)
    if (!res.ok) throw new Error('Failed to fetch schedules')
    schedules.value = await res.json()
  } catch (e) {
    showAlert('Failed to fetch schedules', 'error')
  }
}

async function fetchProfiles(BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles`)
    if (!res.ok) throw new Error('Failed to fetch profiles')
    const data = await res.json()
    profiles.value = data.profiles || []
  } catch (e) {
    showAlert('Failed to fetch profiles', 'error')
  }
}

async function createSchedule(schedule, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(schedule),
    })
    if (!res.ok) throw new Error('Failed to create schedule')
    await fetchSchedules(BACKEND_URL)
  } catch (e) {
    showAlert('Failed to create schedule', 'error')
  }
}

async function updateSchedule(schedule, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules/${schedule.id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(schedule),
    })
    if (!res.ok) throw new Error('Failed to update schedule')
    await fetchSchedules(BACKEND_URL)
  } catch (e) {
    showAlert('Failed to update schedule', 'error')
  }
}

async function deleteSchedule(id, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/schedules/${id}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete schedule')
    await fetchSchedules(BACKEND_URL)
  } catch (e) {
    showAlert('Failed to delete schedule', 'error')
  }
}

// Profile CRUD (implement as needed, similar to schedules)
async function createProfile(profile, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })
    if (!res.ok) throw new Error('Failed to create profile')
    await fetchProfiles(BACKEND_URL)
  } catch (e) {
    showAlert('Failed to create profile', 'error')
  }
}

async function updateProfile(profile, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles/${profile.name}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })
    if (!res.ok) throw new Error('Failed to update profile')
    await fetchProfiles(BACKEND_URL)
  } catch (e) {
    showAlert('Failed to update profile', 'error')
  }
}

async function deleteProfile(name, BACKEND_URL) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/profiles/${name}`, { method: 'DELETE' })
    if (!res.ok) throw new Error('Failed to delete profile')
    await fetchProfiles(BACKEND_URL)
  } catch (e) {
    showAlert('Failed to delete profile', 'error')
  }
}

// Each client uses a unique index (0-4) for up to 5 clients
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

function isRemoteClientPresent () {
  const now = Date.now()
  const remotePing = localStorage.getItem('data_vue_remote_ping')
  return remotePing && now - Number(remotePing) < 2200
}

function updateRemotePing () {
  if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
    localStorage.setItem('data_vue_remote_ping', Date.now())
  }
}

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

if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', stopPolling)
}

export function useGlobalState() {
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
