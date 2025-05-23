<template>
  <v-container class="fill-height d-flex align-center justify-center data-page-root">
    <div class="data-main-layout">
      <!-- Left: Selection Card -->
      <v-card class="data-selection-card" elevation="8" rounded="xl">
        <div class="data-selection-list">
          <v-btn
            v-for="item in selectionOptions"
            :key="item.key"
            block
            class="data-selection-pill-btn"
            :color="item.checked ? 'primary' : '#e0e0e0'"
            :elevation="item.checked ? 8 : 4"
            rounded="pill"
            style="display: flex; align-items: center; justify-content: center; position: relative; min-height: 44px; font-weight: 600; font-size: 1.1em; box-shadow: 0 2px 8px rgba(0,0,0,0.10);"
            :variant="item.checked ? 'elevated' : 'flat'"
            @click="item.checked = !item.checked"
          >
            <span v-if="item.checked" class="checkmark-wrapper">
              <v-icon start style="position: absolute; left: 16px; top: 50%; transform: translateY(-50%);">mdi-check</v-icon>
            </span>
            <span class="btn-label-flex"><span class="btn-label">{{ item.label }}</span></span>
          </v-btn>
        </div>
      </v-card>

      <!-- Center: Main Data Card -->
      <v-card class="data-graph-card" elevation="12" rounded="xl">
        <div class="data-graph-header" style="overflow: visible;">
          <v-btn
            class="data-date-btn"
            color="primary"
            elevation="6"
            rounded
            @click="datePickerDialog = true"
          >
            <v-icon>mdi-calendar</v-icon>
            <span class="ml-2">{{ selectedDateLabel }}</span>
          </v-btn>
          <v-btn
            class="data-interval-btn ml-auto"
            color="primary"
            elevation="4"
            rounded
            style="margin-left:auto;"
            @click="cycleIntervalMode"
          >
            {{ intervalModeLabel }}
          </v-btn>
        </div>
        <div class="data-graph-content">
          <template v-if="filteredData.length > 0">
            <v-sheet class="stackSheet" color="white" style="position:relative; width:320px; min-height:90px;">
              <v-sparkline
                v-for="color in selectedLedColors"
                :key="color.key"
                :color="color.color"
                :height="90"
                :line-width="2"
                :model-value="getColorDisplayData(getPaddedColorData(color.key), color.key)"
                :padding="16"
                :smooth="smooth"
                style="position:absolute; top:0; left:0;"
                :width="320"
              />
            </v-sheet>
            <!-- Dynamic label row below the sparklines -->
            <div class="data-graph-dynamic-labels" style="width:320px; text-align:center; margin-top:8px; font-size:0.98em; color:#555;">
              {{ getDynamicLabelText() }}
            </div>
          </template>
          <template v-else>
            <div class="data-graph-empty">No data for this period.</div>
          </template>
        </div>
        <div class="data-graph-nav">
          <v-btn icon rounded @click="navigateHistory(-1)"><v-icon>mdi-chevron-left</v-icon></v-btn>
          <v-btn icon rounded @click="navigateHistory(1)"><v-icon>mdi-chevron-right</v-icon></v-btn>
        </div>
      </v-card>
    </div>

    <!-- Bottom: LED Color Selection Card -->
    <v-card class="data-led-color-card" elevation="8" rounded="xl">
      <div class="data-led-color-row">
        <div
          v-for="color in ledColors"
          :key="color.key"
          class="data-led-color-square"
          :style="getLedSquareStyle(color)"
          @mousedown="onLedColorHold(color.key)"
          @mouseleave="onLedColorRelease"
          @mouseup="onLedColorRelease"
        />
      </div>
    </v-card>

    <!-- Date Picker Dialog -->
    <v-dialog v-model="datePickerDialog" max-width="340">
      <v-date-picker
        v-model="selectedDate"
        :allowed-dates="allowedDates"
        color="primary"
        scrollable
        @change="onDateChange"
      />
    </v-dialog>
  </v-container>
</template>

