'use client'

import { useRef } from 'react'
import { motion, useScroll, useTransform, useSpring } from 'framer-motion'
import styles from './ScrollStory.module.css'

const F442 = [
  { x: 50, y: 88, role: 'GK',  n: 1 },
  { x: 18, y: 68, role: 'DEF', n: 2 },
  { x: 38, y: 68, role: 'DEF', n: 5 },
  { x: 62, y: 68, role: 'DEF', n: 6 },
  { x: 82, y: 68, role: 'DEF', n: 3 },
  { x: 18, y: 46, role: 'MID', n: 11 },
  { x: 38, y: 46, role: 'MID', n: 8 },
  { x: 62, y: 46, role: 'MID', n: 4 },
  { x: 82, y: 46, role: 'MID', n: 7 },
  { x: 35, y: 22, role: 'FWD', n: 10 },
  { x: 65, y: 22, role: 'FWD', n: 9 },
]

// On-ball shape
const F352 = [
  { x: 50, y: 88, role: 'GK',  n: 1 },
  { x: 28, y: 68, role: 'DEF', n: 5 },
  { x: 50, y: 70, role: 'DEF', n: 6 },
  { x: 72, y: 68, role: 'DEF', n: 2 },
  { x: 14, y: 48, role: 'MID', n: 3 },
  { x: 30, y: 44, role: 'MID', n: 8 },
  { x: 50, y: 42, role: 'MID', n: 4 },
  { x: 70, y: 44, role: 'MID', n: 7 },
  { x: 86, y: 48, role: 'MID', n: 11 },
  { x: 36, y: 20, role: 'FWD', n: 10 },
  { x: 64, y: 20, role: 'FWD', n: 9 },
]

// Off-ball shape
const F451 = [
  { x: 50, y: 88, role: 'GK',  n: 1 },
  { x: 18, y: 68, role: 'DEF', n: 2 },
  { x: 38, y: 68, role: 'DEF', n: 5 },
  { x: 62, y: 68, role: 'DEF', n: 6 },
  { x: 82, y: 68, role: 'DEF', n: 3 },
  { x: 14, y: 46, role: 'MID', n: 11 },
  { x: 32, y: 44, role: 'MID', n: 8 },
  { x: 50, y: 42, role: 'MID', n: 4 },
  { x: 68, y: 44, role: 'MID', n: 7 },
  { x: 86, y: 46, role: 'MID', n: 10 },
  { x: 50, y: 22, role: 'FWD', n: 9 },
]

// Step 3 base shape (4-2-3-1)
const F4231 = [
  { x: 50, y: 88, role: 'GK',  n: 1 },
  { x: 18, y: 68, role: 'DEF', n: 2 },
  { x: 38, y: 68, role: 'DEF', n: 5 },
  { x: 62, y: 68, role: 'DEF', n: 6 },
  { x: 82, y: 68, role: 'DEF', n: 3 },
  { x: 35, y: 54, role: 'MID', n: 8 },
  { x: 65, y: 54, role: 'MID', n: 4 },
  { x: 20, y: 36, role: 'MID', n: 11 },
  { x: 50, y: 32, role: 'MID', n: 7 },
  { x: 80, y: 36, role: 'MID', n: 10 },
  { x: 50, y: 15, role: 'FWD', n: 9 },
]

const OPP = [
  { x: 50, y: 12 },
  { x: 18, y: 28 },
  { x: 38, y: 28 },
  { x: 62, y: 28 },
  { x: 82, y: 28 },
  { x: 25, y: 44 },
  { x: 50, y: 40 },
  { x: 75, y: 44 },
  { x: 20, y: 60 },
  { x: 50, y: 64 },
  { x: 80, y: 60 },
]

const ROLE_COLORS: Record<string, string> = {
  GK:  '#B86A3C',
  DEF: '#8C7A63',
  MID: '#5A8A6A',
  FWD: '#C8612A',
}

const GOOD_FORM = [2, 6, 9]

const POPUPS = [
  { idx: 2,  label: 'Rajan M.', attrs: ['Form 0.81', 'Pace 16.2', 'Fit 94%'] },
  { idx: 6,  label: 'Rohit A.', attrs: ['Form 0.74', 'Pass 18',   'Stam 15'] },
  { idx: 9,  label: 'Sanjay R.', attrs: ['Form 0.79', 'Fin 17',   'Pace 15'] },
]

