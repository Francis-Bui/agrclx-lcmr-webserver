<template>
  <div class="page-root data-page-root">
    <!-- Floating Save/Load Buttons -->
    <div class="profile-fab-group">
      <v-btn
        class="profile-fab save"
        color="success"
        :disabled="lockStatus.local_lock"
        elevation="8"
        icon
        rounded
        @click="openSaveDialog"
      >
        <v-icon>mdi-content-save</v-icon>
      </v-btn>
      <v-btn
        class="profile-fab load"
        color="primary"
        elevation="8"
        icon
        rounded
        @click="openLoadDialog"
      >
        <v-icon>mdi-folder-open</v-icon>
      </v-btn>
    </div>

    <v-container
      class="d-flex flex-row justify-center align-center flex-wrap"
      style="gap: 48px;"
    >
      <div v-for="chip in chips" :key="chip" class="slider-stack">
        <div
          class="slider-box"
          :style="{ boxShadow: getBoxStyle(chip).boxShadow, animation: getBoxStyle(chip).animation, margin: '0 16px' }"
        >
          <v-slider
            v-model="sliderValues[chip]"
            class="my-slider"
            :color="chipColors[chip]"
            direction="vertical"
            :disabled="lockStatus.local_lock"
            hide-details
            :max="100"
            :min="0"
            :step="1"
            thumb-label="focus"
            :thumb-size="32"
            :track-color="chipColors[chip]"
            :track-size="12"
            @update:model-value="onSliderChange"
          />
        </div>
        <div class="slider-label">{{ chip }}</div>
      </div>
    </v-container>

    <!-- Save Profile Dialog -->
    <v-dialog v-model="dialogs.save" max-width="400" persistent>
      <v-card>
        <v-card-title>Save Profile</v-card-title>
        <v-card-text>
          <v-text-field v-model="profileName" autofocus label="Profile Name" :rules="[v => !!v || 'Name required']" />
          <div class="profile-preview profile-preview-center">
            <div
              v-for="chip in chips"
              :key="chip"
              class="profile-bar-mini"
              :style="{ background: chipColors[chip], height: sliderValues[chip] + '%', opacity: 0.8 }"
            />
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn color="primary" :disabled="!profileName" @click="saveProfile">Save</v-btn>
          <v-btn text @click="closeSaveDialog">Cancel</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Load Profile Dialog -->
    <v-dialog v-model="dialogs.load" max-width="600" persistent>
      <v-card>
        <v-card-title>Load Profile</v-card-title>
        <v-card-text>
          <v-list>
            <v-list-item
              v-for="profile in profiles"
              :key="profile.name"
              class="profile-list-item profile-list-item-rounded"
              :disabled="lockStatus.local_lock"
              elevation="4"
              style="max-width:340px;margin:16px auto 0 auto;position:relative;"
              @click="selectProfile(profile)"
            >
              <v-list-item-content>
                <v-list-item-title class="profile-title-center">{{ profile.name }}</v-list-item-title>
                <div class="profile-preview profile-preview-center">
                  <div
                    v-for="(val, idx) in profile.values"
                    :key="chips[idx]"
                    class="profile-bar-mini"
                    :style="{ background: chipColors[chips[idx]], height: val + '%', opacity: 0.8 }"
                  />
                </div>
              </v-list-item-content>
              <!-- Delete icon: bottom left, Edit icon: bottom right -->
              <v-btn
                class="profile-action-btn profile-action-btn-delete"
                color="error"
                icon
                style="position:absolute;bottom:8px;left:8px;z-index:2;"
                variant="tonal"
                @click.stop="deleteProfile(profile)"
              >
                <v-icon>mdi-delete</v-icon>
              </v-btn>
              <v-btn
                class="profile-action-btn profile-action-btn-edit"
                color="primary"
                icon
                style="position:absolute;bottom:8px;right:8px;z-index:2;"
                variant="tonal"
                @click.stop="editProfile(profile)"
              >
                <v-icon>mdi-pencil</v-icon>
              </v-btn>
            </v-list-item>
          </v-list>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn text @click="closeLoadDialog">Close</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Animated Alert -->
    <transition name="bounce-fade">
      <div v-if="alert.show" :class="['alert', alert.type]">
        {{ alert.message }}
      </div>
    </transition>
  </div>
</template>

