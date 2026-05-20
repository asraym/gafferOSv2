import AppNavbar from '@/components/app/AppNavbar'
import styles from './layout.module.css'

export default function AppLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className={styles.shell}>
      <AppNavbar />
      <main className={styles.main}>
        {children}
      </main>
    </div>
  )
}