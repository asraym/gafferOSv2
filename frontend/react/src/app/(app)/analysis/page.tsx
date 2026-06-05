'use client'
import { useEffect, useRef, useState } from 'react'
import { motion, useTransform, useSpring } from 'framer-motion'
import FormationPitch, { PitchState } from '@/components/app/FormationPitch'
import { analyseMatch, getUpcomingMatch } from '@/lib/api'
import styles from './analysis.module.css'
import { useMotionValue, } from 'framer-motion'

interface UpcomingMatch {
  match_id: number; opponent_name: string; match_date: string; venue: string
}

interface PlayerAttrs {
  pace?: number; stamina?: number; heading?: number; passing?: number
  tackling?: number; finishing?: number; creativity?: number
  strength?: number; role_rating?: number; overall_rating?: number
  [key: string]: number | undefined
}

interface XIPlayer {
  name: string; slot_key: string; specific_position: string
  broad_position: string; form_score: number | null
  attributes: PlayerAttrs; traits: string[]
  tactical_profile?: Record<string, number>
}

interface AnalysisResult {
  recommended_formation: string; defensive_formation?: string
  defensive_line: string; press_intensity: string
  tactical_focus: string; match_risk_level: string
  win_probability: number | null; draw_probability: number | null; loss_probability: number | null
  starting_xi: XIPlayer[]; bench: XIPlayer[]
  rotation_suggestions: string[]
  matchup_exploits: string[]; matchup_vulnerabilities: string[]; matchup_general_notes: string[]
  defensive_shape?: { block: string; compactness: string; press_trigger: string; transition: string; shape_label: string }
  linkup_pairs?: { id: string; player_a: string; player_b: string; description: string }[]
  reasoning: string; data_mode: string; squad_style?: any; coherence_score?: number
  formation_selection_note?: string
  opposition?: {
    likely_formation?: string; formation?: string; shape?: string
    press_style?: string; defensive_line?: string
    playing_style?: string; set_piece_threat?: string; opponent_strength?: string
    attributes?: Record<string, string>
  }
}

const ATTR_LABELS: Record<string, string> = {
  pace: 'Pace', stamina: 'Stamina', heading: 'Heading', passing: 'Passing',
  tackling: 'Tackling', finishing: 'Finishing', creativity: 'Creativity', strength: 'Strength',
}

const KEY_ATTRS_BY_POS: Record<string, string[]> = {
  GK:  ['stamina', 'strength', 'heading'],
  CB:  ['heading', 'tackling', 'pace', 'strength'],
  RB:  ['pace', 'stamina', 'tackling', 'passing'],
  LB:  ['pace', 'stamina', 'tackling', 'passing'],
  CDM: ['tackling', 'passing', 'stamina', 'strength'],
  CM:  ['passing', 'stamina', 'creativity', 'tackling'],
  CAM: ['creativity', 'passing', 'finishing', 'pace'],
  RM:  ['pace', 'creativity', 'passing', 'stamina'],
  LM:  ['pace', 'creativity', 'passing', 'stamina'],
  RW:  ['pace', 'creativity', 'finishing', 'stamina'],
  LW:  ['pace', 'creativity', 'finishing', 'stamina'],
  ST:  ['finishing', 'pace', 'heading', 'strength'],
  CF:  ['finishing', 'creativity', 'pace', 'heading'],
}

function getKeyAttrs(p: XIPlayer) {
  return KEY_ATTRS_BY_POS[p.specific_position] ?? ['pace', 'passing', 'stamina', 'heading']
}

function getSpotlightPlayers(xi: XIPlayer[]) {
  const outfield = xi.filter(p => p.broad_position !== 'GK')
  const bestOverall = [...outfield]
    .sort((a, b) => (b.attributes?.overall_rating ?? 0) - (a.attributes?.overall_rating ?? 0))[0]
  const bestFit = [...outfield]
    .sort((a, b) => (b.attributes?.role_rating ?? 0) - (a.attributes?.role_rating ?? 0))[0]
  const concern = getConcernPlayer(xi)
    ?? [...outfield].sort((a, b) => getConcernScore(b) - getConcernScore(a))[0]

  const picks: XIPlayer[] = []
  for (const p of [bestOverall, bestFit, concern]) {
    if (p && !picks.some(existing => existing.name === p.name)) picks.push(p)
  }
  return picks.slice(0, 3)
}

