'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getUpcomingMatch, submitFeedback } from '@/lib/api'
import styles from './feedback.module.css'

export default function Feedback() {
  const [match, setMatch] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const [form, setForm] = useState({
    actual_result: '',
    formation_used: '',
    goals_scored: '',
    goals_conceded: '',
    coach_followed_rec: true,
    coach_notes: '',
  })

  useEffect(() => {
    getUpcomingMatch()
      .then(setMatch)
      .catch(() => setMatch(null))
      .finally(() => setLoading(false))
  }, [])

  async function handleSubmit() {
    if (!form.actual_result) {
      setError('Select a result.')
      return
    }
    if (!match) {
      setError('No match found.')
      return
    }
    setSubmitting(true)
    setError('')
    try {
      await submitFeedback({
        match_id: match.match_id || match.id,
        actual_result: form.actual_result,
        formation_used: form.formation_used || null,
        goals_scored: form.goals_scored ? parseInt(form.goals_scored) : null,
        goals_conceded: form.goals_conceded ? parseInt(form.goals_conceded) : null,
        coach_followed_rec: form.coach_followed_rec,
        coach_notes: form.coach_notes || null,
      })
      setSubmitted(true)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const RESULTS = [
    { value: 'W', label: 'Win', color: 'var(--color-success)' },
    { value: 'D', label: 'Draw', color: 'var(--color-muted)' },
    { value: 'L', label: 'Loss', color: 'var(--color-alert)' },
  ]

  return (
    <div className={styles.page}>

      <div className={styles.header}>
        <div>
          <p className={styles.pageLabel}>Post-match</p>
          <h1 className={styles.pageTitle}>Feedback</h1>
        </div>
      </div>

      <p className={styles.desc}>
        Submit the actual result after each match. The engine uses this
        to learn which recommendations translate to wins over time.
      </p>

      {loading ? (
        <p className={styles.loadingText}>Loading...</p>
      ) : match ? (
        <div className={styles.matchBanner}>
          <p className={styles.bannerLabel}>Match</p>
          <p className={styles.bannerOpponent}>vs {match.opponent_name}</p>
          <div className={styles.bannerMeta}>
            <span className={styles.metaTag}>
              {new Date(match.match_date).toLocaleDateString('en-GB', {
                weekday: 'short', day: 'numeric', month: 'short'
              })}
            </span>
            <span className={styles.metaTag}>
              {match.venue?.charAt(0).toUpperCase() + match.venue?.slice(1)}
            </span>
          </div>
        </div>
      ) : (
        <div className={styles.noMatch}>
          No match found. Register a fixture in the Opposition tab first.
        </div>
      )}

      <AnimatePresence mode="wait">
        {submitted ? (
          <motion.div
            className={styles.successCard}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <span className={styles.successIcon}>✓</span>
            <div>
              <p className={styles.successTitle}>Feedback submitted</p>
              <p className={styles.successDesc}>
                The engine has recorded this result. It will factor into
                future recommendations as match data accumulates.
              </p>
            </div>
          </motion.div>
        ) : (
          <motion.div
            key="form"
            className={styles.formCard}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >

            {/* Result selector */}
            <div className={styles.fieldGroup}>
              <p className={styles.fieldLabel}>Result</p>
              <div className={styles.resultRow}>
                {RESULTS.map(r => (
                  <button
                    key={r.value}
                    className={`${styles.resultBtn} ${form.actual_result === r.value ? styles.resultBtnActive : ''}`}
                    style={form.actual_result === r.value ? {
                      borderColor: r.color,
                      color: r.color,
                      background: `${r.color}18`,
                    } : {}}
                    onClick={() => setForm(f => ({ ...f, actual_result: r.value }))}
                  >
                    {r.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Score */}
            <div className={styles.fieldGroup}>
              <p className={styles.fieldLabel}>Score</p>
              <div className={styles.scoreRow}>
                <div className={styles.scoreField}>
                  <label className={styles.scoreLabel}>Goals scored</label>
                  <input
                    type="number"
                    min="0"
                    className={styles.input}
                    value={form.goals_scored}
                    onChange={e => setForm(f => ({ ...f, goals_scored: e.target.value }))}
                    placeholder="0"
                  />
                </div>
                <span className={styles.scoreDash}>—</span>
                <div className={styles.scoreField}>
                  <label className={styles.scoreLabel}>Goals conceded</label>
                  <input
                    type="number"
                    min="0"
                    className={styles.input}
                    value={form.goals_conceded}
                    onChange={e => setForm(f => ({ ...f, goals_conceded: e.target.value }))}
                    placeholder="0"
                  />
                </div>
              </div>
            </div>

            {/* Formation used */}
            <div className={styles.fieldGroup}>
              <p className={styles.fieldLabel}>Formation used</p>
              <input
                className={styles.input}
                placeholder="e.g. 4-3-3"
                value={form.formation_used}
                onChange={e => setForm(f => ({ ...f, formation_used: e.target.value }))}
              />
            </div>

            {/* Followed recommendation */}
            <div className={styles.fieldGroup}>
              <p className={styles.fieldLabel}>Did you follow the engine recommendation?</p>
              <div className={styles.toggleRow}>
                <button
                  className={`${styles.toggleBtn} ${form.coach_followed_rec ? styles.toggleActive : ''}`}
                  onClick={() => setForm(f => ({ ...f, coach_followed_rec: true }))}
                >
                  Yes
                </button>
                <button
                  className={`${styles.toggleBtn} ${!form.coach_followed_rec ? styles.toggleActive : ''}`}
                  onClick={() => setForm(f => ({ ...f, coach_followed_rec: false }))}
                >
                  No
                </button>
              </div>
            </div>

            {/* Coach notes */}
            <div className={styles.fieldGroup}>
              <p className={styles.fieldLabel}>Notes (optional)</p>
              <textarea
                className={styles.textarea}
                placeholder="Anything notable about how the match played out..."
                value={form.coach_notes}
                onChange={e => setForm(f => ({ ...f, coach_notes: e.target.value }))}
                rows={4}
              />
            </div>

            {error && <p className={styles.error}>{error}</p>}

            <button
              className={styles.btnPrimary}
              onClick={handleSubmit}
              disabled={submitting || !match}
            >
              {submitting ? 'Submitting...' : 'Submit feedback →'}
            </button>

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}