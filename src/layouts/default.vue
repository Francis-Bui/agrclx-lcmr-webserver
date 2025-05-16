<template>
  <v-app>
    <v-main>
      <transition mode="in-out" :name="transitionName">
        <router-view />
      </transition>
    </v-main>

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

  const showManualPopup = ref(false)
  const BACKEND_URL = `http://${window.location.hostname}:8080`
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
  let lockInterval = null

  onMounted(() => {
    if (!isLocal) {
      lockInterval = setInterval(async () => {
        try {
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

  onUnmounted(() => {
    if (lockInterval) clearInterval(lockInterval)
  })

  const route = useRoute()
  const pageOrder = ['/', '/timer', '/data']

  const lastIndex = ref(pageOrder.indexOf(route.path))
  const transitionName = ref('slide-left')

  watch(
    () => route.path,
    (to, from) => {
      const fromIdx = lastIndex.value
      const toIdx = pageOrder.indexOf(to)
      transitionName.value = toIdx > fromIdx ? 'slide-left' : 'slide-right'
      lastIndex.value = toIdx
      console.log('Transition:', transitionName.value)
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

</style>
