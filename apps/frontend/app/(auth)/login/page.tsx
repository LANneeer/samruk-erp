'use client'

import Link from 'next/link'
import { AuthProvider } from '@/components/auth/auth-provider'
import { LoginForm } from '@/components/auth/login-form'
import { FileSpreadsheet } from 'lucide-react'

export default function LoginPage() {
  return (
    <AuthProvider>
      <div className="flex min-h-screen flex-col items-center justify-center bg-background p-4">
        <Link href="/" className="mb-8 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary">
            <FileSpreadsheet className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">Samruk-Kazyna</h1>
            <p className="text-xs text-muted-foreground">Reports Portal</p>
          </div>
        </Link>
        <LoginForm />
        <p className="mt-8 text-center text-xs text-muted-foreground">
          Demo credentials: admin@samruk.kz / password123
        </p>
      </div>
    </AuthProvider>
  )
}
