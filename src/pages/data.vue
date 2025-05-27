<template>
  <div class="page-root">
    <v-container class="fill-height d-flex flex-row align-center justify-center" style="gap:32px;">
      <!-- Left: Selection Card and LED Color Card -->
      <div class="data-left-col">
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
              @click="onSelectionClick(item)"
            >
              <span v-if="item.checked" class="checkmark-wrapper">
                <v-icon start style="position: absolute; left: 16px; top: 50%; transform: translateY(-50%);">mdi-check</v-icon>
              </span>
              <span class="btn-label-flex"><span class="btn-label">{{ item.label }}</span></span>
            </v-btn>
          </div>
        </v-card>
        <!-- LED Color Card below selection card -->
        <v-card class="data-led-color-card" elevation="8" rounded="xl">
          <div class="data-led-color-grid">
            <div
              v-for="color in ledColors"
              :key="color.key"
              class="data-led-color-square"
              :style="getLedSquareStyle(color)"
              @click="toggleLedColor(color.key)"
              @mousedown="onLedColorHold(color.key)"
              @mouseleave="onLedColorRelease"
              @mouseup="onLedColorRelease"
            />
          </div>
        </v-card>
      </div>
      <!-- Center: Main Data Card -->
      <div class="data-center-col">
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
              v-if="!isEventsMode"
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
            <template v-if="isEventsMode">
              <div class="event-log-terminal-light">
                <div class="event-log-list">
                  <div
                    v-for="(row, idx) in eventLog"
                    :key="idx"
                    class="event-log-row-light"
                    :class="{ 'event-log-row-alt-light': idx % 2 === 1 }"
                  >
                    <div class="event-log-timestamp-light">{{ formatEventTimestamp(row.timestamp) }}</div>
                    <div class="event-log-action-light" @click="showPopup(idx, row.action, $event)">
                      <span>{{ truncateAction(row.action) }}</span>
                      <span v-if="row.action && row.action.length > 54" class="event-log-expand-light">▼</span>
                    </div>
                    <div
                      class="event-log-status-light"
                      :class="'event-log-status-' + row.status"
                    >{{ row.status }}</div>
                  </div>
                </div>
                <div v-if="popup.visible" class="event-log-popup" :style="popup.style">
                  <div class="event-log-popup-content">
                    <span>{{ popup.text }}</span>
                    <v-btn class="event-log-popup-close" icon size="small" @click="popup.visible = false"><v-icon>mdi-close</v-icon></v-btn>
                  </div>
                </div>
              </div>
            </template>
            <template
              v-else-if="
                filteredData.length
                  > 0"
            >
              <ApexChart
                height="500"
                :options="chartOptions"
                :series="chartSeries"
                type="line"
                width="880"
              />
            </template>
            <template v-else>
              <div class="data-graph-empty">No data for this period.</div>
            </template>
          </div>
          <div v-if="!isEventsMode" class="data-graph-nav">
            <v-btn icon rounded @click="navigateHistory(-1)"><v-icon>mdi-chevron-left</v-icon></v-btn>
            <v-btn icon rounded @click="navigateHistory(1)"><v-icon>mdi-chevron-right</v-icon></v-btn>
          </div>
        </v-card>
      </div>
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
  </div>
</template>