function getConcernPlayer(xi: XIPlayer[]): XIPlayer | null {
  return xi.find(p => (p.form_score ?? 1) < 0.35 && (p.attributes?.role_rating ?? 20) < 12) ?? null
}

function getConcernScore(p: XIPlayer) {
  const formGap = Math.max(0, 0.5 - (p.form_score ?? 0.5)) * 20
  const roleGap = Math.max(0, 13 - (p.attributes?.role_rating ?? 13))
  const overallGap = Math.max(0, 12 - (p.attributes?.overall_rating ?? 12)) * 0.5
  return formGap + roleGap + overallGap
}

function getPlayerCardMeta(index: number) {
  if (index === 0) return { label: 'Best performer', variant: 'success' }
  if (index === 1) return { label: 'Best tactical fit', variant: 'default' }
  return { label: 'Watch point', variant: 'warn' }
}

function AttrRadial({ player }: { player: XIPlayer }) {
  const attrs  = getKeyAttrs(player)
  const values = attrs.map(a => ({ label: ATTR_LABELS[a] ?? a, val: player.attributes?.[a] ?? 0 }))
  const cx = 80; const cy = 80; const r = 55; const n = values.length
  const points = values.map((v, i) => {
    const angle = (i / n) * 2 * Math.PI - Math.PI / 2
    const frac  = v.val / 20
    return { x: cx + r * frac * Math.cos(angle), y: cy + r * frac * Math.sin(angle), angle, ...v }
  })
  const polyStr = points.map(p => `${p.x},${p.y}`).join(' ')
  const rings   = [0.25, 0.5, 0.75, 1.0]
  return (
    <svg viewBox="0 0 160 160" className={styles.radial}>
      {rings.map(f => {
        const pts = Array.from({ length: n }, (_, i) => {
          const a = (i / n) * 2 * Math.PI - Math.PI / 2
          return `${cx + r * f * Math.cos(a)},${cy + r * f * Math.sin(a)}`
        }).join(' ')
        return <polygon key={f} points={pts} fill="none" stroke="rgba(61,53,48,0.10)" strokeWidth="0.8" />
      })}
      {points.map((p, i) => (
        <line key={i} x1={cx} y1={cy}
          x2={cx + r * Math.cos(p.angle)} y2={cy + r * Math.sin(p.angle)}
          stroke="rgba(61,53,48,0.10)" strokeWidth="0.8" />
      ))}
      <motion.polygon
        points={polyStr}
        fill="rgba(184,106,60,0.15)" stroke="rgba(184,106,60,0.75)" strokeWidth="1.2"
        initial={{ opacity: 0, scale: 0.4 }} animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.6 }}
        style={{ transformOrigin: `${cx}px ${cy}px` }}
      />
      {points.map((p, i) => <circle key={i} cx={p.x} cy={p.y} r="2.5" fill="var(--color-accent)" />)}
      {points.map((p, i) => {
        const lx = cx + (r + 14) * Math.cos(p.angle)
        const ly = cy + (r + 14) * Math.sin(p.angle)
        return (
          <text key={i} x={lx} y={ly} textAnchor="middle" dominantBaseline="central"
            fontSize="8" fontFamily="var(--font-mono)" fill="var(--color-muted)">
            {p.label}
          </text>
        )
      })}
    </svg>
  )
}

function FormDots({ score }: { score: number | null }) {
  if (score == null) return <span className={styles.formNone}>No data</span>
  const dots = Array.from({ length: 5 }, (_, i) => {
    const t = 1 - i * 0.15
    return score >= t ? 'W' : score >= t - 0.15 ? 'D' : 'L'
  })
  return (
    <div className={styles.formDots}>
      {dots.map((r, i) => <span key={i} className={`${styles.formDot} ${styles[`formDot${r}`]}`}>{r}</span>)}
    </div>
  )
}

