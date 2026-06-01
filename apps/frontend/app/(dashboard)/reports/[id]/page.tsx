'use client'

import { useState, useEffect, use } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import useSWR from 'swr'
import { getDocument, downloadDocument, deleteDocument, type Document } from '@/lib/documents-api'
import { ExcelViewer } from '@/components/reports/excel-viewer'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Spinner } from '@/components/ui/spinner'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { ArrowLeft, Calendar, FileText, Trash2, Download, User } from 'lucide-react'
import { ChatPanel } from '@/components/ai/chat-panel'

export default function ReportDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const { id } = use(params)
  const router = useRouter()
  const [fileData, setFileData] = useState<ArrayBuffer | null>(null)
  const [fileLoading, setFileLoading] = useState(true)
  const [fileError, setFileError] = useState<string | null>(null)
  const [isDeleting, setIsDeleting] = useState(false)

  const { data: document, error: docError, isLoading: docLoading } = useSWR<Document>(
    id ? `document-${id}` : null,
    () => getDocument(id),
    { revalidateOnFocus: false }
  )

  // Load the file data
  useEffect(() => {
    async function loadFile() {
      if (!id) return
      
      setFileLoading(true)
      setFileError(null)
      
      try {
        const blob = await downloadDocument(id)
        const arrayBuffer = await blob.arrayBuffer()
        setFileData(arrayBuffer)
      } catch (err) {
        console.error('Failed to download file:', err)
        setFileError('Failed to load the document file')
      } finally {
        setFileLoading(false)
      }
    }
    
    loadFile()
  }, [id])

  const handleDownload = async () => {
    if (!document) return
    
    try {
      const blob = await downloadDocument(id)
      const url = URL.createObjectURL(blob)
      const a = window.document.createElement('a')
      a.href = url
      a.download = document.file_name
      window.document.body.appendChild(a)
      a.click()
      window.document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const handleDelete = async () => {
    setIsDeleting(true)
    try {
      await deleteDocument(id)
      router.push('/reports')
    } catch (err) {
      console.error('Delete failed:', err)
      setIsDeleting(false)
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getFileExtension = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    return ext || 'file'
  }

  if (docLoading) {
    return (
      <div className="flex h-[calc(100vh-4rem)] items-center justify-center">
        <Spinner className="h-8 w-8" />
      </div>
    )
  }

  if (docError || !document) {
    return (
      <div className="flex h-[calc(100vh-4rem)] flex-col items-center justify-center gap-4">
        <p className="text-muted-foreground">Document not found or failed to load</p>
        <Link href="/reports">
          <Button variant="outline">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Back to Reports
          </Button>
        </Link>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/reports"
          className="mb-4 inline-flex items-center text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="mr-1.5 h-4 w-4" />
          Back to Reports
        </Link>
        
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-primary/10">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-foreground">{document.title}</h1>
              <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
                <span className="flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5" />
                  {document.file_name}
                </span>
                <Badge variant="secondary" className="uppercase">
                  {getFileExtension(document.file_name)}
                </Badge>
              </div>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleDownload}>
              <Download className="mr-2 h-4 w-4" />
              Download
            </Button>
            <AlertDialog>
              <AlertDialogTrigger asChild>
                <Button variant="destructive" disabled={isDeleting}>
                  {isDeleting ? <Spinner className="mr-2 h-4 w-4" /> : <Trash2 className="mr-2 h-4 w-4" />}
                  Delete
                </Button>
              </AlertDialogTrigger>
              <AlertDialogContent>
                <AlertDialogHeader>
                  <AlertDialogTitle>Delete Document</AlertDialogTitle>
                  <AlertDialogDescription>
                    Are you sure you want to delete this document? This action cannot be undone.
                  </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                  <AlertDialogCancel>Cancel</AlertDialogCancel>
                  <AlertDialogAction onClick={handleDelete}>Delete</AlertDialogAction>
                </AlertDialogFooter>
              </AlertDialogContent>
            </AlertDialog>
          </div>
        </div>

        {/* Metadata */}
        <div className="mt-4 flex flex-wrap gap-6 text-sm">
          <div className="flex items-center gap-2 text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span>Created: {formatDate(document.created_at)}</span>
          </div>
          <div className="flex items-center gap-2 text-muted-foreground">
            <User className="h-4 w-4" />
            <span>Author ID: {document.author_id.slice(0, 8)}...</span>
          </div>
        </div>
      </div>

      {/* Excel Viewer */}
      <ExcelViewer
        data={fileData}
        fileName={document.file_name}
        isLoading={fileLoading}
        error={fileError}
        onDownload={handleDownload}
      />

      {/* AI Assistant */}
      <ChatPanel 
        documentId={document.id} 
        documentTitle={document.title}
      />
    </div>
  )
}