<script setup>
  import { computed, onMounted, reactive, ref } from 'vue'
  import { useGlobalState } from '@/plugins/globalState'
  // REMOVED: import Vue3Sparklines from 'vue3-sparklines'

  const { showAlert } = useGlobalState()

  // Data selection options (expandable in future)
  const selectionOptions = reactive([
    { key: 'led', label: 'LED', checked: true },
    { key: 'motion', label: 'Motion', checked: false },
    { key: 'events', label: 'Events', checked: false },
  ])

  // LED color options
  const ledColors = [
    { key: 'IR', color: '#b71c1c' },
    { key: 'R', color: '#ff5252' },
    { key: 'G', color: '#4caf50' },
    { key: 'B', color: '#2196f3' },
    { key: 'W', color: '#bdbdbd' },
    { key: 'UV', color: '#7c4dff' },
  ]

  // Only show sparklines for selected LED colors
  const selectedLedColors = computed(() => {
    if (heldLedColor.value) {
      return ledColors.filter(c => c.key === heldLedColor.value)
    }
    return ledColors.filter(c => c.selected !== false)
  })

  const heldLedColor = ref(null)
  const faded = ref(false)

  function onLedColorHold (key) {
    heldLedColor.value = key
    faded.value = true
  }
  function onLedColorRelease () {
    heldLedColor.value = null
    faded.value = false
  }

  // Date picker state
  const datePickerDialog = ref(false)
  const selectedDate = ref(null)
  const availableDates = ref([])
  const selectedDateLabel = computed(() => selectedDate.value || 'Select Date')

  // --- INTERVAL & NAVIGATION LOGIC ---
  const intervalModes = ['hour', 'day', 'week', 'month']
  const intervalMode = ref('hour') // Make hour the default
  const intervalModeLabel = computed(() => intervalMode.value.charAt(0).toUpperCase() + intervalMode.value.slice(1))

  function cycleIntervalMode () {
    const idx = intervalModes.indexOf(intervalMode.value)
    intervalMode.value = intervalModes[(idx + 1) % intervalModes.length]
    historyIndex.value = 0 // reset navigation on mode change
  }

  const historyIndex = ref(0)
  const maxHistoryIndex = computed(() => {
    if (!ledHistory.value.length || !selectedDate.value) return 0
    const all = ledHistory.value.filter(row => row.timestamp.startsWith(selectedDate.value))
    if (intervalMode.value === 'hour') {
      // How many full hours are in the data for this day?
      const hours = [...new Set(all.map(row => new Date(row.timestamp).getHours()))]
      return Math.max(0, hours.length - 1)
    } else if (intervalMode.value === 'day') {
      // How many days in the month?
      return 0 // navigation not used for day
    } else if (intervalMode.value === 'week') {
      // Number of weeks in data
      return Math.max(0, Math.floor(all.length / (7 * 24 * 6)) - 1)
    } else if (intervalMode.value === 'month') {
      // Only one month at a time
      return 0
    }
    return 0
  })
  function navigateHistory (dir) {
    historyIndex.value -= dir // Reverse direction: +1 is forward in time
    if (historyIndex.value < 0) historyIndex.value = 0
    if (historyIndex.value > maxHistoryIndex.value) historyIndex.value = maxHistoryIndex.value
  }

  // --- INTERVAL DATA SLICING & LABELS ---
  const filteredData = computed(() => {
    if (!ledHistory.value.length || !selectedDate.value) return []
    const all = ledHistory.value.filter(row => row.timestamp.startsWith(selectedDate.value))
    if (!all.length) return []
    let groups = []
    if (intervalMode.value === 'hour') {
      const last = new Date(all[all.length - 1].timestamp)
      let hour = last.getHours() - historyIndex.value
      if (hour < 0) hour = 0
      groups = all.filter(row => new Date(row.timestamp).getHours() === hour)
    } else if (intervalMode.value === 'day') {
      groups = all
    } else if (intervalMode.value === 'week') {
      const baseDate = new Date(selectedDate.value)
      const weekStart = new Date(baseDate)
      weekStart.setDate(baseDate.getDate() - baseDate.getDay() + 1 - 7 * historyIndex.value)
      weekStart.setHours(0,0,0,0)
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekStart.getDate() + 7)
      groups = all.filter(row => {
        const d = new Date(row.timestamp)
        return d >= weekStart && d < weekEnd
      })
    } else if (intervalMode.value === 'month') {
      const baseDate = new Date(selectedDate.value)
      const month = baseDate.getMonth()
      groups = all.filter(row => new Date(row.timestamp).getMonth() === month)
    }
    return groups
  })

  // Helper to get display data for a specific color, handling heldLedColor/fading
  function getColorDisplayData (arr, colorKey) {
    // If a color is being held, only show that color, others are faded (null)
    if (heldLedColor.value && heldLedColor.value !== colorKey) {
      return arr.map(() => null)
    }
    return arr
  }

  // LED history data
  const ledHistory = ref([])

  function getLedSquareStyle (color) {
    return {
      background: color.color,
      opacity: heldLedColor.value && heldLedColor.value !== color.key ? 0.2 : 1,
      filter: heldLedColor.value && heldLedColor.value !== color.key ? 'grayscale(0.7)' : '',
      transition: 'opacity 0.2s, filter 0.2s',
      borderRadius: '6px',
      width: '36px',
      height: '36px',
      margin: '0 12px',
      cursor: 'pointer',
      boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
      border: heldLedColor.value === color.key ? '2px solid #1976d2' : 'none',
    }
  }

  function allowedDates (date) {
    // Only allow dates present in the CSV
    return availableDates.value.includes(date)
  }

  function onDateChange (val) {
    selectedDate.value = val
    datePickerDialog.value = false
  }

  // Fetch LED history from backend
  async function fetchLedHistory () {
    try {
      const res = await fetch('/api/logs/led_history')
      if (!res.ok) throw new Error('Failed to fetch LED history')
      const data = await res.json()
      ledHistory.value = data.history || []
      // Extract available dates
      availableDates.value = [...new Set(ledHistory.value.map(row => row.timestamp.split('T')[0]))]
      if (!selectedDate.value && availableDates.value.length > 0) {
        selectedDate.value = availableDates.value[availableDates.value.length - 1]
      }
    } catch {
      showAlert('Failed to load LED history', 'error')
    }
  }

  onMounted(() => {
    fetchLedHistory()
  })

  // Add getDynamicLabelText helper
  function getDynamicLabelText () {
    if (!filteredData.value.length) return ''
    const first = filteredData.value[0]
    const last = filteredData.value[filteredData.value.length - 1]
    if (!first || !last || !first.timestamp || !last.timestamp) return ''
    const d1 = new Date(first.timestamp)
    const d2 = new Date(last.timestamp)
    if (intervalMode.value === 'hour') {
      return d1.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }) + ' - ' + d2.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' })
    } else if (intervalMode.value === 'day') {
      return d1.toLocaleDateString() + ' (' + d1.toLocaleTimeString([], { hour: 'numeric', hour12: true }) + ' - ' + d2.toLocaleTimeString([], { hour: 'numeric', hour12: true }) + ')'
    } else if (intervalMode.value === 'week') {
      return d1.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' }) + ' - ' + d2.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })
    } else if (intervalMode.value === 'month') {
      return d1.toLocaleDateString([], { month: 'long', year: 'numeric' })
    }
    return ''
  }
