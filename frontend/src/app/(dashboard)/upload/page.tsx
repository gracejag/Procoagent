'use client'

import { useState, useEffect } from 'react'
import { Upload, FileSpreadsheet, PenLine, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import Header from '@/components/header'
import CsvUpload from '@/components/csv-upload'
import TransactionForm from '@/components/transaction-form'
import TransactionTable from '@/components/transaction-table'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useToast } from '@/components/ui/use-toast'

interface Business {
  id: number
  name: string
  business_type: string | null
}

export default function UploadPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [refreshTrigger, setRefreshTrigger] = useState(0)
  const { toast } = useToast()

  useEffect(() => {
    const fetchBusinesses = async () => {
      try {
        const response = await api.get('/business/')
        setBusinesses(response.data)
        if (response.data.length > 0) {
          setSelectedBusinessId(response.data[0].id)
        }
      } catch (error) {
        console.error('Failed to fetch businesses:', error)
        toast({
          title: 'Error',
          description: 'Failed to load businesses. Please try again.',
          variant: 'destructive',
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchBusinesses()
  }, [toast])

  const handleUploadSuccess = (count: number) => {
    toast({
      title: 'Upload successful',
      description: `${count} transactions have been imported.`,
    })
    setRefreshTrigger((prev) => prev + 1)
  }

  const handleTransactionSuccess = () => {
    setRefreshTrigger((prev) => prev + 1)
  }

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (businesses.length === 0) {
    return (
      <div className="min-h-screen">
        <Header />
        <div className="flex flex-col items-center justify-center p-8">
          <div className="text-center">
            <Upload className="mx-auto h-12 w-12 text-muted-foreground" />
            <h2 className="mt-4 text-xl font-semibold">No business found</h2>
            <p className="mt-2 text-muted-foreground">
              Please complete the onboarding process to set up your business first.
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Header />
      <div className="p-8">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-3xl font-bold">Upload Data</h1>
            <p className="text-muted-foreground">
              Import transactions via CSV or add them manually
            </p>
          </div>
          {businesses.length > 1 && (
            <div className="w-full sm:w-64">
              <Select
                value={selectedBusinessId?.toString()}
                onValueChange={(value) => setSelectedBusinessId(parseInt(value))}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select business" />
                </SelectTrigger>
                <SelectContent>
                  {businesses.map((business) => (
                    <SelectItem key={business.id} value={business.id.toString()}>
                      {business.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        <div className="grid gap-8 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Add Transactions
              </CardTitle>
              <CardDescription>
                Choose how you want to add transaction data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="csv" className="w-full">
                <TabsList className="grid w-full grid-cols-2">
                  <TabsTrigger value="csv" className="flex items-center gap-2">
                    <FileSpreadsheet className="h-4 w-4" />
                    CSV Upload
                  </TabsTrigger>
                  <TabsTrigger value="manual" className="flex items-center gap-2">
                    <PenLine className="h-4 w-4" />
                    Manual Entry
                  </TabsTrigger>
                </TabsList>
                <TabsContent value="csv" className="mt-4">
                  {selectedBusinessId && (
                    <CsvUpload
                      businessId={selectedBusinessId}
                      onSuccess={handleUploadSuccess}
                    />
                  )}
                </TabsContent>
                <TabsContent value="manual" className="mt-4">
                  {selectedBusinessId && (
                    <TransactionForm
                      businessId={selectedBusinessId}
                      onSuccess={handleTransactionSuccess}
                    />
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
              <CardDescription>
                Overview of your transaction data
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-sm text-muted-foreground">Upload CSV</p>
                  <p className="mt-1 text-2xl font-bold text-primary">Bulk Import</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Upload multiple transactions at once
                  </p>
                </div>
                <div className="rounded-lg bg-slate-50 p-4">
                  <p className="text-sm text-muted-foreground">Manual Entry</p>
                  <p className="mt-1 text-2xl font-bold text-primary">Single Add</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    Add transactions one at a time
                  </p>
                </div>
              </div>
              <div className="mt-4 rounded-lg border border-dashed p-4">
                <h4 className="font-medium">Tips for CSV Upload</h4>
                <ul className="mt-2 list-inside list-disc text-sm text-muted-foreground">
                  <li>Use columns: amount, date, customer_id, category</li>
                  <li>Date format: YYYY-MM-DD (e.g., 2024-01-15)</li>
                  <li>Amount should be numeric (e.g., 150.00)</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Transaction History</CardTitle>
            <CardDescription>
              View and manage your imported transactions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedBusinessId && (
              <TransactionTable
                businessId={selectedBusinessId}
                refreshTrigger={refreshTrigger}
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
