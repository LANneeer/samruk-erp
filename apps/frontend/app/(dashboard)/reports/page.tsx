'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import useSWR from 'swr'
import { listDocuments, type Document } from '@/lib/documents-api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Empty } from '@/components/ui/empty'
import { Spinner } from '@/components/ui/spinner'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { FileSpreadsheet, Search, Plus, ExternalLink, Calendar, FileText } from 'lucide-react'

export default function ReportsPage() {
  const [searchQuery, setSearchQuery] = useState('')
  
  const { data: documents, error, isLoading } = useSWR<Document[]>(
    'documents',
    () => listDocuments(0, 100),
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
    }
  )

  // Sort by created_at (newest first) and filter by search
  const filteredDocuments = documents
    ?.filter((doc) => {
      if (!searchQuery) return true
      const query = searchQuery.toLowerCase()
      return (
        doc.title.toLowerCase().includes(query) ||
        doc.file_name.toLowerCase().includes(query)
      )
    })
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  const getFileExtension = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    return ext || 'file'
  }

  return (
    <div className="p-6">
      <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Reports</h1>
          <p className="text-sm text-muted-foreground">
            Manage and view Excel reports from portfolio companies
          </p>
        </div>
        <Link href="/upload">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Upload Report
          </Button>
        </Link>
      </div>

      <Card>
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-lg">All Documents</CardTitle>
              <CardDescription>
                {filteredDocuments?.length || 0} document{filteredDocuments?.length !== 1 ? 's' : ''} found
              </CardDescription>
            </div>
            <div className="relative w-full sm:w-72">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search reports..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Spinner className="h-8 w-8" />
            </div>
          ) : error ? (
            <div className="rounded-lg border border-destructive/20 bg-destructive/5 p-6 text-center">
              <p className="text-sm text-destructive">
                Failed to load documents. Please check your API connection.
              </p>
              <p className="mt-2 text-xs text-muted-foreground">
                Make sure NEXT_PUBLIC_DOCUMENTS_API_URL is configured correctly.
              </p>
            </div>
          ) : !filteredDocuments || filteredDocuments.length === 0 ? (
            <Empty
              icon={<FileSpreadsheet className="h-10 w-10" />}
              title="No documents found"
              description={
                searchQuery
                  ? 'Try adjusting your search query'
                  : 'Upload your first report to get started'
              }
              action={
                !searchQuery && (
                  <Link href="/upload">
                    <Button>
                      <Plus className="mr-2 h-4 w-4" />
                      Upload Report
                    </Button>
                  </Link>
                )
              }
            />
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[50%]">Document</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredDocuments.map((doc) => (
                    <TableRow key={doc.id}>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                            <FileText className="h-5 w-5 text-primary" />
                          </div>
                          <div className="min-w-0">
                            <p className="font-medium text-foreground truncate">
                              {doc.title}
                            </p>
                            <p className="text-xs text-muted-foreground truncate">
                              {doc.file_name}
                            </p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="uppercase">
                          {getFileExtension(doc.file_name)}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                          <Calendar className="h-3.5 w-3.5" />
                          {formatDate(doc.created_at)}
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <Link href={`/reports/${doc.id}`}>
                          <Button variant="ghost" size="sm">
                            <ExternalLink className="mr-1.5 h-3.5 w-3.5" />
                            View
                          </Button>
                        </Link>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
