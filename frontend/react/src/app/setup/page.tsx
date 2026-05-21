'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import { setClub, markSetupDone } from '@/lib/storage'
import { importPlayersCSV, registerMatch } from '@/lib/api'
import styles from './setup.module.css'

type Step = 0 | 1 | 2

export default function Setup() {
  const router = useRouter()
  const [step, setStep] = useState<Step>(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [club, setClubData] = useState({ name: '', city: '', teamName: '' })
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [csvResult, setCsvResult] = useState<any>(null)
  const [match, setMatch] = useState({ opponent_name: '', match_date: '', venue: 'home' })

  const next = () => setStep(s => (s + 1) as Step)

  async function handleClub() {
    if (!club.name || !club.city || !club.teamName) {
      setError('Please fill in all fields.')
      return
    }
    setClub(club)
    setError('')
    next()
  }

  async function handleCSV() {
    if (!csvFile) { setError('Please select a CSV file.'); return }
    setLoading(true)
    setError('')
    try {
      const fd = new FormData()
      fd.append('file', csvFile)
      const result = await importPlayersCSV(fd)
      setCsvResult(result)
      next()
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  async function handleMatch() {
    if (!match.opponent_name || !match.match_date) {
      setError('Please fill in all fields.')
      return
    }
    setLoading(true)
    setError('')
    try {
      await registerMatch({
        team_id: 1,
        opponent_name: match.opponent_name,
        match_date: match.match_date,
        venue: match.venue,
      })
      markSetupDone()
      router.push('/dashboard')
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  const STEPS = ['Club info', 'Import squad', 'First fixture']

  return (
    <div className={styles.page}>
      <div className={styles.card}>

        <div className={styles.logoRow}>
          <span className={styles.logoMark}>G</span>
          <span className={styles.logoText}>GafferOS</span>
        </div>

        <div className={styles.stepper}>
          {STEPS.map((s, i) => (
            <div key={s} className={styles.stepItem}>
              <div className={`${styles.stepDot} ${i <= step ? styles.stepDotActive : ''}`}>
                {i < step ? '✓' : i + 1}
              </div>
              <span className={`${styles.stepLabel} ${i === step ? styles.stepLabelActive : ''}`}>
                {s}
              </span>
              {i < STEPS.length - 1 && <div className={`${styles.stepLine} ${i < step ? styles.stepLineActive : ''}`} />}
            </div>
          ))}
        </div>

        <AnimatePresence mode="wait">
          {step === 0 && (
            <motion.div
              key="step0"
              className={styles.stepContent}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <h1 className={styles.title}>Tell us about your club</h1>
              <p className={styles.desc}>This takes 30 seconds. You can change everything later.</p>

              <div className={styles.fields}>
                <div className={styles.field}>
                  <label className={styles.fieldLabel}>Club name</label>
                  <input
                    className={styles.input}
                    placeholder="e.g. FC Bangalore"
                    value={club.name}
                    onChange={e => setClubData(c => ({ ...c, name: e.target.value }))}
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.fieldLabel}>City</label>
                  <input
                    className={styles.input}
                    placeholder="e.g. Bangalore"
                    value={club.city}
                    onChange={e => setClubData(c => ({ ...c, city: e.target.value }))}
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.fieldLabel}>Team name</label>
                  <input
                    className={styles.input}
                    placeholder="e.g. First Team"
                    value={club.teamName}
                    onChange={e => setClubData(c => ({ ...c, teamName: e.target.value }))}
                  />
                </div>
              </div>

              {error && <p className={styles.error}>{error}</p>}
              <button className={styles.btnPrimary} onClick={handleClub}>
                Continue →
              </button>
            </motion.div>
          )}

          {step === 1 && (
            <motion.div
              key="step1"
              className={styles.stepContent}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <h1 className={styles.title}>Import your squad</h1>
              <p className={styles.desc}>Upload a CSV with your players. Download the template below.</p>

              <div className={styles.templateBox}>
                <p className={styles.templateLabel}>CSV format</p>
                <code className={styles.templateCode}>
                  name, broad_position, specific_position, secondary_position,
                  jersey_number, nationality, date_of_birth
                </code>
              </div>

              <div className={styles.field}>
                <label className={styles.fieldLabel}>Squad CSV file</label>
                <input
                  type="file"
                  accept=".csv"
                  className={styles.fileInput}
                  onChange={e => setCsvFile(e.target.files?.[0] || null)}
                />
              </div>

              {csvResult && (
                <div className={styles.csvResult}>
                  <span className={styles.csvSuccess}>
                    ✓ {csvResult.imported} players imported
                  </span>
                  {csvResult.errors?.length > 0 && (
                    <span className={styles.csvErrors}>
                      {csvResult.errors.length} rows skipped
                    </span>
                  )}
                </div>
              )}

              {error && <p className={styles.error}>{error}</p>}

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={next}>
                  Skip for now
                </button>
                <button
                  className={styles.btnPrimary}
                  onClick={handleCSV}
                  disabled={loading}
                >
                  {loading ? 'Uploading...' : 'Upload & continue →'}
                </button>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div
              key="step2"
              className={styles.stepContent}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.3 }}
            >
              <h1 className={styles.title}>Register your first fixture</h1>
              <p className={styles.desc}>Add your next upcoming match so the engine has something to analyse.</p>

              <div className={styles.fields}>
                <div className={styles.field}>
                  <label className={styles.fieldLabel}>Opponent</label>
                  <input
                    className={styles.input}
                    placeholder="e.g. Mumbai FC"
                    value={match.opponent_name}
                    onChange={e => setMatch(m => ({ ...m, opponent_name: e.target.value }))}
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.fieldLabel}>Match date</label>
                  <input
                    type="date"
                    className={styles.input}
                    value={match.match_date}
                    onChange={e => setMatch(m => ({ ...m, match_date: e.target.value }))}
                  />
                </div>
                <div className={styles.field}>
                  <label className={styles.fieldLabel}>Venue</label>
                  <select
                    className={styles.input}
                    value={match.venue}
                    onChange={e => setMatch(m => ({ ...m, venue: e.target.value }))}
                  >
                    <option value="home">Home</option>
                    <option value="away">Away</option>
                    <option value="neutral">Neutral</option>
                  </select>
                </div>
              </div>

              {error && <p className={styles.error}>{error}</p>}

              <div className={styles.btnRow}>
                <button className={styles.btnGhost} onClick={() => {
                  markSetupDone()
                  router.push('/dashboard')
                }}>
                  Skip for now
                </button>
                <button
                  className={styles.btnPrimary}
                  onClick={handleMatch}
                  disabled={loading}
                >
                  {loading ? 'Saving...' : 'Finish setup →'}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  )
}