'use client'

import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, X, Loader2, CheckCircle2, AlertCircle } from 'lucide-react'
import { api } from '@/lib/api'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { cn } from '@/lib/utils'

interface CsvUploadProps {
  businessId: number
  onSuccess?: (count: number) => void
  onError?: (error: string) => void
}

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error'
  progress: number
  message: string
  count?: number
}

export default function CsvUpload({ businessId, onSuccess, onError }: CsvUploadProps) {
  const [file, setFile] = useState<File | null>(null)
  const [uploadState, setUploadState] = useState<UploadState>({
    status: 'idle',
    progress: 0,
    message: '',
  })

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFile(acceptedFiles[0])
      setUploadState({ status: 'idle', progress: 0, message: '' })
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
    },
    maxFiles: 1,
    onDrop,
  })

  const handleUpload = async () => {
    if (!file) return

    setUploadState({ status: 'uploading', progress: 10, message: 'Uploading...' })

    const formData = new FormData()
    formData.append('file', file)

    try {
      setUploadState({ status: 'uploading', progress: 50, message: 'Processing...' })

      const response = await api.post(`/transactions/upload/${businessId}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploadState({
        status: 'success',
        progress: 100,
        message: `Successfully imported ${response.data.imported} transactions`,
        count: response.data.imported,
      })

      onSuccess?.(response.data.imported)
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || 'Failed to upload file'
      setUploadState({
        status: 'error',
        progress: 0,
        message: errorMessage,
      })
      onError?.(errorMessage)
    }
  }

  const handleRemoveFile = () => {
    setFile(null)
    setUploadState({ status: 'idle', progress: 0, message: '' })
  }

  const handleReset = () => {
    setFile(null)
    setUploadState({ status: 'idle', progress: 0, message: '' })
  }

  return (
    <div className="space-y-4">
      {!file ? (
        <div
          {...getRootProps()}
          className={cn(
            'cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors',
            isDragActive && !isDragReject && 'border-primary bg-primary/5',
            isDragReject && 'border-destructive bg-destructive/5',
            !isDragActive && 'border-muted-foreground/25 hover:border-primary/50'
          )}
        >
          <input {...getInputProps()} />
          <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
          <p className="mt-4 text-lg font-medium">
            {isDragActive
              ? isDragReject
                ? 'Invalid file type'
                : 'Drop your CSV file here'
              : 'Drag & drop your CSV file here'}
          </p>
          <p className="mt-2 text-sm text-muted-foreground">
            or click to browse from your computer
          </p>
          <p className="mt-4 text-xs text-muted-foreground">
            Supported format: CSV with columns: amount, date, customer_id (optional), category (optional)
          </p>
        </div>
      ) : (
        <div className="rounded-lg border p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <File className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="font-medium">{file.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(file.size / 1024).toFixed(1)} KB
                </p>
              </div>
            </div>
            {uploadState.status === 'idle' && (
              <Button variant="ghost" size="icon" onClick={handleRemoveFile}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>

          {uploadState.status === 'uploading' && (
            <div className="mt-4 space-y-2">
              <Progress value={uploadState.progress} className="h-2" />
              <p className="text-sm text-muted-foreground">{uploadState.message}</p>
            </div>
          )}

          {uploadState.status === 'success' && (
            <div className="mt-4 flex items-center gap-2 rounded-lg bg-emerald-50 p-3 text-emerald-700">
              <CheckCircle2 className="h-5 w-5" />
              <p className="text-sm font-medium">{uploadState.message}</p>
            </div>
          )}

          {uploadState.status === 'error' && (
            <div className="mt-4 flex items-center gap-2 rounded-lg bg-destructive/10 p-3 text-destructive">
              <AlertCircle className="h-5 w-5" />
              <p className="text-sm font-medium">{uploadState.message}</p>
            </div>
          )}

          <div className="mt-4 flex gap-2">
            {uploadState.status === 'idle' && (
              <Button onClick={handleUpload} className="flex-1">
                <Upload className="mr-2 h-4 w-4" />
                Upload Transactions
              </Button>
            )}
            {uploadState.status === 'uploading' && (
              <Button disabled className="flex-1">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </Button>
            )}
            {(uploadState.status === 'success' || uploadState.status === 'error') && (
              <Button onClick={handleReset} variant="outline" className="flex-1">
                Upload Another File
              </Button>
            )}
          </div>
        </div>
      )}

      <div className="rounded-lg bg-slate-50 p-4">
        <h4 className="font-medium">CSV Format Requirements</h4>
        <p className="mt-2 text-sm text-muted-foreground">
          Your CSV file should include the following columns:
        </p>
        <ul className="mt-2 list-inside list-disc text-sm text-muted-foreground">
          <li>
            <strong>amount</strong> (required) - Transaction amount (e.g., 150.00)
          </li>
          <li>
            <strong>date</strong> (required) - Transaction date in ISO format (e.g., 2024-01-15)
          </li>
          <li>
            <strong>customer_id</strong> (optional) - Customer identifier
          </li>
          <li>
            <strong>category</strong> (optional) - Transaction category
          </li>
        </ul>
        <div className="mt-4 rounded bg-slate-100 p-3 font-mono text-xs">
          amount,date,customer_id,category<br />
          150.00,2024-01-15,CUST001,retail<br />
          75.50,2024-01-15,CUST002,food
        </div>
      </div>
    </div>
  )
}