function PlayerInsightCard({ player, index }: { player: XIPlayer; index: number }) {
  const meta = getPlayerCardMeta(index)
  const variantClass = styles[`playerInsight${meta.variant.charAt(0).toUpperCase() + meta.variant.slice(1)}`] ?? ''
  const attrs = getKeyAttrs(player).slice(0, 4)

  return (
    <div className={`${styles.playerInsightCard} ${variantClass}`}>
      <div className={styles.playerInsightTop}>
        <div>
          <div className={styles.playerInsightMeta}>{meta.label}</div>
          <div className={styles.playerInsightName}>{player.name}</div>
          <div className={styles.playerInsightPos}>{player.specific_position}</div>
        </div>
        <div className={styles.playerInsightScore}>
          <span>{player.attributes?.overall_rating?.toFixed(1) ?? '-'}</span>
          <small>OVR</small>
        </div>
      </div>

      {index === 0 && <AttrRadial player={player} />}

      <div className={styles.spotAttrs}>
        {attrs.map(a => {
          const v = player.attributes?.[a]
          if (!v) return null
          return (
            <div key={a} className={styles.attrRow}>
              <span className={styles.attrLabel}>{ATTR_LABELS[a]}</span>
              <div className={styles.attrTrack}>
                <motion.div
                  className={`${styles.attrFill} ${v >= 16 ? styles.attrFillHigh : ''}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${(v / 20) * 100}%` }}
                  transition={{ duration: 0.7 }}
                />
              </div>
              <span className={styles.attrValue}>{v.toFixed(1)}</span>
            </div>
          )
        })}
      </div>

      {player.traits?.length > 0 && (
        <div className={styles.spotTraits}>
          {player.traits.slice(0, 4).map(t => (
            <span key={t} className={styles.traitTag}>{t}</span>
          ))}
        </div>
      )}

      <div className={styles.spotForm}>
        <span className={styles.spotFormLabel}>Form</span>
        <FormDots score={player.form_score} />
      </div>
    </div>
  )
}

function ProbBar({ label, value, color }: { label: string; value: number | null; color: string }) {
  const pct = value != null ? Math.round(value * 100) : null
  return (
    <div className={styles.probRow}>
      <span className={styles.probLabel}>{label}</span>
      <div className={styles.probTrack}>
        <motion.div className={styles.probFill} style={{ background: color }}
          initial={{ width: 0 }} animate={{ width: pct != null ? `${pct}%` : '0%' }}
          transition={{ duration: 0.9, ease: 'easeOut' }} />
      </div>
      <span className={styles.probValue}>{pct != null ? `${pct}%` : '—'}</span>
    </div>
  )
}

function Tag({ label, variant = 'default' }: { label: string; variant?: 'default' | 'danger' | 'success' | 'warn' }) {
  return <span className={`${styles.tag} ${styles[`tag${variant.charAt(0).toUpperCase() + variant.slice(1)}`]}`}>{label}</span>
}

interface SectionPanelProps {
  inRange: [number, number]
  smooth: any
  children: React.ReactNode
}

function SectionPanel({ inRange, smooth, children }: SectionPanelProps) {
  const [s0, s1] = inRange
  const opacity = useTransform(smooth, [s0, s0 + 0.04, s1 - 0.04, s1], [0, 1, 1, 0])
  const y = useTransform(smooth, [s0, s0 + 0.06], [20, 0])

  return (
    <motion.div
      className={styles.sectionPanel}
      style={{ opacity, y, pointerEvents: 'none' }}
    >
      <div className={styles.sectionPanelInner}>
        {children}
      </div>
    </motion.div>
  )
}

