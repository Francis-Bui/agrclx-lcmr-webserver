<template>
  <v-card style="margin: auto" width="400">
    <!-- Title -->
    <v-container class="d-flex flex-column align-center pt-6 pb-2">
      <span class="text-h3 font-weight-bold text-center">LCMR_2</span>
    </v-container>
    <v-divider class="mb-2" />

    <v-container class="d-flex justify-center">
      <v-chip-group
        v-model="selectedChip"
        class="d-flex flex-wrap justify-center"
        mandatory
      >
        <v-chip
          v-for="chip in chips"
          :key="chip"
          class="ma-1"
          :color="chipColors[chip]"
          size="small"
          :value="chip"
          :variant="selectedChip === chip ? 'elevated' : 'outlined'"
        >
          {{ chip }}
        </v-chip>
      </v-chip-group>
    </v-container>

    <v-divider />

    <!-- Animated Circle -->
    <v-container class="d-flex justify-center my-4">
      <div
        class="d-flex align-center justify-center pulse-circle"
        :style="circleStyle"
      >
        <span class="text-h4 font-weight-bold" :style="{color: textColor}">
          {{ sliderValues[selectedChip] }}%
        </span>
      </div>
    </v-container>

    <v-card-text>
      <v-slider
        v-model="sliderValues[selectedChip]"
        class="ma-4"
        :color="chipColors[selectedChip]"
        hide-details
        :max="100"
        :step="1"
        @update:model-value="saveSliderValues"
      >
        <template #append>
          <v-text-field
            v-model="sliderValues[selectedChip]"
            density="compact"
            hide-details
            :max="100"
            style="width: 80px"
            suffix="%"
            type="number"
            variant="outlined"
            @update:model-value="onTextFieldInput"
          />
        </template>
      </v-slider>
    </v-card-text>

    <v-divider />

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
  </v-card>
</template>

<script setup>
  import { computed, onMounted, reactive, ref, watch } from 'vue'

  const chips = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']

  const chipColors = {
    IR: '#ff5252', // Red
    Red: '#ff5252', // Red
    Green: '#4caf50', // Green
    Blue: '#2196f3', // Blue
    White: '#e0e0e0', // Light grey
    UV: '#7c4dff', // Purple
  }

  const textColor = computed(() =>
    selectedChip.value === 'White' ? '#333' : '#fff'
  )

  // All sliders start at 0 for safety
  const defaultSliderValues = {
    IR: 0,
    Red: 0,
    Green: 0,
    Blue: 0,
    White: 0,
    UV: 0,
  }

  const sliderValues = reactive({ ...defaultSliderValues })
  const selectedChip = ref('IR')

  // Persistence
  onMounted(() => {
    const saved = localStorage.getItem('lightSliderValues')
    if (saved) Object.assign(sliderValues, JSON.parse(saved))
    const savedChip = localStorage.getItem('selectedChip')
    if (savedChip && chips.includes(savedChip)) selectedChip.value = savedChip
  })
  watch(sliderValues, val => {
    localStorage.setItem('lightSliderValues', JSON.stringify(val))
  }, { deep: true })
  watch(selectedChip, val => {
    localStorage.setItem('selectedChip', val)
  })

  // Save slider values on manual input
  function saveSliderValues () {
    localStorage.setItem('lightSliderValues', JSON.stringify(sliderValues))
    sendStateToBackend(
      sliderValues,
      getSchedulesFromStorage()
    )
  }

  // Prevent numbers > 100 in text field
  function onTextFieldInput (val) {
    if (val > 100) {
      sliderValues[selectedChip.value] = 100
    } else if (val < 0) {
      sliderValues[selectedChip.value] = 0
    }
    saveSliderValues()
  }

  // Get schedules from local storage to prevent sending null values
  function getSchedulesFromStorage () {
    const lightOrder = ['IR', 'Red', 'Green', 'Blue', 'White', 'UV']
    const saved = JSON.parse(localStorage.getItem('schedules') || '[]')
    return {
      scheduleCount: saved.length,
      schedules: saved.map(s => [
        !!s.enabled,
        s.start ? parseInt(s.start.replace(':', '').replace(':', '')) : 0,
        s.end ? parseInt(s.end.replace(':', '').replace(':', '')) : 0,
        ...lightOrder.map(light => s.lights && s.lights.includes(light)),
      ]),
    }
  }

  // Send lighting and schedule data to Flask
  async function sendStateToBackend (lighting, scheduleData) {
    const response = await fetch('http://localhost:5000/api/state', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lighting,
        scheduleData,
      }),
    })
    const result = await response.json()
    console.log('Backend response:', result) // Debug print
  }

  // Pulsating fire effect
  const circleStyle = computed(() => {
    const color = chipColors[selectedChip.value]
    const intensity = sliderValues[selectedChip.value] / 100
    // Aura opacity is 0 when intensity is 0, up to 1 at max
    const auraAlpha = intensity

    let boxShadow = ''
    if (selectedChip.value === 'White') {
      boxShadow = `
        0 0 ${30 + 40 * intensity}px 10px rgba(224,224,224,${auraAlpha}),
        0 0 ${60 + 60 * intensity}px 20px rgba(255,255,255,${auraAlpha * 0.7})
      `
    } else {
      // Convert hex to rgb for alpha
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
    return {
      width: '100px',
      height: '100px',
      borderRadius: '50%',
      background: selectedChip.value === 'White'
        ? 'radial-gradient(circle, #fff 60%, #e0e0e0 100%)'
        : `radial-gradient(circle, ${color} 60%, #222 100%)`,
      boxShadow,
      animation: `pulse ${1.2 - intensity * 0.7}s infinite alternate`,
      transition: 'background 0.3s, box-shadow 0.3s',
    }
  })
</script>

<style scoped>
@keyframes pulse {
  0% {
    transform: scale(1);
    filter: brightness(1);
  }
  100% {
    transform: scale(1.08);
    filter: brightness(1.25);
  }
}
</style>
