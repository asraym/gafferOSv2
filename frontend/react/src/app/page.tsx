import Navbar from '@/components/landing/Navbar'
import Hero from '@/components/landing/Hero'
import Features from '@/components/landing/Features'
import ScrollStory from '@/components/landing/ScrollStory'
import MomentumGraph from '@/components/landing/MomentumGraph'
import CTA from '@/components/landing/CTA'

export default function Home() {
  return (
    <main>
      <Navbar />
      <Hero />
      <Features />
      <ScrollStory />
      <MomentumGraph />
      <CTA />
    </main>
  )
}