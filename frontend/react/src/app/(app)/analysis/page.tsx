'use client'


import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { getUpcomingMatch, analyseMatch } from '@/lib/api'
import styles from './analysis.module.css'
import FormationPitch from '@/components/app/FormationPitch'

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
      .then((m) => {console.log('match:', m); setMatch(m)})
      .catch(() => setMatch(null))
      .finally(() => setLoading(false))
  }, [])

  async function handleAnalyse() {
    if (!match) return
    setAnalysing(true)
    setError('')
    setReport(null)
    try {
      console.log('analysing match:', match)
      const result = await analyseMatch(match.match_id || match.id)
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
                { label: 'Style', value: report.squad_style?.style || report.tactical_focus },
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
                <FormationPitch
                  formation={report.recommended_formation}
                  defensiveFormation={report.defensive_formation}
                  xi={report.starting_xi || []}
                  defensiveShape={report.defensive_shape}
                  linkupPairs={report.linkup_pairs || []}
                />
              </div>

              {/* Right column */}
              <div className={styles.rightCol}>
                {/* ... rest unchanged ... */}
              </div>

            </div>

            <div className={styles.mainGrid}>

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