<script setup>
  import { onUnmounted, reactive, ref } from 'vue'

  const chips = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
  const BACKEND_URL = `http://${window.location.hostname}:8080`
  const lockStatus = reactive({ local_lock: false })

  const sliderValues = reactive({
    IR: 0,
    Red: 0,
    Green: 0,
    Blue: 0,
    White: 0,
    UV: 0,
  })

  const chipColors = {
    IR: '#b71c1c', // Dark red
    Red: '#ff5252',
    Green: '#4caf50',
    Blue: '#2196f3',
    White: '#bdbdbd', // Light grey for white bar
    UV: '#7c4dff',
  }

  // Profile system
  const dialogs = reactive({ save: false, load: false })
  const profiles = ref([])
  const profileName = ref('')
  const editingProfile = ref(null)

  // Alert system
  const alert = reactive({ show: false, message: '', type: 'success' })
  let alertTimeout = null
  function showAlert (msg, type = 'success') {
    alert.message = msg
    alert.type = type
    alert.show = true
    if (alertTimeout) clearTimeout(alertTimeout)
    alertTimeout = setTimeout(() => (alert.show = false), 2200)
  }

  function openSaveDialog () {
    profileName.value = editingProfile.value ? editingProfile.value.name : ''
    dialogs.save = true
  }
  function closeSaveDialog () {
    dialogs.save = false
    editingProfile.value = null
  }
  function openLoadDialog () {
    fetchProfiles()
    dialogs.load = true
  }
  function closeLoadDialog () {
    dialogs.load = false
    editingProfile.value = null
  }

  function saveProfile () {
    const payload = {
      name: profileName.value,
      values: chips.map(k => Number(sliderValues[k]) || 0),
    }
    const method = editingProfile.value ? 'PUT' : 'POST'
    fetch(`${BACKEND_URL}/api/profiles`, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async res => {
        if (res.ok) {
          showAlert(editingProfile.value ? 'Profile updated!' : 'Profile saved!', 'success')
          fetchProfiles()
          dialogs.save = false
          editingProfile.value = null
        } else if (res.status === 409) {
          showAlert('Profile name already exists!', 'warning')
        } else {
          showAlert('Failed to save profile', 'error')
        }
      })
  }

  function fetchProfiles () {
    fetch(`${BACKEND_URL}/api/profiles`)
      .then(res => res.json())
      .then(data => {
        profiles.value = data.profiles || []
      })
  }

  function selectProfile (profile) {
    // Load profile values into sliders
    chips.forEach((k, i) => (sliderValues[k] = profile.values[i]))
    sendSlidersToBackend()
    dialogs.load = false
    showAlert('Profile loaded!', 'success')
  }

  function editProfile (profile) {
    editingProfile.value = profile
    profileName.value = profile.name
    chips.forEach((k, i) => (sliderValues[k] = profile.values[i]))
    dialogs.load = false
    dialogs.save = true
  }

  function deleteProfile (profile) {
    fetch(`${BACKEND_URL}/api/profiles`, {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: profile.name }),
    })
      .then(async res => {
        if (res.ok) {
          showAlert('Profile deleted!', 'success')
          fetchProfiles()
        } else {
          showAlert('Failed to delete profile', 'error')
        }
      })
  }

  function sendSlidersToBackend () {
    fetch(`${BACKEND_URL}/api/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lighting: getLightingArrayFromSliders() }),
    })
  }

  function onSliderChange () {
    sendSlidersToBackend()
  }

  function getLightingArrayFromSliders () {
    const order = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
    return order.map(k => Number(sliderValues[k]) || 0)
  }

  // Live state polling logic: only poll if a remote (non-localhost) client is present
  const pollInterval = ref(null)

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

  updateClientPing()
  const pingInterval = setInterval(() => {
    updateClientPing()
  }, 1000)

  // Only poll state if a remote client is detected (not localhost)
  function isRemoteClientPresent () {
    // Use a localStorage key to indicate remote presence
    // Each remote client sets 'data_vue_remote_ping' every second
    // Localhost does not set this key
    const now = Date.now()
    const remotePing = localStorage.getItem('data_vue_remote_ping')
    return remotePing && now - Number(remotePing) < 2200
  }

  function updateRemotePing () {
    // Only set if not localhost
    if (window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
      localStorage.setItem('data_vue_remote_ping', Date.now())
    }
  }

  // Set remote ping if this is a remote client
  updateRemotePing()
  const remotePingInterval = setInterval(() => {
    updateRemotePing()
  }, 1000)

  function startPollingState () {
    if (pollInterval.value) return
    pollInterval.value = setInterval(async () => {
      try {
        const res = await fetch(`${BACKEND_URL}/api/state`)
        const data = await res.json()
        if (data.lighting) {
          const order = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
          order.forEach((k, i) => {
            sliderValues[k] = data.lighting[i]
          })
        }
      } catch {
        // ignore
      }
    }, 1000)
  }
  function stopPollingState () {
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
  }

  // Check for remote client presence and poll accordingly
  const remoteCheckInterval = setInterval(() => {
    if (isRemoteClientPresent()) {
      startPollingState()
    } else {
      stopPollingState()
    }
  }, 1200)

  onUnmounted(() => {
    if (pollInterval.value) clearInterval(pollInterval.value)
    if (pingInterval) clearInterval(pingInterval)
    if (remotePingInterval) clearInterval(remotePingInterval)
    if (remoteCheckInterval) clearInterval(remoteCheckInterval)
  })

  function getBoxStyle (chip) {
    const color = chipColors[chip]
    const intensity = sliderValues[chip] / 100
    const auraAlpha = intensity
    let boxShadow = ''
    if (chip === 'White') {
      boxShadow = `
      0 0 ${30 + 40 * intensity}px 10px rgba(224,224,224,${auraAlpha}),
      0 0 ${60 + 60 * intensity}px 20px rgba(255,255,255,${auraAlpha * 0.7})
    `
    } else {
      function hexToRgb (hex) {
        hex = hex.replace('#', '')
        if (hex.length === 3) hex = hex.split('').map(x => x + x).join('')
        const num = parseInt(hex, 16)
        return [(num >> 16) & 255, (num >> 8) & 255, num & 255]
      }
      const [r, g, b] = hexToRgb(color)
      boxShadow = `
      0 0 ${30 + 40 * intensity}px 10px rgba(${r},${g},${b},${auraAlpha}),
      0 0 ${60 + 60 * intensity}px 20px rgba(${r},${g},${b},${auraAlpha * 0.7}),
      0 0 ${90 + 80 * intensity}px 30px rgba(${r},${g},${b},${auraAlpha * 0.4})
    `
    }
    // Add strong elevation
    boxShadow += ', 0 8px 32px 0 rgba(0,0,0,0.22), 0 2px 8px rgba(0,0,0,0.12)';
    return {
      boxShadow,
      animation: `pulse 1.2s infinite alternate`,
    }
  }
</script>

<style scoped>
.data-page-root {
  padding-bottom: 80px; /* for nav bar */
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
}

.slider-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.slider-box {
  margin: 0 8px;
  overflow: visible;
  background: #fff;
  border-radius: 24px;
  box-shadow: 0 8px 32px 0 rgba(0,0,0,0.22), 0 2px 8px rgba(0,0,0,0.12);
  height: 500px;
  width: 60px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: 24px;
  padding-bottom: 24px;
  position: relative;
  transition: box-shadow 0.3s, background 0.3s;
  touch-action: none;
}

.my-slider {
  width: 100%;
  height: 100%;
  min-height: 0;
  display: block;
}

.slider-label {
  text-align: center;
  font-weight: bold;
  margin-top: 8px;
  color: #333;
  font-size: 1.1em;
  letter-spacing: 1px;
}

.profile-bar {
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
  gap: 24px;
  margin-top: 32px;
  margin-bottom: 8px;
}

.profile-preview {
  display: flex;
  flex-direction: row;
  align-items: flex-end;
  height: 36px;
  gap: 2px;
  margin-top: 8px;
  margin-bottom: 4px;
}
.profile-bar-mini {
  width: 10px;
  border-radius: 3px 3px 0 0;
  transition: height 0.3s;
  /* Remove border for white bar, always use color */
}

.alert {
  position: fixed;
  left: 50%;
  bottom: 32px;
  transform: translateX(-50%);
  min-width: 220px;
  max-width: 90vw;
  padding: 16px 32px;
  border-radius: 12px;
  font-weight: bold;
  font-size: 1.1em;
  z-index: 9999;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18);
  text-align: center;
  opacity: 0.97;
}
.alert.success { background: #4caf50; color: #fff; }
.alert.error { background: #ff5252; color: #fff; }
.alert.warning { background: #ffb300; color: #333; }

.bounce-fade-enter-active {
  animation: bounce-in 0.5s;
}
.bounce-fade-leave-active {
  animation: fade-out 0.4s;
}
@keyframes bounce-in {
  0% { opacity: 0; transform: translateY(40px) scale(0.9); }
  60% { opacity: 1; transform: translateY(-8px) scale(1.05); }
  100% { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes fade-out {
  0% { opacity: 1; }
  100% { opacity: 0; }
}

@keyframes pulse {
  0% {
    filter: brightness(1);
  }
  100% {
    filter: brightness(1.15);
  }
}

.profile-fab-group {
  position: absolute;
  top: 32px;
  right: 32px;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 16px;
  z-index: 10;
}
.profile-fab {
  width: 56px;
  height: 56px;
  border-radius: 16px !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}
.profile-fab.save {
  background: #43a047 !important;
  color: #fff !important;
}
.profile-fab.load {
  background: #1976d2 !important;
  color: #fff !important;
}
.profile-preview-center {
  justify-content: center;
  align-items: flex-end;
  display: flex;
  margin: 0 auto;
}
.profile-bar-mini.white-outline {
  border: 2px solid #333;
  box-sizing: border-box;
}
.profile-list-item {
  background: #fff;
  border-radius: 18px;
  margin-bottom: 12px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.13);
  transition: box-shadow 0.2s;
  min-width: 0;
  width: 340px;
  max-width: 340px;
  padding: 0 0 0 0;
}
.profile-list-item-rounded {
  border-radius: 24px !important;
}
.profile-list-item:hover {
  box-shadow: 0 8px 32px rgba(0,0,0,0.18);
}
.profile-action-bar {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
  margin-right: 8px;
}
.profile-action-btn {
  min-width: 0;
  width: 40px;
  height: 40px;
  border-radius: 50% !important;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  padding: 0;
}
.profile-action-btn-delete {
  background: #fff !important;
  border: 2px solid #ff5252 !important;
}
.profile-action-btn-edit {
  background: #fff !important;
  border: 2px solid #1976d2 !important;
}
.profile-title-center {
  text-align: center;
  width: 100%;
  font-weight: bold;
  font-size: 1.1em;
  margin-bottom: 2px;
  margin-top: 2px;
}
</style>
