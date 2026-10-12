const { defineConfig, devices } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './tests/web',
  timeout: 30000,
  retries: process.env.CI ? 1 : 0,
  workers: 2,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: { baseURL: 'http://127.0.0.1:8769', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'], viewport: { width: 1440, height: 1000 } } },
    { name: 'mobile', use: { ...devices['Desktop Chrome'], viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } }
  ],
  webServer: {
    command: 'uv run --locked --no-sync python -m http.server 8769 --bind 127.0.0.1 --directory docs',
    url: 'http://127.0.0.1:8769', reuseExistingServer: false
  }
});