</script>

<style scoped>
.data-page-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding-top: 48px;
  padding-bottom: 80px;
}
.data-main-layout {
  display: flex;
  flex-direction: row;
  gap: 32px;
  margin-bottom: 32px;
}
.data-selection-card {
  min-width: 220px;
  max-width: 260px;
  width: 240px;
  padding: 24px 0 24px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
}
.data-selection-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 0 16px;
  align-items: center; /* Center the buttons horizontally */
}
.data-selection-pill {
  background: #f3f3f3;
  border-radius: 32px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  padding: 0 18px 0 0;
  display: flex;
  align-items: center;
  min-height: 44px;
  width: 100%;
}
.data-selection-checkbox {
  margin-left: 8px;
  width: 100%;
}
.data-graph-card {
  min-width: 380px;
  max-width: 420px;
  width: 400px;
  padding: 24px 24px 16px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  overflow: visible; /* Fix calendar button shadow clipping */
}
.data-graph-header {
  width: 100%;
  display: flex;
  flex-direction: row;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 8px;
  overflow: visible; /* Fix calendar button shadow clipping */
}
.data-date-btn {
  border-radius: 18px !important;
  font-weight: 500;
  font-size: 1em;
  padding: 0 18px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  min-width: 0;
}
.data-graph-content {
  width: 100%;
  min-height: 90px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.data-graph-empty {
  color: #888;
  font-size: 1.1em;
  text-align: center;
  padding: 24px 0;
}
.data-graph-controls {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}
.data-interval-toggle {
  border-radius: 24px !important;
  background: #f3f3f3;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  padding: 2px 8px;
}
.data-graph-nav {
  width: 100%;
  display: flex;
  flex-direction: row;
  justify-content: center;
  gap: 24px;
  margin-top: 4px;
}
.data-led-color-card {
  width: 700px;
  max-width: 98vw;
  margin: 0 auto;
  margin-top: 12px;
  padding: 18px 0 18px 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.data-led-color-row {
  width: 100%;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: space-evenly;
  gap: 0;
}
.data-led-color-square {
  border-radius: 6px;
  width: 36px;
  height: 36px;
  margin: 0 12px;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  transition: opacity 0.2s, filter 0.2s;
}
.data-selection-pill-btn {
  position: relative;
  color: #222;
  background: #f3f3f3;
  /* Remove left padding, handled by label if needed */
  padding-left: 0 !important;
}
.data-selection-pill-btn[aria-pressed="false"] {
  color: #222 !important;
  background: #f3f3f3 !important;
}
.data-selection-pill-btn[aria-pressed="true"] {
  color: #fff !important;
}
.data-selection-pill-btn .v-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
}
.btn-label-flex {
  display: flex;
  width: 100%;
  justify-content: center;
  align-items: center;
  position: relative;
}
.btn-label {
  width: 100%;
  text-align: center;
  color: inherit;
  z-index: 1;
}
.data-interval-btn {
  min-width: 80px;
  max-width: 100px;
  width: 100px;
  justify-content: center;
}
</style>
