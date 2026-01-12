'use client'

import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import {
  User,
  Building2,
  Bell,
  Loader2,
  Save,
} from 'lucide-react'
import { api } from '@/lib/api'
import { useAuth } from '@/contexts/auth-context'
import Header from '@/components/header'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useToast } from '@/components/ui/use-toast'
import { Separator } from '@/components/ui/separator'

const businessTypes = [
  { value: 'restaurant', label: 'Restaurant' },
  { value: 'retail', label: 'Retail Store' },
  { value: 'salon', label: 'Salon / Spa' },
  { value: 'fitness', label: 'Fitness / Gym' },
  { value: 'healthcare', label: 'Healthcare' },
  { value: 'professional', label: 'Professional Services' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'other', label: 'Other' },
]

const profileSchema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters'),
  email: z.string().email('Please enter a valid email address'),
})

const businessSchema = z.object({
  name: z.string().min(2, 'Business name must be at least 2 characters'),
  business_type: z.string().optional(),
  address: z.string().optional(),
  phone: z.string().optional(),
})

type ProfileFormValues = z.infer<typeof profileSchema>
type BusinessFormValues = z.infer<typeof businessSchema>

interface Business {
  id: number
  name: string
  business_type: string | null
  address: string | null
  phone: string | null
}

export default function SettingsPage() {
  const { user } = useAuth()
  const { toast } = useToast()
  const [businesses, setBusinesses] = useState<Business[]>([])
  const [selectedBusiness, setSelectedBusiness] = useState<Business | null>(null)
  const [isLoadingProfile, setIsLoadingProfile] = useState(false)
  const [isLoadingBusiness, setIsLoadingBusiness] = useState(false)
  const [isLoadingData, setIsLoadingData] = useState(true)

  const profileForm = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      name: '',
      email: '',
    },
  })

  const businessForm = useForm<BusinessFormValues>({
    resolver: zodResolver(businessSchema),
    defaultValues: {
      name: '',
      business_type: '',
      address: '',
      phone: '',
    },
  })

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [businessesRes] = await Promise.all([
          api.get('/business/'),
        ])

        setBusinesses(businessesRes.data)
        if (businessesRes.data.length > 0) {
          setSelectedBusiness(businessesRes.data[0])
          businessForm.reset({
            name: businessesRes.data[0].name,
            business_type: businessesRes.data[0].business_type || '',
            address: businessesRes.data[0].address || '',
            phone: businessesRes.data[0].phone || '',
          })
        }

        if (user) {
          profileForm.reset({
            name: user.name,
            email: user.email,
          })
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setIsLoadingData(false)
      }
    }

    fetchData()
  }, [user])

  const onProfileSubmit = async (data: ProfileFormValues) => {
    setIsLoadingProfile(true)
    try {
      await api.put('/auth/profile', data)
      toast({
        title: 'Profile updated',
        description: 'Your profile has been updated successfully.',
      })
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update profile.',
        variant: 'destructive',
      })
    } finally {
      setIsLoadingProfile(false)
    }
  }

  const onBusinessSubmit = async (data: BusinessFormValues) => {
    if (!selectedBusiness) return

    setIsLoadingBusiness(true)
    try {
      const response = await api.put(`/business/${selectedBusiness.id}`, data)
      setSelectedBusiness(response.data)
      setBusinesses((prev) =>
        prev.map((b) => (b.id === selectedBusiness.id ? response.data : b))
      )
      toast({
        title: 'Business updated',
        description: 'Your business details have been updated successfully.',
      })
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.response?.data?.detail || 'Failed to update business.',
        variant: 'destructive',
      })
    } finally {
      setIsLoadingBusiness(false)
    }
  }

  const handleBusinessSelect = (businessId: string) => {
    const business = businesses.find((b) => b.id === parseInt(businessId))
    if (business) {
      setSelectedBusiness(business)
      businessForm.reset({
        name: business.name,
        business_type: business.business_type || '',
        address: business.address || '',
        phone: business.phone || '',
      })
    }
  }

  if (isLoadingData) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <Header />
      <div className="p-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-muted-foreground">
            Manage your account and business settings
          </p>
        </div>

        <Tabs defaultValue="profile" className="space-y-6">
          <TabsList>
            <TabsTrigger value="profile" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              Profile
            </TabsTrigger>
            <TabsTrigger value="business" className="flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Business
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Notifications
            </TabsTrigger>
          </TabsList>

          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Profile Settings</CardTitle>
                <CardDescription>
                  Update your personal information
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Form {...profileForm}>
                  <form
                    onSubmit={profileForm.handleSubmit(onProfileSubmit)}
                    className="space-y-4"
                  >
                    <FormField
                      control={profileForm.control}
                      name="name"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Full Name</FormLabel>
                          <FormControl>
                            <Input placeholder="John Doe" {...field} />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <FormField
                      control={profileForm.control}
                      name="email"
                      render={({ field }) => (
                        <FormItem>
                          <FormLabel>Email</FormLabel>
                          <FormControl>
                            <Input
                              type="email"
                              placeholder="you@example.com"
                              {...field}
                            />
                          </FormControl>
                          <FormMessage />
                        </FormItem>
                      )}
                    />
                    <Separator className="my-4" />
                    <Button type="submit" disabled={isLoadingProfile}>
                      {isLoadingProfile ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="mr-2 h-4 w-4" />
                          Save Changes
                        </>
                      )}
                    </Button>
                  </form>
                </Form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="business">
            <Card>
              <CardHeader>
                <CardTitle>Business Settings</CardTitle>
                <CardDescription>
                  Manage your business information
                </CardDescription>
              </CardHeader>
              <CardContent>
                {businesses.length > 1 && (
                  <div className="mb-6">
                    <label className="text-sm font-medium">Select Business</label>
                    <Select
                      value={selectedBusiness?.id.toString()}
                      onValueChange={handleBusinessSelect}
                    >
                      <SelectTrigger className="mt-2">
                        <SelectValue placeholder="Select a business" />
                      </SelectTrigger>
                      <SelectContent>
                        {businesses.map((business) => (
                          <SelectItem
                            key={business.id}
                            value={business.id.toString()}
                          >
                            {business.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Separator className="my-6" />
                  </div>
                )}

                {selectedBusiness ? (
                  <Form {...businessForm}>
                    <form
                      onSubmit={businessForm.handleSubmit(onBusinessSubmit)}
                      className="space-y-4"
                    >
                      <FormField
                        control={businessForm.control}
                        name="name"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Business Name</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="e.g., Joe's Coffee Shop"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={businessForm.control}
                        name="business_type"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Business Type</FormLabel>
                            <Select
                              onValueChange={field.onChange}
                              value={field.value}
                            >
                              <FormControl>
                                <SelectTrigger>
                                  <SelectValue placeholder="Select business type" />
                                </SelectTrigger>
                              </FormControl>
                              <SelectContent>
                                {businessTypes.map((type) => (
                                  <SelectItem key={type.value} value={type.value}>
                                    {type.label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={businessForm.control}
                        name="address"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Address</FormLabel>
                            <FormControl>
                              <Input
                                placeholder="123 Main St, City, State"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <FormField
                        control={businessForm.control}
                        name="phone"
                        render={({ field }) => (
                          <FormItem>
                            <FormLabel>Phone Number</FormLabel>
                            <FormControl>
                              <Input
                                type="tel"
                                placeholder="(555) 123-4567"
                                {...field}
                              />
                            </FormControl>
                            <FormMessage />
                          </FormItem>
                        )}
                      />
                      <Separator className="my-4" />
                      <Button type="submit" disabled={isLoadingBusiness}>
                        {isLoadingBusiness ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="mr-2 h-4 w-4" />
                            Save Changes
                          </>
                        )}
                      </Button>
                    </form>
                  </Form>
                ) : (
                  <p className="text-muted-foreground">
                    No business found. Please complete onboarding first.
                  </p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="notifications">
            <Card>
              <CardHeader>
                <CardTitle>Notification Settings</CardTitle>
                <CardDescription>
                  Configure how you receive alerts and updates
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Email Notifications</p>
                      <p className="text-sm text-muted-foreground">
                        Receive alerts via email
                      </p>
                    </div>
                    <Button variant="outline" disabled>
                      Coming Soon
                    </Button>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">SMS Notifications</p>
                      <p className="text-sm text-muted-foreground">
                        Receive alerts via SMS
                      </p>
                    </div>
                    <Button variant="outline" disabled>
                      Coming Soon
                    </Button>
                  </div>
                  <div className="flex items-center justify-between rounded-lg border p-4">
                    <div>
                      <p className="font-medium">Revenue Drop Alerts</p>
                      <p className="text-sm text-muted-foreground">
                        Get notified when revenue drops significantly
                      </p>
                    </div>
                    <Button variant="outline" disabled>
                      Coming Soon
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
