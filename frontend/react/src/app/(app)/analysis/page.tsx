'use client'

import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getUpcomingMatch, analyseMatch } from '@/lib/api'
import styles from './analysis.module.css'

const ROLE_COLORS: Record<string, string> = {
  GK: '#B86A3C',
  DEF: '#8C7A63',
  MID: '#5A8A6A',
  FWD: '#B86A3C',
}

const FORMATION_SLOTS: Record<string, { x: number; y: number; role: string }[]> = {
  '4-3-3': [
    { x: 50, y: 88, role: 'GK' },
    { x: 18, y: 68, role: 'DEF' },
    { x: 38, y: 68, role: 'DEF' },
    { x: 62, y: 68, role: 'DEF' },
    { x: 82, y: 68, role: 'DEF' },
    { x: 28, y: 46, role: 'MID' },
    { x: 50, y: 42, role: 'MID' },
    { x: 72, y: 46, role: 'MID' },
    { x: 20, y: 20, role: 'FWD' },
    { x: 50, y: 15, role: 'FWD' },
    { x: 80, y: 20, role: 'FWD' },
  ],
  '4-4-2': [
    { x: 50, y: 88, role: 'GK' },
    { x: 18, y: 68, role: 'DEF' },
    { x: 38, y: 68, role: 'DEF' },
    { x: 62, y: 68, role: 'DEF' },
    { x: 82, y: 68, role: 'DEF' },
    { x: 18, y: 46, role: 'MID' },
    { x: 38, y: 46, role: 'MID' },
    { x: 62, y: 46, role: 'MID' },
    { x: 82, y: 46, role: 'MID' },
    { x: 35, y: 20, role: 'FWD' },
    { x: 65, y: 20, role: 'FWD' },
  ],
  '4-2-3-1': [
    { x: 50, y: 88, role: 'GK' },
    { x: 18, y: 68, role: 'DEF' },
    { x: 38, y: 68, role: 'DEF' },
    { x: 62, y: 68, role: 'DEF' },
    { x: 82, y: 68, role: 'DEF' },
    { x: 35, y: 54, role: 'MID' },
    { x: 65, y: 54, role: 'MID' },
    { x: 20, y: 36, role: 'MID' },
    { x: 50, y: 32, role: 'MID' },
    { x: 80, y: 36, role: 'MID' },
    { x: 50, y: 15, role: 'FWD' },
  ],
  '4-5-1': [
    { x: 50, y: 88, role: 'GK' },
    { x: 18, y: 68, role: 'DEF' },
    { x: 38, y: 68, role: 'DEF' },
    { x: 62, y: 68, role: 'DEF' },
    { x: 82, y: 68, role: 'DEF' },
    { x: 10, y: 46, role: 'MID' },
    { x: 28, y: 46, role: 'MID' },
    { x: 50, y: 42, role: 'MID' },
    { x: 72, y: 46, role: 'MID' },
    { x: 90, y: 46, role: 'MID' },
    { x: 50, y: 18, role: 'FWD' },
  ],
  '5-4-1': [
    { x: 50, y: 88, role: 'GK' },
    { x: 10, y: 68, role: 'DEF' },
    { x: 28, y: 68, role: 'DEF' },
    { x: 50, y: 65, role: 'DEF' },
    { x: 72, y: 68, role: 'DEF' },
    { x: 90, y: 68, role: 'DEF' },
    { x: 18, y: 46, role: 'MID' },
    { x: 38, y: 46, role: 'MID' },
    { x: 62, y: 46, role: 'MID' },
    { x: 82, y: 46, role: 'MID' },
    { x: 50, y: 18, role: 'FWD' },
  ],
}

