'use client'

import { useState, useEffect } from 'react'
import { Users, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'
import Header from '@/components/header'
import TransactionTable from '@/components/transaction-table'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
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

export default function CustomersPage() {
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusinessId, setSelectedBusinessId] = useState<number | null>(null)
  const [isLoading, setIsLoading] = useState(true)
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
            <Users className="mx-auto h-12 w-12 text-muted-foreground" />
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
            <h1 className="text-3xl font-bold">Customers & Transactions</h1>
            <p className="text-muted-foreground">
              View and manage all your customer transactions
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

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              All Transactions
            </CardTitle>
            <CardDescription>
              Complete history of all transactions for your business
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedBusinessId && (
              <TransactionTable businessId={selectedBusinessId} />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
