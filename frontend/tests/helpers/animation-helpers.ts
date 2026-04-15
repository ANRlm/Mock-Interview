export async function waitForAnimations(page: any, durationMs: number = 400) {
  await page.waitForTimeout(durationMs)
}

export async function measureAnimationDuration(page: any, selector: string): Promise<number> {
  return await page.evaluate((sel: string) => {
    const el = document.querySelector(sel)
    if (!el) return 0
    const styles = window.getComputedStyle(el)
    const duration = styles.transitionDuration || styles.animationDuration
    return parseFloat(duration) * 1000
  }, selector)
}

export async function disableAnimations(page: any) {
  await page.addInitScript(() => {
    window.matchMedia = () => ({
      matches: true,
      media: '',
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => true,
    }) as any
  })
}