// Step 2 has two sub-states shown in the formation tag
const STEPS = [
  {
    label: 'Step 1 — Squad analysis',
    title: 'We start with your squad.',
    desc:  'Form curves, fatigue scores, and attribute profiles computed for every available player. Rising players flagged before selection.',
    tag:   '4-4-2',
  },
  {
    label: 'Step 2 — Tactical shape',
    title: 'The engine picks on-ball & off-ball shapes.',
    desc:  'Formation shifts dynamically — 3-5-2 in possession, 4-5-1 out of possession. Players animate between both states.',
    tag:   null, // rendered dynamically
  },
  {
    label: 'Step 3 — Matchup intelligence',
    title: 'Exploits and vulnerabilities surfaced.',
    desc:  'Opposition mapped. Striker run triggers the CB\'s tracking habit — positional vulnerability exposed before kick-off.',
    tag:   '4-2-3-1',
  },
]

function ease(t: number) {
  return t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t
}
function interp(from: number, to: number, t: number) {
  return from + (to - from) * ease(Math.max(0, Math.min(1, t)))
}

export default function ScrollStory() {
  const containerRef = useRef<HTMLDivElement>(null)

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start start', 'end end'],
  })

  const smooth = useSpring(scrollYProgress, {
    stiffness: 60,
    damping: 20,
    restDelta: 0.001,
  })

  // ─── Position transforms ──────────────────────────────────────────────────
  // Scroll map:
  //   0.00–0.33  step 1  (4-4-2, popups)
  //   0.33–0.45  transition → 3-5-2 (on-ball)
  //   0.45–0.52  hold 3-5-2
  //   0.52–0.63  transition → 4-5-1 (off-ball)
  //   0.63–0.66  hold 4-5-1
  //   0.66–0.78  transition → 4-2-3-1 (step 3 base)
  //   0.78–1.00  step 3  (opponents, striker run, CB trail, popup)

  const makeX = (i: number) =>
    useTransform(smooth, (s) => {
      if (s < 0.33) return F442[i].x
      if (s < 0.45) return interp(F442[i].x, F352[i].x, (s - 0.33) / 0.12)
      if (s < 0.52) return F352[i].x
      if (s < 0.63) return interp(F352[i].x, F451[i].x, (s - 0.52) / 0.11)
      if (s < 0.66) return F451[i].x
      if (s < 0.78) return interp(F451[i].x, F4231[i].x, (s - 0.66) / 0.12)
      // Striker run (player index 10 = jersey #9)
      if (i === 10 && s >= 0.82) return F4231[i].x + interp(0, 22, (s - 0.82) / 0.12)
      // CB tracks striker (player index 3 = jersey #6)
      if (i === 3  && s >= 0.85) return F4231[i].x + interp(0, 16, (s - 0.85) / 0.10)
      return F4231[i].x
    })

  const makeY = (i: number) =>
    useTransform(smooth, (s) => {
      if (s < 0.33) return F442[i].y
      if (s < 0.45) return interp(F442[i].y, F352[i].y, (s - 0.33) / 0.12)
      if (s < 0.52) return F352[i].y
      if (s < 0.63) return interp(F352[i].y, F451[i].y, (s - 0.52) / 0.11)
      if (s < 0.66) return F451[i].y
      if (s < 0.78) return interp(F451[i].y, F4231[i].y, (s - 0.66) / 0.12)
      // Striker runs forward (up the pitch = lower y)
      if (i === 10 && s >= 0.82) return F4231[i].y - interp(0, 8, (s - 0.82) / 0.12)
      // CB tracks
      if (i === 3  && s >= 0.85) return F4231[i].y - interp(0, 6, (s - 0.85) / 0.10)
      return F4231[i].y
    })

  // Pre-compute all 11 pairs (no hooks inside loops)
  const x0  = makeX(0);  const y0  = makeY(0)
  const x1  = makeX(1);  const y1  = makeY(1)
  const x2  = makeX(2);  const y2  = makeY(2)
  const x3  = makeX(3);  const y3  = makeY(3)
  const x4  = makeX(4);  const y4  = makeY(4)
  const x5  = makeX(5);  const y5  = makeY(5)
  const x6  = makeX(6);  const y6  = makeY(6)
  const x7  = makeX(7);  const y7  = makeY(7)
  const x8  = makeX(8);  const y8  = makeY(8)
  const x9  = makeX(9);  const y9  = makeY(9)
  const x10 = makeX(10); const y10 = makeY(10)

  const xs = [x0, x1, x2, x3, x4, x5, x6, x7, x8, x9, x10]
  const ys = [y0, y1, y2, y3, y4, y5, y6, y7, y8, y9, y10]

  // ─── Opacity controls ─────────────────────────────────────────────────────
  const s1op  = useTransform(smooth, [0, 0.05, 0.28, 0.33], [0, 1, 1, 0])
  const s2op  = useTransform(smooth, [0.33, 0.38, 0.61, 0.66], [0, 1, 1, 0])
  const s3op  = useTransform(smooth, [0.66, 0.72, 1, 1], [0, 1, 1, 1])
  const stepOps = [s1op, s2op, s3op]

  const s1y   = useTransform(smooth, [0, 0.05], [20, 0])
  const s2y   = useTransform(smooth, [0.33, 0.38], [20, 0])
  const s3y   = useTransform(smooth, [0.66, 0.72], [20, 0])
  const stepYs = [s1y, s2y, s3y]

  // Step 2 formation tag switches mid-step
  const formTag2 = useTransform(smooth, (s) => {
    if (s < 0.52) return '3-5-2'
    return '4-5-1'
  })

  // Defensive line (step 2)
  const defLineOp = useTransform(smooth, [0.38, 0.46, 0.61, 0.66], [0, 1, 1, 0])

  // Step 3 layers: opponents → striker run → CB trail → CB popup
  const oppOp      = useTransform(smooth, [0.72, 0.80], [0, 1])
  const runTrailOp = useTransform(smooth, (s) =>
    s >= 0.82 ? Math.min(1, (s - 0.82) / 0.12) : 0
  )
  const cbTrailOp  = useTransform(smooth, (s) =>
    s >= 0.85 ? Math.min(1, (s - 0.85) / 0.10) : 0
  )
  const cbPopOp    = useTransform(smooth, (s) =>
    s >= 0.92 ? Math.min(1, (s - 0.92) / 0.06) : 0
  )

  // Striker run trail endpoints (from static origin → animated tip)
  const strikerOriginX = F4231[10].x
  const strikerOriginY = F4231[10].y
  const cbOriginX      = F4231[3].x
  const cbOriginY      = F4231[3].y

  return (
    <section className={styles.section} id="how-it-works" ref={containerRef}>
      <div className={styles.sticky}>

        {/* Left — text panels */}
        <div className={styles.left}>
          {STEPS.map((s, i) => (
            <motion.div
              key={i}
              className={styles.step}
              style={{ opacity: stepOps[i], y: stepYs[i] }}
            >
              <p className={styles.stepLabel}>{s.label}</p>
              <h2 className={styles.stepTitle}>{s.title}</h2>
              <p className={styles.stepDesc}>{s.desc}</p>

              {/* Step 2: formation tag updates live */}
              {i === 1 ? (
                <motion.div className={styles.formationTag}>
                  {formTag2}
                </motion.div>
              ) : (
                <div className={styles.formationTag}>{s.tag}</div>
              )}
            </motion.div>
          ))}
        </div>

        {/* Right — pitch */}
        <div className={styles.right}>
          <div className={styles.pitchWrap}>
            <svg viewBox="0 0 100 100" className={styles.pitch}>

              {/* Pitch markings */}
              <g opacity="0.15">
                <rect x="8"  y="4"  width="84" height="92" fill="none" stroke="#3D3530" strokeWidth="0.5" />
                <line x1="8" y1="50" x2="92" y2="50" stroke="#3D3530" strokeWidth="0.3" />
                <circle cx="50" cy="50" r="10" fill="none" stroke="#3D3530" strokeWidth="0.3" />
                <rect x="30" y="4"  width="40" height="12" fill="none" stroke="#3D3530" strokeWidth="0.3" />
                <rect x="30" y="84" width="40" height="12" fill="none" stroke="#3D3530" strokeWidth="0.3" />
              </g>

              {/* Defensive line (step 2) */}
              <motion.line
                x1="10" y1="60" x2="90" y2="60"
                stroke="#B86A3C" strokeWidth="0.5" strokeDasharray="2 1.5"
                style={{ opacity: defLineOp }}
              />
              <motion.text
                x="91" y="59.5" fontSize="2.5" fill="#B86A3C" fontFamily="monospace"
                style={{ opacity: defLineOp }}
              >
                def. line
              </motion.text>

              {/* Opposition nodes (step 3) */}
              {OPP.map((p, i) => (
                <motion.g key={`opp-${i}`} style={{ opacity: oppOp }}>
                  <circle cx={p.x} cy={p.y} r="2.6" fill="#8B3A3A" opacity="0.85" />
                  <circle cx={p.x} cy={p.y} r="3.8" fill="none" stroke="#8B3A3A" strokeWidth="0.4" opacity="0.3" />
                </motion.g>
              ))}

              {/* Striker run trail */}
              <motion.line
                x1={strikerOriginX}
                y1={strikerOriginY}
                x2={xs[10] as any}
                y2={ys[10] as any}
                stroke="#C8612A" strokeWidth="0.7" strokeDasharray="1.5 1.5"
                style={{ opacity: runTrailOp }}
              />

              {/* CB tracking trail */}
              <motion.line
                x1={cbOriginX}
                y1={cbOriginY}
                x2={xs[3] as any}
                y2={ys[3] as any}
                stroke="#8C7A63" strokeWidth="0.7" strokeDasharray="1.5 1.5"
                style={{ opacity: cbTrailOp }}
              />

              {/* CB popup */}
              <motion.g style={{ opacity: cbPopOp }}>
                <rect x="43" y="56" width="38" height="9" rx="1.5"
                  fill="#F7F3EE" stroke="#C8B89A" strokeWidth="0.4" />
                <text x="62" y="62" textAnchor="middle"
                  fontSize="2.5" fill="#C8612A" fontFamily="monospace" fontWeight="500">
                  follows his man
                </text>
              </motion.g>

              {/* Player nodes with jersey numbers */}
              {F442.map((p, i) => (
                <motion.g key={`p-${i}`}>
                  {/* Outer ring */}
                  <motion.circle
                    r="4.2" fill="none"
                    stroke={ROLE_COLORS[p.role]} strokeWidth="0.35" opacity={0.35}
                    style={{ cx: xs[i], cy: ys[i] }}
                  />
                  {/* Filled node */}
                  <motion.circle
                    r="3.2"
                    fill={ROLE_COLORS[p.role]}
                    opacity={0.92}
                    style={{ cx: xs[i], cy: ys[i] }}
                  />
                  {/* Jersey number */}
                  <motion.text
                    textAnchor="middle"
                    dominantBaseline="central"
                    fontSize="2.5"
                    fontWeight="700"
                    fill="#ffffff"
                    fontFamily="monospace"
                    style={{ x: xs[i], y: ys[i] }}
                  >
                    {p.n}
                  </motion.text>

                  {/* Good form arrow (step 1) */}
                  {GOOD_FORM.includes(i) && (
                    <motion.text
                      textAnchor="middle"
                      fontSize="4"
                      fill="#5A8A6A"
                      fontWeight="bold"
                      style={{
                        x: xs[i],
                        y: useTransform(ys[i], v => v - 6),
                        opacity: s1op,
                      }}
                    >
                      ↑
                    </motion.text>
                  )}
                </motion.g>
              ))}

              {/* Attribute popups (step 1) */}
              {POPUPS.map((popup) => (
                <motion.g key={`popup-${popup.idx}`} style={{ opacity: s1op }}>
                  <motion.rect
                    width="26" height="13" rx="1.5"
                    fill="#F7F3EE" stroke="#C8B89A" strokeWidth="0.4"
                    style={{
                      x: useTransform(xs[popup.idx], v => v + 4),
                      y: useTransform(ys[popup.idx], v => v - 15),
                    }}
                  />
                  <motion.text
                    textAnchor="middle" fontSize="2.3"
                    fill="#3D3530" fontFamily="monospace" fontWeight="500"
                    style={{
                      x: useTransform(xs[popup.idx], v => v + 17),
                      y: useTransform(ys[popup.idx], v => v - 11),
                    }}
                  >
                    {popup.label}
                  </motion.text>
                  {popup.attrs.map((attr, ai) => (
                    <motion.text
                      key={ai}
                      textAnchor="middle" fontSize="2"
                      fill="#8C7A63" fontFamily="monospace"
                      style={{
                        x: useTransform(xs[popup.idx], v => v + 17),
                        y: useTransform(ys[popup.idx], v => v - 7.8 + ai * 2.8),
                      }}
                    >
                      {attr}
                    </motion.text>
                  ))}
                </motion.g>
              ))}

            </svg>
          </div>
        </div>

      </div>
    </section>
  )
}