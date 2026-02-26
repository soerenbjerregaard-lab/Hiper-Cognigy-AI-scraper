// Konfiguration for Hiper Cognigy AI Scraper

module.exports = {
  // Endpoint URL til Hiper Cognigy chat
  ENDPOINT: 'https://cognigy-assets.hiper.dk/Test-branch-til-soeren/',

  // Iframe selector (chat kører i cross-origin iframe)
  IFRAME_SELECTOR: 'iframe[class*="cognigy-webchat"]',

  // Tekst på "ikke-kunde"-knappen (bruges af frameLocator)
  IKKE_KUNDE_TEXT: 'Jeg er ikke kunde',

  // Timeout i ms pr. bot-svar
  TIMEOUT_MS: 30000,

  // Antal samtidige samtaler (parallel scraping)
  // Kan overstyres med --concurrency N på kommandolinjen
  CONCURRENCY: 8,

  // Delay per worker mellem samtaler (ms) – lille buffer mod rate limiting
  DELAY_MIN: 1000,
  DELAY_MAX: 2000,

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