function FormationPitch({
  formation,
  xi,
}: {
  formation: string
  xi: any[]
}) {
  const slots = FORMATION_SLOTS[formation] || FORMATION_SLOTS['4-3-3']

  return (
    <svg viewBox="0 0 100 100" className={styles.pitch}>
      <g opacity="0.18">
        <rect x="8" y="4" width="84" height="92" fill="none" stroke="#3D3530" strokeWidth="0.5" />
        <line x1="8" y1="50" x2="92" y2="50" stroke="#3D3530" strokeWidth="0.3" />
        <circle cx="50" cy="50" r="10" fill="none" stroke="#3D3530" strokeWidth="0.3" />
        <rect x="30" y="4" width="40" height="12" fill="none" stroke="#3D3530" strokeWidth="0.3" />
        <rect x="30" y="84" width="40" height="12" fill="none" stroke="#3D3530" strokeWidth="0.3" />
      </g>
      {slots.map((slot, i) => {
        const player = xi[i]
        const initials = player?.name
          ? player.name.split(' ').map((n: string) => n[0]).join('').slice(0, 2)
          : '?'
        return (
          <g key={i}>
            <circle
              cx={slot.x} cy={slot.y} r="5"
              fill={ROLE_COLORS[slot.role]}
              opacity="0.9"
            />
            <circle
              cx={slot.x} cy={slot.y} r="6.5"
              fill="none"
              stroke={ROLE_COLORS[slot.role]}
              strokeWidth="0.4"
              opacity="0.35"
            />
            <text
              x={slot.x} y={slot.y + 1.2}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="3"
              fill="#F7F3EE"
              fontFamily="monospace"
              fontWeight="500"
            >
              {initials}
            </text>
            {player?.name && (
              <text
                x={slot.x} y={slot.y + 8.5}
                textAnchor="middle"
                fontSize="2.8"
                fill="#3D3530"
                fontFamily="monospace"
                opacity="0.7"
              >
                {player.name.split(' ')[0]}
              </text>
            )}
          </g>
        )
      })}
    </svg>
  )
}

