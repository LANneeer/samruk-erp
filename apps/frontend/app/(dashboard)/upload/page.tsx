'use client'

import { useState, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/components/auth/auth-provider'
import { createDocument } from '@/lib/documents-api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldLabel } from '@/components/ui/field'
import { Spinner } from '@/components/ui/spinner'
import { cn } from '@/lib/utils'
import { Upload, FileSpreadsheet, X, ArrowLeft, CheckCircle } from 'lucide-react'

const ACCEPTED_FILE_TYPES = [
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
  'application/vnd.ms-excel', // .xls
  'text/csv', // .csv
]

const ACCEPTED_EXTENSIONS = ['.xlsx', '.xls', '.csv']

export default function UploadPage() {
  const { user } = useAuth()
  const router = useRouter()
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  const [title, setTitle] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadSuccess, setUploadSuccess] = useState(false)
  const [error, setError] = useState('')

  const validateFile = (file: File): boolean => {
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError(`Invalid file type. Accepted formats: ${ACCEPTED_EXTENSIONS.join(', ')}`)
      return false
    }
    
    // 50MB limit
    if (file.size > 50 * 1024 * 1024) {
      setError('File size must be less than 50MB')
      return false
    }
    
    return true
  }

  const handleFileSelect = (selectedFile: File) => {
    setError('')
    if (validateFile(selectedFile)) {
      setFile(selectedFile)
      // Auto-fill title from filename if empty
      if (!title) {
        const nameWithoutExt = selectedFile.name.replace(/\.[^/.]+$/, '')
        setTitle(nameWithoutExt)
      }
    }
  }

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    
    const droppedFile = e.dataTransfer.files[0]
    if (droppedFile) {
      handleFileSelect(droppedFile)
    }
  }, [title])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      handleFileSelect(selectedFile)
    }
  }

  const handleRemoveFile = () => {
    setFile(null)
    setError('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!file) {
      setError('Please select a file to upload')
      return
    }
    
    if (!title.trim()) {
      setError('Please enter a title for the document')
      return
    }
    
    if (!user?.id) {
      setError('You must be logged in to upload documents')
      return
    }

    setIsUploading(true)
    setError('')

    try {
      const doc = await createDocument(file, title.trim(), user.id)
      setUploadSuccess(true)
      setTimeout(() => {
        router.push(`/reports/${doc.id}`)
      }, 1500)
    } catch (err) {
      console.error('Upload failed:', err)
      setError('Failed to upload document. Please check your API connection and try again.')
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  if (uploadSuccess) {
    return (
      <div className="flex min-h-[calc(100vh-4rem)] items-center justify-center p-6">
        <Card className="w-full max-w-md text-center">
          <CardContent className="pt-6">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
              <CheckCircle className="h-8 w-8 text-green-600" />
            </div>
            <h2 className="text-xl font-semibold text-foreground">Upload Successful</h2>
            <p className="mt-2 text-sm text-muted-foreground">
              Redirecting to your document...
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <Link
          href="/reports"
          className="mb-4 inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          Back to Reports
        </Link>
        <h1 className="text-2xl font-bold text-foreground">Upload Report</h1>
        <p className="text-sm text-muted-foreground">
          Upload an Excel document to the reports portal
        </p>
      </div>

      <Card className="max-w-2xl">
        <CardHeader>
          <CardTitle>Document Details</CardTitle>
          <CardDescription>
            Provide information about the report you&apos;re uploading
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {error && (
              <div className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
                {error}
              </div>
            )}

            <Field>
              <FieldLabel htmlFor="title">Document Title</FieldLabel>
              <Input
                id="title"
                type="text"
                placeholder="Enter document title"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
              />
            </Field>

            <Field>
              <FieldLabel>File</FieldLabel>
              {!file ? (
                <div
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onDrop={handleDrop}
                  onClick={() => fileInputRef.current?.click()}
                  className={cn(
                    'flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-8 transition-colors',
                    isDragging
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50 hover:bg-muted/50'
                  )}
                >
                  <Upload className="mb-4 h-10 w-10 text-muted-foreground" />
                  <p className="mb-1 text-sm font-medium text-foreground">
                    Drop your file here or click to browse
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Supports {ACCEPTED_EXTENSIONS.join(', ')} (max 50MB)
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED_EXTENSIONS.join(',')}
                    onChange={handleInputChange}
                    className="hidden"
                  />
                </div>
              ) : (
                <div className="flex items-center gap-3 rounded-lg border border-border bg-muted/30 p-4">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                    <FileSpreadsheet className="h-5 w-5 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-foreground truncate">{file.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={handleRemoveFile}
                    className="shrink-0"
                  >
                    <X className="h-4 w-4" />
                    <span className="sr-only">Remove file</span>
                  </Button>
                </div>
              )}
            </Field>

            <div className="flex gap-3">
              <Button
                type="submit"
                disabled={isUploading || !file}
                className="flex-1"
              >
                {isUploading ? (
                  <>
                    <Spinner className="mr-2" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload Document
                  </>
                )}
              </Button>
              <Link href="/reports">
                <Button type="button" variant="outline">
                  Cancel
                </Button>
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
