'use client'

import Link from 'next/link'
import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { AuthProvider, useAuth } from '@/components/auth/auth-provider'
import { FileSpreadsheet, Shield, Bot, Upload } from 'lucide-react'

function LandingContent() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && user) {
      router.push('/reports')
    }
  }, [user, isLoading, router])

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
              <FileSpreadsheet className="h-6 w-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-foreground">Samruk-Kazyna</h1>
              <p className="text-xs text-muted-foreground">Reports Portal</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/login">
              <Button variant="ghost">Sign In</Button>
            </Link>
            <Link href="/signup">
              <Button>Get Started</Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden py-24">
        <div className="absolute inset-0 bg-gradient-to-b from-primary/5 to-transparent" />
        <div className="relative mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-balance text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Secure Document Management for Business Reports
            </h2>
            <p className="mt-6 text-pretty text-lg leading-relaxed text-muted-foreground">
              Verify integrity, analyze data, and manage Excel reports from Samruk-Kazyna Fund portfolio companies with AI-powered insights.
            </p>
            <div className="mt-10 flex items-center justify-center gap-4">
              <Link href="/signup">
                <Button size="lg" className="h-12 px-8">
                  Create Account
                </Button>
              </Link>
              <Link href="/login">
                <Button size="lg" variant="outline" className="h-12 px-8">
                  Sign In
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="border-t border-border bg-card py-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mx-auto max-w-2xl text-center">
            <h3 className="text-3xl font-bold text-foreground">
              Enterprise-Grade Document Management
            </h3>
            <p className="mt-4 text-muted-foreground">
              Everything you need to manage and verify business reports efficiently.
            </p>
          </div>
          <div className="mt-16 grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            <FeatureCard
              icon={<FileSpreadsheet className="h-6 w-6" />}
              title="Excel Viewer"
              description="View and analyze Excel reports directly in your browser with multi-sheet support."
            />
            <FeatureCard
              icon={<Shield className="h-6 w-6" />}
              title="Integrity Verification"
              description="Ensure document authenticity and track changes across report versions."
            />
            <FeatureCard
              icon={<Bot className="h-6 w-6" />}
              title="AI Assistant"
              description="Get intelligent insights and answers about your report data instantly."
            />
            <FeatureCard
              icon={<Upload className="h-6 w-6" />}
              title="Easy Upload"
              description="Upload and organize reports with automatic processing and indexing."
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-border bg-background py-8">
        <div className="mx-auto max-w-7xl px-6 text-center text-sm text-muted-foreground">
          <p>Samruk-Kazyna JSC - National Welfare Fund of Kazakhstan</p>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="rounded-xl border border-border bg-background p-6">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 text-primary">
        {icon}
      </div>
      <h4 className="font-semibold text-foreground">{title}</h4>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{description}</p>
    </div>
  )
}

export default function HomePage() {
  return (
    <AuthProvider>
      <LandingContent />
    </AuthProvider>
  )
}
