<template>
  <v-app>
    <v-main>
      <transition mode="in-out" :name="transitionName">
        <router-view />
      </transition>
    </v-main>

    <!-- Global Alert Bar -->
    <transition name="bounce-fade">
      <div v-if="alert.visible" :class="['alert', alert.type]">
        {{ alert.message }}
      </div>
    </transition>

    <!-- Manual Popup Dialog -->
    <v-dialog v-model="showManualPopup" max-width="320" persistent>
      <v-card class="text-center" color="warning">
        <v-card-title class="text-h6">Manual Interface In Use</v-card-title>
        <v-card-text>
          The touchscreen interface is currently controlling the system.<br>
          Remote control will resume when the touchscreen is inactive for 5 seconds.
        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Bottom Navigation -->
    <v-bottom-navigation
      color="primary"
      grow
      mode="fixed"
      style="border-radius: 0 0 12px 12px;"
    >
      <v-btn :active="$route.path === '/'" icon to="/">
        <v-icon>mdi-lightbulb-outline</v-icon>
        <span>Light</span>
      </v-btn>
      <v-btn :active="$route.path === '/timer'" icon to="/timer">
        <v-icon>mdi-timer-outline</v-icon>
        <span>Timer</span>
      </v-btn>
      <v-btn :active="$route.path === '/data'" icon to="/data">
        <v-icon>mdi-database-outline</v-icon>
        <span>Data</span>
      </v-btn>
    </v-bottom-navigation>

  </v-app>
</template>

<script setup>
  import { onMounted, onUnmounted, ref, watch } from 'vue'
  import { useRoute } from 'vue-router'
  import { useGlobalState } from '@/plugins/globalState.js'

  /*
    default.vue
    -----------
    This layout file provides the main application shell, including:
      - The navigation bar and persistent UI elements
      - The main content area (router-view)
      - Global alert bar for user notifications
      - Manual lockout popup dialog for local/remote control

    All pages are wrapped in this layout for a consistent look and feel across the app.
  */

  // Access global alert state
  const { alert } = useGlobalState()

  // Controls the manual lockout popup dialog
  const showManualPopup = ref(false)
  const BACKEND_URL = `http://${window.location.hostname}:8080`
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  let lockInterval = null

  // Poll backend for lock status every second (only if not local)
  onMounted(() => {
    if (!isLocal) {
      lockInterval = setInterval(async () => {
        try {
          // Query backend for local lock status
          const res = await fetch(`${BACKEND_URL}/api/lock_status`)
          const { local_lock } = await res.json()
          showManualPopup.value = local_lock
        // eslint-disable-next-line no-unused-vars
        } catch (err) {
        // Optionally handle error
        }
      }, 1000)
    }
  })

  // Cleanup polling interval on component unmount
  onUnmounted(() => {
    if (lockInterval) clearInterval(lockInterval)
  })

  // Handle page transitions for bottom navigation
  const route = useRoute()
  const pageOrder = ['/', '/timer', '/data']
  const lastIndex = ref(pageOrder.indexOf(route.path))
  const transitionName = ref('slide-left')

  // Watch for route changes to determine transition direction
  watch(
    () => route.path,
    to => {
      const fromIdx = lastIndex.value
      const toIdx = pageOrder.indexOf(to)
      transitionName.value = toIdx > fromIdx ? 'slide-left' : 'slide-right'
      lastIndex.value = toIdx
    }
  )
</script>

<style>

.page-root {
  width: 100vw;
  height: 100vh;
  min-height: 100vh;
  position: absolute;
  top: 0;
  left: 0;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-bottom: 70px;
}

.v-main {
  position: relative;
  overflow: hidden;
}

.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  position: fixed !important;
  width: 100vw;
  height: 100vh;
  top: 0;
  left: 0;
  transition: transform 0.5s cubic-bezier(.77,0,.175,1) !important;
  z-index: 1;
  background: #fff;
  will-change: transform;
}
.slide-left-enter-from,
.slide-right-leave-to {
  transform: translateX(100%) !important;
}
.slide-left-leave-to,
.slide-right-enter-from {
  transform: translateX(-100%) !important;
}
.slide-right-enter-from,
.slide-left-leave-to {
  transform: translateX(-100%) !important;
}

.alert {
  position: fixed;
  left: 50%;
  bottom: 90px;
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

</style>