<script setup>
  import { computed, onMounted, reactive, ref, watch } from 'vue'
  import { useGlobalState } from '@/plugins/globalState'
  import ApexChart from 'vue3-apexcharts'

  const { showAlert } = useGlobalState()

  const selectionOptions = reactive([
    { key: 'led', label: 'LED', checked: true },
    { key: 'motion', label: 'Motion', checked: false },
    { key: 'events', label: 'Events', checked: false },
  ])

  const ledColors = reactive([
    { key: 'IR', color: '#b71c1c', selected: true },
    { key: 'R', color: '#ff5252', selected: true },
    { key: 'G', color: '#4caf50', selected: true },
    { key: 'B', color: '#2196f3', selected: true },
    { key: 'W', color: '#bdbdbd', selected: true },
    { key: 'UV', color: '#7c4dff', selected: true },
  ])

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
  function toggleLedColor (key) {
    const color = ledColors.find(c => c.key === key)
    if (color) color.selected = !color.selected
  }

  const selectedLedColors = computed(() => {
    if (heldLedColor.value) {
      return ledColors.filter(c => c.key === heldLedColor.value)
    }
    return ledColors.filter(c => c.selected !== false)
  })

  const datePickerDialog = ref(false)
  const selectedDate = ref(null)
  const availableDates = ref([])
  const selectedDateLabel = computed(() => selectedDate.value || 'Select Date')

  const intervalModes = ['hour', 'day', 'week', 'month']
  const intervalMode = ref('hour')
  const intervalModeLabel = computed(() => intervalMode.value.charAt(0).toUpperCase() + intervalMode.value.slice(1))

  function cycleIntervalMode () {
    const idx = intervalModes.indexOf(intervalMode.value)
    intervalMode.value = intervalModes[(idx + 1) % intervalModes.length]
    historyIndex.value = 0
  }

  const historyIndex = ref(0)
  const maxHistoryIndex = computed(() => {
    if (!ledHistory.value.length || !selectedDate.value) return 0
    const all = ledHistory.value.filter(row => row.timestamp.startsWith(selectedDate.value))
    if (intervalMode.value === 'hour') {
      const hours = [...new Set(all.map(row => new Date(row.timestamp).getHours()))]
      return Math.max(0, hours.length - 1)
    } else if (intervalMode.value === 'day') {
      return 0
    } else if (intervalMode.value === 'week') {
      return Math.max(0, Math.floor(all.length / (7 * 24 * 6)) - 1)
    } else if (intervalMode.value === 'month') {
      return 0
    }
    return 0
  })
  function navigateHistory (dir) {
    historyIndex.value -= dir
    if (historyIndex.value < 0) historyIndex.value = 0
    if (historyIndex.value > maxHistoryIndex.value) historyIndex.value = maxHistoryIndex.value
  }

  const filteredData = computed(() => {
    if (!ledHistory.value.length || !selectedDate.value) return []
    const all = ledHistory.value.filter(row => row.timestamp.startsWith(selectedDate.value))
    if (!all.length) return []
    let groups = []
    if (intervalMode.value === 'hour') {
      // Find the hour to display
      const last = new Date(all[all.length - 1].timestamp)
      let hour = last.getHours() - historyIndex.value
      if (hour < 0) hour = 0
      // Get all data points for this hour
      let hourData = all.filter(row => {
        const d = new Date(row.timestamp)
        return d.getHours() === hour
      })
      // If the last data point is before the end of the hour, interpolate to X:59:59 if a future value exists
      if (hourData.length > 0) {
        const lastPoint = hourData[hourData.length - 1]
        const hourEnd = new Date(lastPoint.timestamp)
        hourEnd.setMinutes(59, 59, 999)
        const lastTime = new Date(lastPoint.timestamp)
        if (lastTime.getMinutes() < 59) {
          // Find the next data point after this hour
          const next = all.find(row => {
            const d = new Date(row.timestamp)
            return d > hourEnd
          })
          if (next) {
            // Interpolate each channel value between lastPoint and next for X:59:59
            const filled = { ...lastPoint, timestamp: hourEnd.toISOString() }
            for (const color of ledColors) {
              const key = color.key
              const v1 = Number(lastPoint[key])
              const v2 = Number(next[key])
              const t1 = new Date(lastPoint.timestamp).getTime()
              const t2 = new Date(next.timestamp).getTime()
              const t = hourEnd.getTime()
              // Linear interpolation
              filled[key] = t2 !== t1 ? v1 + (v2 - v1) * ((t - t1) / (t2 - t1)) : v1
            }
            hourData = [...hourData, filled]
          } else {
            // No next point, just extend the last value to the end of the hour
            const filled = { ...lastPoint, timestamp: hourEnd.toISOString() }
            hourData = [...hourData, filled]
          }
        }
      }
      groups = hourData
    } else if (intervalMode.value === 'day') {
      groups = all
    } else if (intervalMode.value === 'week') {
      const baseDate = new Date(selectedDate.value)
      const weekStart = new Date(baseDate)
      weekStart.setDate(baseDate.getDate() - baseDate.getDay() + 1 - 7 * historyIndex.value)
      weekStart.setHours(0, 0, 0, 0)
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

  const chartOptions = computed(() => {
    const xaxis = {
      type: 'datetime',
      labels: { datetimeUTC: false },
    }
    // For hourly, always show the full hour on the x-axis
    if (intervalMode.value === 'hour' && filteredData.value.length) {
      const first = filteredData.value[0]
      const d = new Date(first.timestamp)
      d.setSeconds(0, 0)
      const min = new Date(d)
      const max = new Date(d)
      max.setHours(min.getHours() + 1)
      xaxis.min = min.getTime()
      xaxis.max = max.getTime()
    }
    return {
      chart: {
        id: 'led-timeseries',
        type: 'line',
        zoom: { enabled: true, type: 'x', autoScaleYaxis: true },
        toolbar: { show: true, tools: { zoom: true, zoomin: true, zoomout: true, pan: true, reset: true } },
        animations: { enabled: true, easing: 'easeinout', speed: 400 },
      },
      xaxis,
      yaxis: {
        min: 0,
        decimalsInFloat: 0,
      },
      stroke: {
        width: 2,
        curve: 'smooth',
      },
      colors: selectedLedColors.value.map(c => c.color),
      legend: { show: false },
      tooltip: { x: { format: 'yyyy-MM-dd HH:mm' } },
      grid: { borderColor: '#eee', strokeDashArray: 4 },
    }
  })

  const ledHistory = ref([])
  const eventLog = ref([])
  const isEventsMode = computed(() => selectionOptions.find(o => o.key === 'events').checked)

  onMounted(async () => {
    fetchLedHistory()
  })

  function getLedSquareStyle (color) {
    return {
      background: color.color,
      opacity: heldLedColor.value && heldLedColor.value !== color.key ? 0.2 : (color.selected ? 1 : 0.2),
      filter: heldLedColor.value && heldLedColor.value !== color.key ? 'grayscale(0.7)' : '',
      transition: 'opacity 0.2s, filter 0.2s',
      borderRadius: '6px',
      width: '36px',
      height: '36px',
      margin: '0',
      cursor: 'pointer',
      boxShadow: '0 2px 8px rgba(0,0,0,0.10)',
      border: heldLedColor.value === color.key ? '2px solid #1976d2' : 'none',
    }
  }

  function allowedDates (date) {
    return availableDates.value.includes(date)
  }

  function onDateChange (val) {
    selectedDate.value = val
    datePickerDialog.value = false
  }

  async function fetchLedHistory () {
    try {
      const res = await fetch('/api/logs/led_history')
      if (!res.ok) throw new Error('Failed to fetch LED history')
      const data = await res.json()
      ledHistory.value = data.history || []
      availableDates.value = [...new Set(ledHistory.value.map(row => row.timestamp.split('T')[0]))]
      if (!selectedDate.value && availableDates.value.length > 0) {
        selectedDate.value = availableDates.value[availableDates.value.length - 1]
      }
    } catch {
      showAlert('Failed to load LED history', 'error')
    }
  }

  async function fetchEventLog () {
    try {
      const res = await fetch('/api/logs/event_history')
      if (!res.ok) throw new Error('Failed to fetch event log')
      const data = await res.json()
      eventLog.value = data.history || []
    } catch {
      showAlert('Failed to load event log', 'error')
    }
  }

  watch(
    () => isEventsMode.value,
    val => {
      if (val) fetchEventLog()
    },
    { immediate: true }
  )

  function onSelectionClick (item) {
    selectionOptions.forEach(opt => opt.checked = false)
    item.checked = true
    if (item.key === 'events') fetchEventLog()
  }

  const chartSeries = computed(() => {
    if (!filteredData.value.length) return []
    return selectedLedColors.value.map(color => ({
      name: color.key,
      data: filteredData.value.map(row => [row.timestamp, row[color.key]]),
    }))
  })

  const popup = ref({ visible: false, text: '', style: {} })
  function showPopup (idx, text, event) {
    if (!text || text.length <= 54) return
    const rect = event.target.getBoundingClientRect()
    popup.value = {
      visible: true,
      text,
      style: {
        position: 'fixed',
        top: `${rect.bottom + 8}px`,
        left: `${rect.left}px`,
        zIndex: 9999,
      },
    }
  }

  function truncateAction (action) {
    if (!action) return ''
    return action.length > 54 ? action.slice(0, 54) + '…' : action
  }
  function formatEventTimestamp (ts) {
    if (!ts) return ''
    const d = new Date(ts)
    if (isNaN(d)) return ts
    const options = { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }
    return d.toLocaleString('en-US', options)
  }
</script>

<style scoped>

.v-container.fill-height {
  flex: 1 1 auto;
  display: flex;
  flex-direction: row;
  align-items: center !important;
  justify-content: center;
  height: 100vh;
  min-height: 0;
  min-width: 0;
}

.data-left-col,
.data-center-col {
  /* Remove align-self: flex-start so columns center with v-container */
  align-self: unset;
}

.data-left-col {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 24px;
  height: 100%;
  /* Align top of left column with graph card */
  justify-content: flex-start;
  margin-top: 0;
}
.data-selection-card {
  min-width: 180px;
  padding: 24px 12px 24px 12px;
  background: #fff;
  margin-bottom: 0;
}
.data-led-color-card {
  min-width: 180px;
  background: #fff;
  margin-bottom: 0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.10);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: 24px 12px 24px 12px;
  min-height: 382px;
}
.data-selection-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.data-selection-pill-btn {
  margin-bottom: 0;
}
.data-center-col {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: flex-start;
  height: 100%;
}
.data-graph-card {
  min-width: 900px;
  max-width: 900px;
  width: 100%;
  background: #fff;
  padding: 24px 24px 8px 24px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  box-shadow: 0 4px 24px rgba(0,0,0,0.08);
  margin-bottom: 0;
}
.data-graph-header {
  display: flex;
  flex-direction: row;
  align-items: center;
  margin-bottom: 8px;
  gap: 12px;
}
.data-graph-content {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0px;
}
.data-graph-empty {
  color: #aaa;
  font-size: 1.1em;
  text-align: center;
  width: 100%;
  padding: 32px 0;
}
.data-graph-nav {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 0px;
  margin-bottom: 0px;
  padding: 0;
}
.data-graph-nav .v-btn {
  min-width: 28px !important;
  height: 28px !important;
  font-size: 18px !important;
  padding: 0 !important;
}
.data-led-color-grid {
  display: grid;
  grid-template-columns: repeat(3, 36px);
  grid-template-rows: repeat(2, 36px);
  gap: 16px 16px;
  justify-content: center;
  align-items: center;
  margin-top: auto;
  margin-bottom: auto;
}
.data-led-color-square {
  transition: opacity 0.2s, filter 0.2s, border 0.2s;
  border-radius: 6px;
  width: 36px;
  height: 36px;
  margin: 0;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0,0,0,0.10);
  border: 2px solid transparent;
}
.data-led-color-square[style*='2px solid #1976d2'] {
  border: 2px solid #1976d2 !important;
}
.event-log-terminal-light {
  width: 100%;
  height: 546px;
  background: #f7f7fa;
  color: #222;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
}
.event-log-list {
  width: 100%;
  min-height: 100%;
  max-height: 100%;
  display: flex;
  flex-direction: column;
}
.event-log-row-light {
  display: flex;
  flex-direction: row;
  align-items: center;
  padding: 0 18px;
  min-height: 38px;
  font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
  font-size: 1.05em;
  line-height: 1.5;
  background: #fff;
  border-bottom: 1px solid #eee;
  cursor: pointer;
  transition: background 0.15s;
}
.event-log-row-alt-light {
  background: #f0f0f7;
}
.event-log-row-light:hover {
  background: #e3e7f7;
}
.event-log-timestamp-light {
  min-width: 120px;
  color: #1976d2;
  margin-right: 18px;
  font-weight: 500;
}
.event-log-action-light {
  flex: 1 1 0;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  cursor: pointer;
  position: relative;
  padding-right: 18px;
}
.event-log-action-light span {
  vertical-align: middle;
}
.event-log-expand-light {
  color: #1976d2;
  font-size: 0.95em;
  margin-left: 8px;
  user-select: none;
}
.event-log-status-light {
  min-width: 70px;
  text-align: right;
  font-weight: 600;
  margin-left: 18px;
  border-radius: 6px;
  padding: 2px 10px;
  font-size: 0.98em;
  background: #e3e7f7;
  color: #1976d2;
}
.event-log-status-success {
  background: #c8e6c9;
  color: #2e7d32;
}
.event-log-status-error {
  background: #ffcdd2;
  color: #b71c1c;
}
.event-log-status-pending {
  color: #ffa726;
}
.event-log-popup {
  position: fixed;
  min-width: 320px;
  max-width: 480px;
  background: #fff;
  color: #222;
  border-radius: 14px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.18);
  padding: 0;
  z-index: 9999;
  animation: fadeIn 0.18s;
}
.event-log-popup-content {
  padding: 18px 24px 18px 18px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  font-family: 'Fira Mono', 'Consolas', 'Menlo', monospace;
  font-size: 1.05em;
  word-break: break-word;
}
.event-log-popup-close {
  margin-left: auto;
  margin-top: -6px;
  color: #888;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: none; }
}
</style>
