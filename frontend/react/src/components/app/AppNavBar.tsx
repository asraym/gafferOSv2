'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { getClub } from '@/lib/storage'
import styles from './AppNavbar.module.css'

const NAV_LINKS = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/squad', label: 'Squad' },
  { href: '/analysis', label: 'Analysis' },
  { href: '/opposition', label: 'Opposition' },
  { href: '/feedback', label: 'Feedback' },
]

export default function AppNavbar() {
  const pathname = usePathname()
  const [clubName, setClubName] = useState('My Club')

  useEffect(() => {
    const club = getClub()
    if (club?.name) setClubName(club.name)
  }, [])

  return (
    <nav className={styles.nav}>
      <div className={styles.inner}>
        <Link href="/" className={styles.logo}>
          <span className={styles.logoMark}>G</span>
          <span className={styles.logoText}>GafferOS</span>
        </Link>

        <div className={styles.links}>
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`${styles.link} ${pathname === link.href ? styles.active : ''}`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        <div className={styles.right}>
          <div className={styles.clubBadge}>
            <span className={styles.clubDot} />
            {clubName}
          </div>
        </div>
      </div>
    </nav>
  )
}