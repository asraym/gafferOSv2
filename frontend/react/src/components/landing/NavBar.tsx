'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import styles from './Navbar.module.css'

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const handle = () => setScrolled(window.scrollY > 40)
    window.addEventListener('scroll', handle)
    return () => window.removeEventListener('scroll', handle)
  }, [])

  return (
    <motion.nav
      className={`${styles.nav} ${scrolled ? styles.scrolled : ''}`}
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
    >
      <div className={styles.logo}>
        <span className={styles.logoMark}>G</span>
        <span className={styles.logoText}>GafferOS</span>
      </div>

      <div className={styles.links}>
        <a href="#features">Features</a>
        <a href="#how-it-works">How it works</a>
        <a href="#analysis">Analysis</a>
      </div>

      <div className={styles.actions}>
        <button className={styles.btnLogin}>Sign in</button>
        <button className={styles.btnCta}>Get started</button>
      </div>
    </motion.nav>
  )
}