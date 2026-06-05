'use client'

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import AppNavbar from '@/components/app/AppNavBar'
import { isSetupDone } from '@/lib/storage'
import styles from './layout.module.css'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const pathname = usePathname()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    if (!isSetupDone()) {
      router.replace('/setup')
    } else {
      setChecking(false)
    }
  }, [pathname, router])

  if (checking) return null

  return (
    <div className={styles.shell}>
      <AppNavbar />
      <main className={styles.main}>
        {children}
      </main>
    </div>
  )
}