function ProbBar({
  label,
  value,
  color,
}: {
  label: string
  value: number
  color: string
}) {
  return (
    <div className={styles.probRow}>
      <span className={styles.probLabel}>{label}</span>
      <div className={styles.probTrack}>
        <motion.div
          className={styles.probFill}
          style={{ background: color }}
          initial={{ width: 0 }}
          animate={{ width: `${(value * 100).toFixed(0)}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
      <span className={styles.probVal}>{(value * 100).toFixed(0)}%</span>
    </div>
  )
}

export default function Analysis() {
  const [match, setMatch] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [analysing, setAnalysing] = useState(false)
  const [report, setReport] = useState<any>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    getUpcomingMatch()
      .then(setMatch)
      .catch(() => setMatch(null))
      .finally(() => setLoading(false))
  }, [])

  async function handleAnalyse() {
    if (!match) return
    setAnalysing(true)
    setError('')
    setReport(null)
    try {
      const result = await analyseMatch(match.id)
      setReport(result)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setAnalysing(false)
    }
  }

  const RISK_COLORS: Record<string, string> = {
    High: 'var(--color-alert)',
    Medium: 'var(--color-accent)',
    Low: 'var(--color-success)',
  }

  return (
    <div className={styles.page}>

      <div className={styles.header}>
        <div>
          <p className={styles.pageLabel}>Pre-match</p>
          <h1 className={styles.pageTitle}>Analysis</h1>
        </div>
      </div>

      {loading ? (
        <p className={styles.loadingText}>Loading...</p>
      ) : match ? (
        <div className={styles.matchBanner}>
          <div>
            <p className={styles.bannerLabel}>Upcoming fixture</p>
            <p className={styles.bannerOpponent}>vs {match.opponent_name}</p>
          </div>
          <div className={styles.bannerRight}>
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
            <button
              className={styles.btnPrimary}
              onClick={handleAnalyse}
              disabled={analysing}
            >
              {analysing ? 'Analysing...' : 'Run analysis →'}
            </button>
          </div>
        </div>
      ) : (
        <div className={styles.noMatch}>
          No upcoming fixture. Register one in the Opposition tab first.
        </div>
      )}

      {error && <p className={styles.error}>{error}</p>}

      {analysing && (
        <div className={styles.loadingState}>
          <motion.div
            className={styles.loadingDot}
            animate={{ opacity: [1, 0.3, 1] }}
            transition={{ duration: 1.2, repeat: Infinity }}
          />
          <p className={styles.loadingText}>Engine running...</p>
        </div>
      )}

      <AnimatePresence>
        {report && (
          <motion.div
            className={styles.report}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >

            {/* KPI strip */}
            <div className={styles.kpiStrip}>
              {[
                { label: 'Formation', value: report.recommended_formation },
                { label: 'Press', value: report.press_intensity },
                { label: 'Line', value: report.defensive_line },
                {
                  label: 'Risk',
                  value: report.match_risk_level,
                  color: RISK_COLORS[report.match_risk_level]
                },
                { label: 'Style', value: report.squad_style || report.tactical_focus },
              ].map(k => (
                <div key={k.label} className={styles.kpiCard}>
                  <p className={styles.kpiLabel}>{k.label}</p>
                  <p
                    className={styles.kpiValue}
                    style={{ color: k.color || 'var(--color-text)' }}
                  >
                    {k.value || '—'}
                  </p>
                </div>
              ))}
            </div>

            <div className={styles.mainGrid}>

              {/* Formation pitch */}
              <div className={styles.pitchCard}>
                <p className={styles.cardLabel}>Starting XI — {report.recommended_formation}</p>
                <div className={styles.pitchWrap}>
                  <FormationPitch
                    formation={report.recommended_formation}
                    xi={report.starting_xi || []}
                  />
                </div>
              </div>

              {/* Right column */}
              <div className={styles.rightCol}>

                {/* Probabilities */}
                {report.win_probability != null && (
                  <div className={styles.card}>
                    <p className={styles.cardLabel}>Outcome probabilities</p>
                    <div className={styles.probBars}>
                      <ProbBar label="Win" value={report.win_probability} color="var(--color-success)" />
                      <ProbBar label="Draw" value={report.draw_probability} color="var(--color-muted)" />
                      <ProbBar label="Loss" value={report.loss_probability} color="var(--color-alert)" />
                    </div>
                  </div>
                )}

                {/* Rotation */}
                {report.rotation_suggestions?.length > 0 && (
                  <div className={styles.card}>
                    <p className={styles.cardLabel}>Rotation notes</p>
                    <div className={styles.rotationList}>
                      {report.rotation_suggestions.map((s: string, i: number) => (
                        <div key={i} className={styles.rotationItem}>
                          <span className={styles.rotationDot} />
                          <span className={styles.rotationText}>{s}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Matchup exploits */}
                {report.matchup_exploits?.length > 0 && (
                  <div className={styles.card}>
                    <p className={styles.cardLabel}>Exploits</p>
                    <div className={styles.flagList}>
                      {report.matchup_exploits.map((f: string, i: number) => (
                        <div key={i} className={`${styles.flagItem} ${styles.flagGood}`}>
                          ↑ {f}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Matchup vulnerabilities */}
                {report.matchup_vulnerabilities?.length > 0 && (
                  <div className={styles.card}>
                    <p className={styles.cardLabel}>Vulnerabilities</p>
                    <div className={styles.flagList}>
                      {report.matchup_vulnerabilities.map((f: string, i: number) => (
                        <div key={i} className={`${styles.flagItem} ${styles.flagBad}`}>
                          ↓ {f}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              </div>
            </div>

            {/* Bench */}
            {report.bench?.length > 0 && (
              <div className={styles.card}>
                <p className={styles.cardLabel}>Bench</p>
                <div className={styles.benchList}>
                  {report.bench.map((p: any, i: number) => (
                    <div key={i} className={styles.benchPlayer}>
                      <span className={styles.benchName}>{p.name}</span>
                      <span className={styles.benchPos}>{p.specific_position || p.position}</span>
                      {p.overall_rating && (
                        <span className={styles.benchRating}>
                          {p.overall_rating.toFixed(1)}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Reasoning */}
            {report.reasoning && (
              <div className={styles.reasoningCard}>
                <p className={styles.cardLabel}>Engine reasoning</p>
                <p className={styles.reasoningText}>{report.reasoning}</p>
              </div>
            )}

          </motion.div>
        )}
      </AnimatePresence>

    </div>
  )
}