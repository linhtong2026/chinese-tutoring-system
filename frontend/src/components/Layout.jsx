import { useState } from 'react'
import { useUser } from '@clerk/clerk-react'
import { UserButton } from '@clerk/clerk-react'
import { 
  LayoutDashboard,
  FileText,
  History,
  User,
  Menu,
  Calendar
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

function Layout({ children, currentPage, onPageChange, userData }) {
  const { user } = useUser()
  const [sidebarOpen, setSidebarOpen] = useState(true)

  const navigation = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'sessions', label: 'Sessions', icon: Calendar },
    { id: 'history', label: 'History', icon: History },
  ]

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className={cn(
        "transition-all duration-300 bg-card border-r border-border overflow-hidden flex flex-col",
        sidebarOpen ? "w-64" : "w-0"
      )}>
        <div className="p-6 border-b border-border">
          <h1 className="text-lg font-semibold text-foreground">
            Chinese Tutoring Platform
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Session Management
          </p>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <ul className="space-y-2">
            {navigation.map((item) => {
              const Icon = item.icon
              const isActive = currentPage === item.id
              return (
                <li key={item.id}>
                  <Button
                    variant={isActive ? "default" : "ghost"}
                    onClick={() => onPageChange(item.id)}
                    className={cn(
                      "w-full justify-start gap-3",
                      isActive && "bg-primary text-primary-foreground"
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </Button>
                </li>
              )
            })}
          </ul>
        </nav>

        <Separator />

        {/* User Profile */}
        <div className="p-4">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-2">
              <User className="w-4 h-4 text-foreground" />
              <span className="text-sm text-foreground">
                {user?.fullName || user?.firstName || 'User'}
              </span>
            </div>
            {userData?.role && (
              <span className="text-xs text-muted-foreground capitalize ml-6">
                {userData.role}
              </span>
            )}
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="h-16 border-b border-border flex items-center justify-between px-6 bg-card">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              <Menu className="w-5 h-5" />
            </Button>
            <h2 className="text-lg font-semibold text-foreground capitalize">
              {currentPage}
            </h2>
          </div>
          <UserButton />
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto bg-background">
          {children}
        </main>
      </div>
    </div>
  )
}

export default Layout

