'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  ShoppingCart,
  AlertTriangle,
} from 'lucide-react'
import Header from '@/components/header'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'

interface DashboardStats {
  totalRevenue: number
  revenueChange: number
  totalCustomers: number
  customerChange: number
  totalTransactions: number
  transactionChange: number
  activeAlerts: number
}

interface RevenueDataPoint {
  date: string
  revenue: number
  projected: number
}

const mockStats: DashboardStats = {
  totalRevenue: 124500,
  revenueChange: -5.2,
  totalCustomers: 1420,
  customerChange: 2.1,
  totalTransactions: 3250,
  transactionChange: -1.8,
  activeAlerts: 3,
}

const mockRevenueData: RevenueDataPoint[] = [
  { date: 'Mon', revenue: 4200, projected: 4500 },
  { date: 'Tue', revenue: 3800, projected: 4200 },
  { date: 'Wed', revenue: 4500, projected: 4400 },
  { date: 'Thu', revenue: 4100, projected: 4300 },
  { date: 'Fri', revenue: 3600, projected: 4100 },
  { date: 'Sat', revenue: 5200, projected: 5000 },
  { date: 'Sun', revenue: 4800, projected: 4800 },
]

interface StatCardProps {
  title: string
  value: string | number
  change: number
  icon: React.ReactNode
  prefix?: string
}

function StatCard({ title, value, change, icon, prefix = '' }: StatCardProps) {
  const isPositive = change >= 0

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <div className="rounded-full bg-slate-100 p-2">{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {prefix}
          {typeof value === 'number' ? value.toLocaleString() : value}
        </div>
        <div className="flex items-center gap-1 text-xs">
          {isPositive ? (
            <TrendingUp className="h-3 w-3 text-green-500" />
          ) : (
            <TrendingDown className="h-3 w-3 text-red-500" />
          )}
          <span className={isPositive ? 'text-green-500' : 'text-red-500'}>
            {isPositive ? '+' : ''}
            {change}%
          </span>
          <span className="text-muted-foreground">from last week</span>
        </div>
      </CardContent>
    </Card>
  )
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>(mockStats)
  const [revenueData, setRevenueData] =
    useState<RevenueDataPoint[]>(mockRevenueData)

  return (
    <div className="flex flex-col">
      <Header title="Dashboard" />

      <div className="p-6">
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Revenue"
            value={stats.totalRevenue}
            change={stats.revenueChange}
            icon={<DollarSign className="h-4 w-4 text-slate-600" />}
            prefix="$"
          />
          <StatCard
            title="Total Customers"
            value={stats.totalCustomers}
            change={stats.customerChange}
            icon={<Users className="h-4 w-4 text-slate-600" />}
          />
          <StatCard
            title="Transactions"
            value={stats.totalTransactions}
            change={stats.transactionChange}
            icon={<ShoppingCart className="h-4 w-4 text-slate-600" />}
          />
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Alerts
              </CardTitle>
              <div className="rounded-full bg-red-100 p-2">
                <AlertTriangle className="h-4 w-4 text-red-600" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.activeAlerts}</div>
              <Badge variant="destructive" className="mt-2">
                Requires attention
              </Badge>
            </CardContent>
          </Card>
        </div>

        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Revenue Trend</CardTitle>
              <CardDescription>
                Daily revenue vs projected for the past week
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={revenueData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip
                      formatter={(value: number) => [
                        `$${value.toLocaleString()}`,
                        '',
                      ]}
                    />
                    <Area
                      type="monotone"
                      dataKey="projected"
                      stroke="#94a3b8"
                      fill="#f1f5f9"
                      strokeDasharray="5 5"
                      name="Projected"
                    />
                    <Area
                      type="monotone"
                      dataKey="revenue"
                      stroke="#0ea5e9"
                      fill="#e0f2fe"
                      name="Actual"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Alerts</CardTitle>
              <CardDescription>
                AI-detected anomalies requiring attention
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <div className="rounded-full bg-red-100 p-2">
                    <TrendingDown className="h-4 w-4 text-red-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Revenue drop detected</p>
                    <p className="text-sm text-muted-foreground">
                      15% decrease from the 7-day average on Friday
                    </p>
                    <Badge variant="destructive" className="mt-2">
                      High Priority
                    </Badge>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <div className="rounded-full bg-yellow-100 p-2">
                    <Users className="h-4 w-4 text-yellow-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Customer churn increase</p>
                    <p className="text-sm text-muted-foreground">
                      Returning customer rate down 8% this week
                    </p>
                    <Badge variant="warning" className="mt-2">
                      Medium Priority
                    </Badge>
                  </div>
                </div>
                <div className="flex items-start gap-3 rounded-lg border p-3">
                  <div className="rounded-full bg-blue-100 p-2">
                    <ShoppingCart className="h-4 w-4 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">Low transaction volume</p>
                    <p className="text-sm text-muted-foreground">
                      Tuesday transactions 20% below normal
                    </p>
                    <Badge variant="secondary" className="mt-2">
                      Low Priority
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
