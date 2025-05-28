<template>
  <div class="page-root data-page-root">
    <!-- Floating Save/Load/Reset Buttons -->
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
    <v-btn
      class="profile-fab reset-fab"
      color="blue darken-2"
      :disabled="lockStatus.local_lock"
      elevation="8"
      icon
      rounded
      style="position:fixed;bottom:70px;right:40px;z-index:20;"
      @click="resetSliders"
    >
      <v-icon :class="{ 'spin': resetSpinning }">mdi-restore</v-icon>
    </v-btn>

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
              <!-- Delete icon: middle left -->
              <v-btn
                class="profile-action-btn profile-action-btn-delete"
                color="error"
                icon
                style="position:absolute;top:50%;transform:translateY(-50%);z-index:2;"
                variant="tonal"
                @click.stop="handleDeleteProfile(profile)"
              >
                <v-icon>mdi-delete</v-icon>
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
  import { onMounted, onUnmounted, reactive, ref } from 'vue'
  import { useGlobalState } from '@/plugins/globalState.js'
  import { io } from 'socket.io-client'

  /*
    index.vue
    ---------
    This is the main control page for the lighting system. It provides:
      - Vertical sliders for each light channel (IR, Red, Green, Blue, White, UV)
      - Floating action buttons for saving/loading/resetting profiles
      - Dialogs for profile management with previews
      - Real-time updates via WebSocket for multi-client sync
      - Animated alerts and a modern, responsive UI

    All state is synchronized with the backend and other clients for a seamless experience.
  */

  // Light channel names
  const chips = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
  const BACKEND_URL = `http://${window.location.hostname}:8080`
  const lockStatus = reactive({ local_lock: false })

  // Reactive slider values for each channel
  const sliderValues = reactive({
    IR: 0,
    Red: 0,
    Green: 0,
    Blue: 0,
    White: 0,
    UV: 0,
  })

  // Color mapping for each channel
  const chipColors = {
    IR: '#b71c1c',
    Red: '#ff5252',
    Green: '#4caf50',
    Blue: '#2196f3',
    White: '#bdbdbd',
    UV: '#7c4dff',
  }

  // Use global state composable for profiles, alerts, and CRUD
  const {
    profiles,
    alert,
    fetchProfiles,
    createProfile,
    deleteProfile,
    showAlert,
  } = useGlobalState()

  // Dialog state for save/load dialogs
  const dialogs = reactive({ save: false, load: false })
  const profileName = ref('')

  // Reset button animation state
  const resetSpinning = ref(false)
  function resetSliders () {
    if (lockStatus.local_lock) return
    // Reset all sliders to 0
    Object.keys(sliderValues).forEach(k => sliderValues[k] = 0)
    sendSlidersToBackend()
    resetSpinning.value = true
    setTimeout(() => { resetSpinning.value = false }, 700)
    showAlert('All lights reset to 0%', 'success')
  }

  // WebSocket connection for real-time updates
  const socket = ref(null)

  onMounted(() => {
    // Connect to backend WebSocket
    socket.value = io(BACKEND_URL)
    socket.value.on('connect', () => {
      // Optionally show connection status
    })
    // Listen for lighting updates from backend
    socket.value.on('slider_update', data => {
      if (data && Array.isArray(data.lighting)) {
        const order = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
        order.forEach((k, i) => {
          sliderValues[k] = data.lighting[i]
        })
      }
    })
    // On connect, request current state
    socket.value.emit('get_state')
  })

  onUnmounted(() => {
    // Disconnect WebSocket on component unmount
    if (socket.value) {
      socket.value.disconnect()
      socket.value = null
    }
  })

  // Open/close save dialog
  function openSaveDialog () {
    profileName.value = ''
    dialogs.save = true
  }
  function closeSaveDialog () {
    dialogs.save = false
  }
  // Open/close load dialog
  function openLoadDialog () {
    fetchProfiles(BACKEND_URL) // Only fetch when dialog opens
    dialogs.load = true
  }
  function closeLoadDialog () {
    dialogs.load = false
  }

  // Save a new profile to backend
  async function saveProfile () {
    const payload = {
      name: profileName.value,
      values: chips.map(k => Number(sliderValues[k]) || 0),
    }
    await createProfile(payload, BACKEND_URL)
    fetchProfiles(BACKEND_URL) // Refresh after create
    dialogs.save = false
  }

  // Load a profile's values into the sliders
  function selectProfile (profile) {
    chips.forEach((k, i) => (sliderValues[k] = profile.values[i]))
    sendSlidersToBackend()
    dialogs.load = false
    showAlert('Profile loaded!', 'success')
  }

  // Delete a profile from backend
  async function handleDeleteProfile (profile) {
    await deleteProfile(profile.name, BACKEND_URL)
    fetchProfiles(BACKEND_URL) // Refresh after delete
  }

  // Send current slider values to backend
  function sendSlidersToBackend () {
    fetch(`${BACKEND_URL}/api/state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lighting: getLightingArrayFromSliders() }),
    })
  }

  // Called when a slider is changed
  function onSliderChange () {
    sendSlidersToBackend()
    // Do not update UI here; wait for WebSocket event
  }

  // Get slider values as array in backend order
  function getLightingArrayFromSliders () {
    const order = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
    return order.map(k => Number(sliderValues[k]) || 0)
  }

  // Compute box shadow and animation for slider based on value
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
.reset-fab {
  background: #1976d2 !important;
  color: #fff !important;
  border-radius: 16px !important;
  width: 56px;
  height: 56px;
  box-shadow: 0 4px 16px rgba(0,0,0,0.18);
  display: flex;
  align-items: center;
  justify-content: center;
}
.spin {
  animation: spin 0.2s ease-in-out;
}
@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
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

.profile-title-center {
  text-align: center;
  width: 100%;
  font-weight: bold;
  font-size: 1.1em;
  margin-bottom: 2px;
  margin-top: 2px;
}
</style>
