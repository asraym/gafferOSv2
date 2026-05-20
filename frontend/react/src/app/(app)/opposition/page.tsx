'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getUpcomingMatch, parseOpposition, registerMatch } from '@/lib/api'
import { TEAM_ID } from '@/lib/api'
import styles from './opposition.module.css'

export default function Opposition() {
  const [match, setMatch] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [notes, setNotes] = useState('')
  const [parsing, setParsing] = useState(false)
  const [parsed, setParsed] = useState<any>(null)
  const [error, setError] = useState('')

  const [showRegister, setShowRegister] = useState(false)
  const [newMatch, setNewMatch] = useState({
    opponent_name: '',
    match_date: '',
    venue: 'home',
  })
  const [registering, setRegistering] = useState(false)

  useEffect(() => {
    getUpcomingMatch()
      .then(setMatch)
      .catch(() => setMatch(null))
      .finally(() => setLoading(false))
  }, [])

  async function handleParse() {
    if (!notes.trim()) { setError('Add some scouting notes first.'); return }
    if (!match) { setError('No upcoming match found.'); return }
    setParsing(true)
    setError('')
    try {
      const result = await parseOpposition({
        match_id: match.id,
        opponent_name: match.opponent_name,
        notes,
      })
      setParsed(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setParsing(false)
    }
  }

  async function handleRegister() {
    if (!newMatch.opponent_name || !newMatch.match_date) {
      setError('Fill in all fields.')
      return
    }
    setRegistering(true)
    setError('')
    try {
      await registerMatch({ team_id: TEAM_ID, ...newMatch })
      const m = await getUpcomingMatch()
      setMatch(m)
      setShowRegister(false)
      setNewMatch({ opponent_name: '', match_date: '', venue: 'home' })
    } catch (e: any) {
      setError(e.message)
    } finally {
      setRegistering(false)
    }
  }

  const STYLE_COLORS: Record<string, string> = {
    high: '#C8612A',
    medium: '#8C7A63',
    low: '#5A8A6A',
    direct: '#C8612A',
    possession: '#5A8A6A',
    counter: '#B86A3C',
    physical: '#8C7A63',
  }

  return (
    <div className={styles.page}>

      <div className={styles.header}>
        <div>
          <p className={styles.pageLabel}>Pre-match</p>
          <h1 className={styles.pageTitle}>Opposition</h1>
        </div>
        <button
          className={styles.btnGhost}
          onClick={() => setShowRegister(!showRegister)}
        >
          + Register match
        </button>
      </div>

      {/* Register match panel */}
      <AnimatePresence>
        {showRegister && (
          <motion.div
            className={styles.registerBox}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.25 }}
          >
            <p className={styles.boxLabel}>Register upcoming fixture</p>
            <div className={styles.registerRow}>
              <input
                className={styles.input}
                placeholder="Opponent name"
                value={newMatch.opponent_name}
                onChange={e => setNewMatch(m => ({ ...m, opponent_name: e.target.value }))}
              />
              <input
                type="date"
                className={styles.input}
                value={newMatch.match_date}
                onChange={e => setNewMatch(m => ({ ...m, match_date: e.target.value }))}
              />
              <select
                className={styles.input}
                value={newMatch.venue}
                onChange={e => setNewMatch(m => ({ ...m, venue: e.target.value }))}
              >
                <option value="home">Home</option>
                <option value="away">Away</option>
                <option value="neutral">Neutral</option>
              </select>
              <button
                className={styles.btnPrimary}
                onClick={handleRegister}
                disabled={registering}
              >
                {registering ? 'Saving...' : 'Save'}
              </button>
            </div>
            {error && <p className={styles.error}>{error}</p>}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Match context */}
      {loading ? (
        <p className={styles.loadingText}>Loading...</p>
      ) : match ? (
        <div className={styles.matchBanner}>
          <div className={styles.matchBannerLeft}>
            <p className={styles.bannerLabel}>Upcoming fixture</p>
            <p className={styles.bannerOpponent}>vs {match.opponent_name}</p>
          </div>
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
          <p>No upcoming match registered. Use the button above to add one.</p>
        </div>
      )}

      {/* Scouting notes input */}
      <div className={styles.notesSection}>
        <p className={styles.sectionLabel}>Scouting notes</p>
        <p className={styles.sectionDesc}>
          Write what you know about the opponent in plain English.
          The engine will parse it into structured data.
        </p>
        <div className={styles.exampleBox}>
          <p className={styles.exampleLabel}>Example</p>
          <p className={styles.exampleText}>
            "They play a 4-3-3 and press high. Their left back is slow.
            Very dangerous from set pieces. Striker tends to drift wide."
          </p>
        </div>
        <textarea
          className={styles.textarea}
          placeholder="Write your scouting notes here..."
          value={notes}
          onChange={e => setNotes(e.target.value)}
          rows={6}
        />
        {error && <p className={styles.error}>{error}</p>}
        <button
          className={styles.btnPrimary}
          onClick={handleParse}
          disabled={parsing || !match}
        >
          {parsing ? 'Parsing...' : 'Parse scouting notes →'}
        </button>
      </div>

      {/* Parsed output */}
      <AnimatePresence>
        {parsed && (
          <motion.div
            className={styles.parsedSection}
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <p className={styles.sectionLabel}>Parsed profile</p>

            <div className={styles.parsedGrid}>
              {[
                { label: 'Formation', value: parsed.likely_formation || '—' },
                { label: 'Press style', value: parsed.press_style || '—' },
                { label: 'Defensive line', value: parsed.defensive_line || '—' },
                { label: 'Playing style', value: parsed.playing_style || '—' },
                { label: 'Set piece threat', value: parsed.set_piece_threat || '—' },
                { label: 'Strength', value: parsed.opponent_strength || '—' },
              ].map(item => (
                <div key={item.label} className={styles.parsedCard}>
                  <p className={styles.parsedLabel}>{item.label}</p>
                  <p
                    className={styles.parsedValue}
                    style={{ color: STYLE_COLORS[item.value?.toLowerCase()] || 'var(--color-text)' }}
                  >
                    {item.value}
                  </p>
                </div>
              ))}
            </div>

            {parsed.attributes && Object.keys(parsed.attributes).length > 0 && (
              <div className={styles.attributesBox}>
                <p className={styles.boxLabel}>Player-level notes</p>
                <div className={styles.attributesList}>
                  {Object.entries(parsed.attributes).map(([pos, attr]) => (
                    <div key={pos} className={styles.attributeRow}>
                      <span className={styles.attrPos}>{pos.replace(/_/g, ' ')}</span>
                      <span className={styles.attrVal}>{attr as string}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}