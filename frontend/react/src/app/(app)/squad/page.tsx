'use client'

import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { getPlayers, importPlayersCSV, uploadPhysicalCSV } from '@/lib/api'
import styles from './squad.module.css'

export default function Squad() {
  const [players, setPlayers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [csvMode, setCsvMode] = useState<'squad' | 'physical' | null>(null)
  const [csvFile, setCsvFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploadResult, setUploadResult] = useState<any>(null)

  async function load() {
    try {
      const data: any = await getPlayers()
      setPlayers(Array.isArray(data) ? data : [])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  async function handleUpload() {
    if (!csvFile || !csvMode) return
    setUploading(true)
    setUploadResult(null)
    try {
      const fd = new FormData()
      fd.append('file', csvFile)
      const result = csvMode === 'squad'
        ? await importPlayersCSV(fd)
        : await uploadPhysicalCSV(fd)
      setUploadResult(result)
      await load()
    } catch (e: any) {
      setUploadResult({ error: e.message })
    } finally {
      setUploading(false)
      setCsvFile(null)
    }
  }

  const POSITION_ORDER = ['GK', 'DEF', 'MID', 'FWD']
  const grouped = POSITION_ORDER.reduce((acc, pos) => {
    acc[pos] = players.filter((p: any) => p.broad_position === pos || p.position === pos)
    return acc
  }, {} as Record<string, any[]>)

  return (
    <div className={styles.page}>

      <div className={styles.header}>
        <div>
          <p className={styles.pageLabel}>Season 2024-25</p>
          <h1 className={styles.pageTitle}>Squad</h1>
        </div>
        <div className={styles.headerActions}>
          <button
            className={styles.btnGhost}
            onClick={() => setCsvMode(csvMode === 'physical' ? null : 'physical')}
          >
            Physical CSV
          </button>
          <button
            className={styles.btnPrimary}
            onClick={() => setCsvMode(csvMode === 'squad' ? null : 'squad')}
          >
            Import squad
          </button>
        </div>
      </div>

      {csvMode && (
        <motion.div
          className={styles.uploadBox}
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
        >
          <p className={styles.uploadLabel}>
            {csvMode === 'squad' ? 'Upload squad CSV' : 'Upload physical assessment CSV'}
          </p>
          <div className={styles.uploadRow}>
            <input
              type="file"
              accept=".csv"
              className={styles.fileInput}
              onChange={e => setCsvFile(e.target.files?.[0] || null)}
            />
            <button
              className={styles.btnPrimary}
              onClick={handleUpload}
              disabled={!csvFile || uploading}
            >
              {uploading ? 'Uploading...' : 'Upload'}
            </button>
            <button
              className={styles.btnGhost}
              onClick={() => { setCsvMode(null); setUploadResult(null) }}
            >
              Cancel
            </button>
          </div>
          {uploadResult && (
            <div className={styles.uploadResult}>
              {uploadResult.error
                ? <span className={styles.resultError}>{uploadResult.error}</span>
                : <span className={styles.resultSuccess}>
                    ✓ {uploadResult.imported || uploadResult.processed || 0} records processed
                    {uploadResult.errors?.length > 0 && ` · ${uploadResult.errors.length} skipped`}
                  </span>
              }
            </div>
          )}
        </motion.div>
      )}

      {loading ? (
        <div className={styles.loadingState}>
          <p className={styles.loadingText}>Loading squad...</p>
        </div>
      ) : players.length === 0 ? (
        <div className={styles.emptyState}>
          <p className={styles.emptyTitle}>No players registered yet.</p>
          <p className={styles.emptyDesc}>Import a squad CSV to get started.</p>
        </div>
      ) : (
        <div className={styles.groups}>
          {POSITION_ORDER.map(pos => {
            const group = grouped[pos]
            if (!group || group.length === 0) return null
            return (
              <div key={pos} className={styles.group}>
                <div className={styles.groupHeader}>
                  <span className={styles.groupLabel}>{pos}</span>
                  <span className={styles.groupCount}>{group.length}</span>
                </div>
                <div className={styles.playerList}>
                  {group.map((p: any, i: number) => (
                    <motion.div
                      key={p.player_id || i}
                      className={styles.playerRow}
                      initial={{ opacity: 0, y: 8 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.04 }}
                    >
                      <div className={styles.playerLeft}>
                        <span className={styles.jersey}>
                          {p.jersey_number || '—'}
                        </span>
                        <div className={styles.playerInfo}>
                          <span className={styles.playerName}>{p.name}</span>
                          <span className={styles.playerPos}>
                            {p.specific_position || p.position}
                          </span>
                        </div>
                      </div>

                      <div className={styles.playerStats}>
                        {p.overall_rating && (
                          <div className={styles.stat}>
                            <span className={styles.statVal}>
                              {p.overall_rating.toFixed(1)}
                            </span>
                            <span className={styles.statLabel}>Overall</span>
                          </div>
                        )}
                        {p.role_rating && (
                          <div className={styles.stat}>
                            <span className={styles.statVal}>
                              {p.role_rating.toFixed(1)}
                            </span>
                            <span className={styles.statLabel}>Role</span>
                          </div>
                        )}
                        {p.form_score != null && (
                          <div className={styles.stat}>
                            <span className={styles.statVal}>
                              {(p.form_score * 100).toFixed(0)}%
                            </span>
                            <span className={styles.statLabel}>Form</span>
                          </div>
                        )}
                      </div>

                      <div className={styles.playerTraits}>
                        {(p.traits || []).slice(0, 2).map((t: string) => (
                          <span key={t} className={styles.trait}>{t}</span>
                        ))}
                      </div>

                      <div className={styles.playerRight}>
                        <span className={`${styles.availBadge} ${p.is_active === false ? styles.unavail : ''}`}>
                          {p.is_active === false ? 'Unavailable' : 'Available'}
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )
          })}
        </div>
      )}

    </div>
  )
}