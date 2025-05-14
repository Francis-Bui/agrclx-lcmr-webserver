<template>
  <v-container class="fill-height d-flex align-center justify-center">
    <span class="text-h4 font-weight-bold">Data Page</span>
  </v-container>
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
</template>
