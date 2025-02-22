import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { motion } from 'framer-motion'
import { Home, MessageSquare, BarChart, FileText, Settings, Menu, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

const menuItems = [
  { icon: Home, label: 'Dashboard', href: '/' },
  { icon: MessageSquare, label: 'Conversations', href: '/conversations' },
  { icon: BarChart, label: 'Analytics', href: '/analytics' },
  { icon: FileText, label: 'Reports', href: '/reports' },
  { icon: Settings, label: 'Settings', href: '/settings' },
]

export function Sidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const pathname = usePathname()

  return (
    <motion.aside
      initial={{ width: 240 }}
      animate={{ width: isCollapsed ? 80 : 240 }}
      className="bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 h-screen flex flex-col"
    >
      <div className="h-16 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between px-4">
        {!isCollapsed && (
          <span className="text-xl font-bold text-gray-900 dark:text-gray-100">Menu</span>
        )}
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsCollapsed(!isCollapsed)}
        >
          {isCollapsed ? <Menu className="h-5 w-5" /> : <X className="h-5 w-5" />}
        </Button>
      </div>

      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href

            return (
              <li key={item.href}>
                <Link href={item.href}>
                  <span
                    className={`flex items-center gap-4 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-gray-100 dark:bg-gray-800 text-primary'
                        : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    {!isCollapsed && <span>{item.label}</span>}
                  </span>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>
    </motion.aside>
  )
}
