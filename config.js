// Konfiguration for Hiper Cognigy AI Scraper
// IKKE_KUNDE_* koordinater skal måles på dag 1 via screenshot

module.exports = {
  // Endpoint URL til Hiper Cognigy chat
  ENDPOINT: 'https://cognigy-assets.hiper.dk/Test-branch-til-soeren/',

  // Koordinater til "Jeg er ikke kunde"-knap i chat onboarding
  // Mål disse ved at køre: node measure_coords.js
  IKKE_KUNDE_X: null, // TODO: Udfyld dag 1
  IKKE_KUNDE_Y: null, // TODO: Udfyld dag 1

  // Timeout i ms pr. bot-svar
  TIMEOUT_MS: 30000,

  // Delay mellem samtaler (ms) – random interval for at undgå rate limiting
  DELAY_MIN: 3000,
  DELAY_MAX: 8000,

  // Delay efter page load inden onboarding-klik (ms)
  PAGE_LOAD_WAIT: 2500,

  // Delay efter "ikke kunde"-klik inden spørgsmål sendes (ms)
  ONBOARDING_WAIT: 1000,

  // Tekst-fragment der indikerer ægte handover (agentoverlevering)
  HANDOVER_TEXT_MARKERS: ['sat i kø', 'stillet i kø', 'viderestiller', 'agent'],

  // Database-fil
  DB_PATH: './conversations.db',

  // Playwright browser options
  HEADLESS: true,
};
