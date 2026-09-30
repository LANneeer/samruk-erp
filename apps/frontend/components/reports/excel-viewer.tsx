'use client'

import { useState, useEffect, useMemo } from 'react'
import * as XLSX from 'xlsx'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area'
import { Download, ChevronLeft, ChevronRight } from 'lucide-react'

interface ExcelViewerProps {
  data: ArrayBuffer | null
  fileName?: string
  isLoading?: boolean
  error?: string | null
  onDownload?: () => void
}

interface SheetData {
  name: string
  data: (string | number | boolean | null)[][]
  merges?: XLSX.Range[]
}

export function ExcelViewer({
  data,
  fileName,
  isLoading,
  error,
  onDownload,
}: ExcelViewerProps) {
  const [activeSheet, setActiveSheet] = useState(0)
  const [sheets, setSheets] = useState<SheetData[]>([])

  useEffect(() => {
    if (!data) {
      setSheets([])
      return
    }

    try {
      const workbook = XLSX.read(data, { type: 'array' })
      const parsedSheets: SheetData[] = workbook.SheetNames.map((name) => {
        const sheet = workbook.Sheets[name]
        const jsonData = XLSX.utils.sheet_to_json<(string | number | boolean | null)[]>(sheet, {
          header: 1,
          defval: null,
        })
        return {
          name,
          data: jsonData,
          merges: sheet['!merges'],
        }
      })
      setSheets(parsedSheets)
      setActiveSheet(0)
    } catch (err) {
      console.error('Failed to parse Excel file:', err)
      setSheets([])
    }
  }, [data])

  const currentSheet = sheets[activeSheet]

  // Calculate column widths based on content
  const columnWidths = useMemo(() => {
    if (!currentSheet?.data || currentSheet.data.length === 0) return []
    
    const maxCols = Math.max(...currentSheet.data.map(row => row?.length || 0))
    const widths: number[] = new Array(maxCols).fill(80)
    
    currentSheet.data.forEach(row => {
      row?.forEach((cell, colIndex) => {
        if (cell != null) {
          const cellWidth = Math.min(String(cell).length * 8 + 24, 300)
          widths[colIndex] = Math.max(widths[colIndex], cellWidth)
        }
      })
    })
    
    return widths
  }, [currentSheet])

  if (isLoading) {
    return (
      <div className="flex h-96 items-center justify-center rounded-lg border border-border bg-card">
        <div className="flex flex-col items-center gap-3">
          <Spinner className="h-8 w-8" />
          <p className="text-sm text-muted-foreground">Loading document...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-96 items-center justify-center rounded-lg border border-destructive/20 bg-destructive/5">
        <div className="text-center">
          <p className="text-sm font-medium text-destructive">Failed to load document</p>
          <p className="mt-1 text-xs text-muted-foreground">{error}</p>
        </div>
      </div>
    )
  }

  if (!data || sheets.length === 0) {
    return (
      <div className="flex h-96 items-center justify-center rounded-lg border border-border bg-card">
        <p className="text-sm text-muted-foreground">No data to display</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col rounded-lg border border-border bg-card overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between border-b border-border bg-muted/30 px-4 py-2">
        <div className="flex items-center gap-2">
          {sheets.length > 1 && (
            <>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                disabled={activeSheet === 0}
                onClick={() => setActiveSheet((prev) => prev - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <span className="text-sm text-muted-foreground">
                Sheet {activeSheet + 1} of {sheets.length}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7"
                disabled={activeSheet === sheets.length - 1}
                onClick={() => setActiveSheet((prev) => prev + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </>
          )}
        </div>
        {onDownload && (
          <Button variant="outline" size="sm" onClick={onDownload}>
            <Download className="mr-2 h-4 w-4" />
            Download
          </Button>
        )}
      </div>

      {/* Sheet tabs */}
      {sheets.length > 1 && (
        <div className="flex overflow-x-auto border-b border-border bg-muted/20">
          {sheets.map((sheet, index) => (
            <button
              key={sheet.name}
              onClick={() => setActiveSheet(index)}
              className={cn(
                'shrink-0 border-r border-border px-4 py-2 text-sm transition-colors',
                index === activeSheet
                  ? 'bg-card font-medium text-foreground'
                  : 'text-muted-foreground hover:bg-muted/50 hover:text-foreground'
              )}
            >
              {sheet.name}
            </button>
          ))}
        </div>
      )}

      {/* Spreadsheet content */}
      <ScrollArea className="h-[500px]">
        <div className="min-w-max">
          <table className="w-full border-collapse text-sm">
            <tbody>
              {currentSheet?.data.map((row, rowIndex) => (
                <tr key={rowIndex} className="border-b border-border last:border-b-0">
                  {/* Row number */}
                  <td className="sticky left-0 z-10 min-w-[40px] border-r border-border bg-muted px-2 py-1.5 text-center text-xs font-medium text-muted-foreground">
                    {rowIndex + 1}
                  </td>
                  {Array.from({ length: Math.max(...currentSheet.data.map(r => r?.length || 0)) }).map((_, colIndex) => {
                    const cellValue = row?.[colIndex]
                    const isNumber = typeof cellValue === 'number'
                    
                    return (
                      <td
                        key={colIndex}
                        className={cn(
                          'border-r border-border px-3 py-1.5 last:border-r-0',
                          rowIndex === 0 && 'bg-muted/50 font-medium',
                          isNumber && 'text-right tabular-nums'
                        )}
                        style={{ minWidth: columnWidths[colIndex] || 80 }}
                      >
                        {cellValue != null ? String(cellValue) : ''}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  )
}