const SCROLL_SECTIONS: [PitchState, [number, number]][] = [
  ['xi',         [0.00, 0.20]],
  ['opposition', [0.20, 0.40]],
  ['possession', [0.40, 0.60]],
  ['defensive',  [0.60, 0.80]],
  ['defensive',  [0.80, 1.00]],
]

export default function AnalysisPage() {
  const [match, setMatch]               = useState<UpcomingMatch | null>(null)
  const [result, setResult]             = useState<AnalysisResult | null>(null)
  const [loading, setLoading]           = useState(false)
  const [fetchingMatch, setFetchingMatch] = useState(true)
  const [error, setError]               = useState<string | null>(null)
  const [pitchState, setPitchState]     = useState<PitchState>('xi')

  // ref always mounted — avoids hydration error
  const containerRef = useRef<HTMLDivElement>(null)
  const scrollProgress = useRef(0)
  const rawProgress = useMotionValue(0)
  const smooth = useSpring(rawProgress, { stiffness: 60, damping: 20, restDelta: 0.001 })

  useEffect(() => {
    function handleScroll() {
      const el = containerRef.current
      if (!el) return
      const rect = el.getBoundingClientRect()
      const total = el.offsetHeight - window.innerHeight
      if(total <= 0) return 
      const scrolled = -rect.top
      const progress = Math.max(0, Math.min(1, scrolled / total))
      rawProgress.set(progress)
    }
    window.addEventListener('scroll', handleScroll, { passive: true})
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  useEffect(() => {
    getUpcomingMatch()
      .then((d: unknown) => setMatch(d as UpcomingMatch))
      .catch(() => setMatch(null))
      .finally(() => setFetchingMatch(false))
  }, [])


  // Fade pitch out at summary section
  const [pitchVisisble, setPitchVisible] = useState(true)
  useEffect(() => {
    return smooth.on('change', (v:number) => {
      setPitchVisible(v < 0.82)
      for (const [state, [s0, s1]] of SCROLL_SECTIONS) {
        if (v >= s0 && v < s1) { setPitchState(state); break }
      }
    })
  }, [smooth])

  async function runAnalysis() {
    if (!match) return
    setLoading(true); setError(null)
    try {
      const matchId = (match as any).match_id ?? (match as any).id
      const data    = await analyseMatch(matchId) as AnalysisResult
      setResult(data)
      setPitchState('xi')
    } catch (e: any) {
      setError(e?.message ?? 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  if (fetchingMatch) return (
    <div className={styles.centred}><div className={styles.spinner} /><p>Loading fixture…</p></div>
  )

  if (!match) return (
    <div className={styles.centred}>
      <p className={styles.emptyTitle}>No upcoming fixture</p>
      <p className={styles.emptyBody}>Register a match in the Opposition tab first.</p>
    </div>
  )

  const matchDate = new Date(match.match_date).toLocaleDateString('en-GB', {
    weekday: 'short', day: 'numeric', month: 'short',
  })
  const opp       = result?.opposition
  const oppFormation = opp?.likely_formation ?? opp?.formation ?? opp?.shape
  const spotlight = result ? getSpotlightPlayers(result.starting_xi) : []
  const concern   = result ? getConcernPlayer(result.starting_xi) : null
  const styleName = typeof result?.squad_style === 'object'
    ? result?.squad_style?.style
    : result?.squad_style

  return (
    <div className={styles.page}>

      {/* Match header */}
      <div className={styles.matchHeader}>
        <div className={styles.matchInfo}>
          <span className={styles.matchVs}>vs {match.opponent_name}</span>
          <span className={styles.matchMeta}>{matchDate} · {match.venue}</span>
        </div>
        <button
          className={`${styles.runBtn} ${loading ? styles.runBtnLoading : ''}`}
          onClick={runAnalysis} disabled={loading}
        >
          {loading ? <><span className={styles.btnSpinner} />Analysing…</> : 'Run Analysis'}
        </button>
      </div>

      {error && <div className={styles.errorBanner}>{error}</div>}

      {!result && !loading && (
        <div className={styles.preAnalysis}>
          <div className={styles.preIcon}>◈</div>
          <p>Hit <strong>Run Analysis</strong> to generate the tactical report.</p>
        </div>
      )}

      {/* scrollBody always mounted so ref is always hydrated */}
      <div
        className={styles.scrollBody}
        ref={containerRef}
        style={result ? {} : { height: 0, overflow: 'hidden', visibility: 'hidden' }}
      >
        <div className={styles.sticky}>

          {/* Left — text panels */}
          <div className={styles.left}>

            <SectionPanel inRange={[0.00, 0.20]} smooth={smooth}>
              <p className={styles.stepLabel}>01 — Playing XI</p>
              <h2 className={styles.stepTitle}>{result?.recommended_formation}</h2>
              <p className={styles.stepDesc}>
                {result?.starting_xi.length} players selected.
                {result?.formation_selection_note ? ` ${result.formation_selection_note}` : ''}
              </p>
              <div className={styles.playerInsightGrid}>
                {spotlight.map((p, i) => (
                  <PlayerInsightCard key={p.name} player={p} index={i} />
                ))}
              </div>
              {false && spotlight[0] && (
                <div className={styles.spotlight}>
                  <div className={styles.spotlightTop}>
                    <div>
                      <div className={styles.spotName}>{spotlight[0].name}</div>
                      <div className={styles.spotPos}>{spotlight[0].specific_position}</div>
                    </div>
                    <div className={styles.spotRatings}>
                      <div className={styles.spotRating}>
                        <span className={styles.spotRatingVal}>
                          {spotlight[0].attributes?.overall_rating?.toFixed(1) ?? '—'}
                        </span>
                        <span className={styles.spotRatingLabel}>OVR</span>
                      </div>
                    </div>
                  </div>
                  <AttrRadial player={spotlight[0]} />
                  <div className={styles.spotAttrs}>
                    {getKeyAttrs(spotlight[0]).slice(0, 3).map(a => {
                      const v = spotlight[0].attributes?.[a]
                      if (!v) return null
                      return (
                        <div key={a} className={styles.attrRow}>
                          <span className={styles.attrLabel}>{ATTR_LABELS[a]}</span>
                          <div className={styles.attrTrack}>
                            <motion.div
                              className={`${styles.attrFill} ${v >= 16 ? styles.attrFillHigh : ''}`}
                              initial={{ width: 0 }}
                              animate={{ width: `${(v / 20) * 100}%` }}
                              transition={{ duration: 0.7 }}
                            />
                          </div>
                          <span className={styles.attrValue}>{v.toFixed(1)}</span>
                        </div>
                      )
                    })}
                  </div>
                  {spotlight[0].traits?.length > 0 && (
                    <div className={styles.spotTraits}>
                      {spotlight[0].traits.slice(0, 3).map(t => (
                        <span key={t} className={styles.traitTag}>{t}</span>
                      ))}
                    </div>
                  )}
                  <div className={styles.spotForm}>
                    <span className={styles.spotFormLabel}>Form</span>
                    <FormDots score={spotlight[0].form_score} />
                  </div>
                </div>
              )}
              {spotlight.slice(1).map(p => (
                <div key={p.name} className={styles.spotSecondary}>
                  <div className={styles.spotSecName}>{p.name}</div>
                  <div className={styles.spotSecPos}>{p.specific_position}</div>
                  <div className={styles.spotSecRating}>
                    {p.attributes?.overall_rating?.toFixed(1) ?? '—'}
                  </div>
                </div>
              ))}
              {concern && (
                <div className={styles.concern}>
                  <span className={styles.concernIcon}>⚠</span>
                  <span>{concern.name} — below baseline in form and positional fit</span>
                </div>
              )}
            </SectionPanel>

            <SectionPanel inRange={[0.20, 0.40]} smooth={smooth}>
              <p className={styles.stepLabel}>02 — Opposition</p>
              <h2 className={styles.stepTitle}>{match.opponent_name}</h2>
              {opp ? (
                <>
                  <p className={styles.stepDesc}>
                    {oppFormation && `Playing ${oppFormation}. `}
                    {opp.playing_style && `${opp.playing_style} style. `}
                    {opp.opponent_strength && `Assessed as ${opp.opponent_strength} strength.`}
                  </p>
                  <div className={styles.oppTags}>
                    {opp.press_style && (
                      <Tag label={`Press: ${opp.press_style}`}
                        variant={opp.press_style === 'high' ? 'danger' : 'default'} />
                    )}
                    {opp.defensive_line && <Tag label={`Line: ${opp.defensive_line}`} />}
                    {opp.set_piece_threat && (
                      <Tag label={`Set pieces: ${opp.set_piece_threat}`}
                        variant={opp.set_piece_threat === 'high' ? 'warn' : 'default'} />
                    )}
                  </div>
                  {(result?.matchup_exploits?.length > 0 || result?.matchup_vulnerabilities?.length > 0) && (
                    <div className={styles.matchups}>
                      {result?.matchup_exploits?.map((e, i) => (
                        <div key={i} className={`${styles.matchupRow} ${styles.exploit}`}>
                          <span className={styles.matchupIcon}>↑</span><span>{e}</span>
                        </div>
                      ))}
                      {result?.matchup_vulnerabilities?.map((v, i) => (
                        <div key={i} className={`${styles.matchupRow} ${styles.vuln}`}>
                          <span className={styles.matchupIcon}>↓</span><span>{v}</span>
                        </div>
                      ))}
                      {result?.matchup_general_notes?.map((n, i) => (
                        <div key={i} className={`${styles.matchupRow} ${styles.noteRow}`}>
                          <span className={styles.matchupIcon}>·</span><span>{n}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </>
              ) : (
                <p className={styles.stepDesc} style={{ color: 'var(--color-muted)' }}>
                  No scouting data available. Add notes in the Opposition tab.
                </p>
              )}
            </SectionPanel>

            <SectionPanel inRange={[0.40, 0.60]} smooth={smooth}>
              <p className={styles.stepLabel}>03 — In Possession</p>
              <h2 className={styles.stepTitle}>{result?.tactical_focus}</h2>
              <p className={styles.stepDesc}>
                How the team attacks with the ball.
                {result?.linkup_pairs?.length
                  ? ` ${result.linkup_pairs.length} key linkup pairs identified.`
                  : ''}
              </p>
              {result?.linkup_pairs?.map(pair => (
                <div key={pair.id} className={styles.linkupRow}>
                  <div className={styles.linkupPlayers}>
                    <span className={styles.linkupName}>{pair.player_a}</span>
                    <span className={styles.linkupDash}>⟷</span>
                    <span className={styles.linkupName}>{pair.player_b}</span>
                  </div>
                  <p className={styles.linkupDesc}>{pair.description}</p>
                </div>
              ))}
            </SectionPanel>

            <SectionPanel inRange={[0.60, 0.80]} smooth={smooth}>
              <p className={styles.stepLabel}>04 — Out of Possession</p>
              <h2 className={styles.stepTitle}>
                {result?.defensive_shape?.shape_label ?? 'Defensive Shape'}
              </h2>
              <p className={styles.stepDesc}>
                {result?.press_intensity === 'High'
                  ? 'Aggressive press from front. Forwards lead the press trigger.'
                  : result?.press_intensity === 'Low'
                  ? 'Sit deep and absorb. Protect the block.'
                  : 'Measured press. Trigger on back pass and keeper.'}
                {' '}
                {result?.defensive_line === 'High'
                  ? 'Line pushed up — CBs need pace to cover in behind.'
                  : result?.defensive_line === 'Deep'
                  ? 'Deep block — absorb and counter.'
                  : 'Balanced line. Hold shape.'}
              </p>
              <div className={styles.defStats}>
                <div className={styles.defStat}>
                  <span className={styles.defStatVal} data-level={result?.press_intensity}>
                    {result?.press_intensity}
                  </span>
                  <span className={styles.defStatLabel}>Press</span>
                </div>
                <div className={styles.defStat}>
                  <span className={styles.defStatVal} data-line={result?.defensive_line}>
                    {result?.defensive_line}
                  </span>
                  <span className={styles.defStatLabel}>Line</span>
                </div>
                {result?.defensive_shape && (
                  <div className={styles.defStat}>
                    <span className={styles.defStatVal}>{result.defensive_shape.block}</span>
                    <span className={styles.defStatLabel}>Block</span>
                  </div>
                )}
              </div>
              {result?.rotation_suggestions
                ?.filter(s => s.toLowerCase().includes('stamina'))
                .map((s, i) => (
                  <div key={i} className={styles.staminaWarn}>
                    <span>⚡</span><span>{s}</span>
                  </div>
                ))}
            </SectionPanel>

            <SectionPanel inRange={[0.80, 1.00]} smooth={smooth}>
              <p className={styles.stepLabel}>05 — Match Summary</p>
              <h2 className={styles.stepTitle}>
                {result?.win_probability != null
                  ? `${Math.round(result.win_probability * 100)}% to win`
                  : 'Outlook'}
              </h2>
              <p className={styles.stepDesc}>
                {result?.match_risk_level} risk match.
                {result?.coherence_score != null
                  ? ` Tactical coherence: ${Math.round(result.coherence_score * 100)}.`
                  : ''}
              </p>
              <div className={styles.probs}>
                <ProbBar label="Win"  value={result?.win_probability ?? null}  color="var(--color-success)" />
                <ProbBar label="Draw" value={result?.draw_probability ?? null} color="var(--color-accent)" />
                <ProbBar label="Loss" value={result?.loss_probability ?? null} color="var(--color-alert)" />
                {result?.data_mode === 'default' && (
                  <p className={styles.dataNote}>Base rates — no match data yet</p>
                )}
              </div>
              {result?.rotation_suggestions
                ?.filter(s => !s.toLowerCase().includes('stamina'))
                .slice(0, 3)
                .map((s, i) => (
                  <div key={i} className={styles.rotationRow}>
                    <span className={styles.rotationDot} />
                    <span>{s}</span>
                  </div>
                ))}
            </SectionPanel>

          </div>

          {/* Right — sticky pitch */}
          <div className={styles.right} style={{ opacity: pitchVisisble ? 1 : 0, transition: 'opacity 0.4s ease '}}>
            {result && (
              <>
                <FormationPitch
                  pitchState={pitchState}
                  formation={result.recommended_formation}
                  defensiveFormation={result.defensive_formation}
                  xi={result.starting_xi}
                  defensiveShape={result.defensive_shape}
                  defensiveLine={result.defensive_line}
                  pressIntensity={result.press_intensity}
                  linkupPairs={result.linkup_pairs}
                  oppFormation={oppFormation}
                  squadStyle={typeof result.squad_style === 'object'
                    ? result.squad_style?.style
                    : result.squad_style}
                />
                <div className={styles.pitchKpis}>
                  <div className={styles.kpiPill}>
                    <span className={styles.kpiPillLabel}>Press</span>
                    <span className={styles.kpiPillVal} data-level={result.press_intensity}>
                      {result.press_intensity}
                    </span>
                  </div>
                  <div className={styles.kpiPill}>
                    <span className={styles.kpiPillLabel}>Line</span>
                    <span className={styles.kpiPillVal}>{result.defensive_line}</span>
                  </div>
                  <div className={styles.kpiPill}>
                    <span className={styles.kpiPillLabel}>Risk</span>
                    <span className={styles.kpiPillVal} data-level={result.match_risk_level}>
                      {result.match_risk_level}
                    </span>
                  </div>
                  {styleName && (
                    <div className={styles.kpiPill}>
                      <span className={styles.kpiPillLabel}>Style</span>
                      <span className={styles.kpiPillVal}>{styleName}</span>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

        </div>
      </div>

    </div>
  )
}
