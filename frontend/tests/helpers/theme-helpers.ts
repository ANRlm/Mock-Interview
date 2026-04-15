export async function toggleDarkMode(page: any) {
  await page.evaluate(() => {
    document.documentElement.classList.add('dark')
  })
}

export async function toggleLightMode(page: any) {
  await page.evaluate(() => {
    document.documentElement.classList.remove('dark')
  })
}

export async function emulateSystemTheme(page: any, theme: 'dark' | 'light') {
  await page.emulateMedia({ colorScheme: theme })
}

export async function getCurrentTheme(page: any): Promise<'light' | 'dark'> {
  return await page.evaluate(() => {
    return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
  })
}
