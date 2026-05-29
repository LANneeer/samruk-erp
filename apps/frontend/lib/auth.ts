// Demo authentication utilities
// In production, replace with proper authentication system

export interface User {
  id: string
  email: string
  name: string
}

const STORAGE_KEY = 'samruk_auth_user'
const USERS_KEY = 'samruk_users'

// Demo credentials
const DEMO_USERS: User[] = [
  {
    id: 'a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d',
    email: 'admin@samruk.kz',
    name: 'Admin User',
  },
]

function getStoredUsers(): Array<User & { password: string }> {
  if (typeof window === 'undefined') return []
  const stored = localStorage.getItem(USERS_KEY)
  if (stored) {
    return JSON.parse(stored)
  }
  // Initialize with demo users
  const initial = DEMO_USERS.map(u => ({ ...u, password: 'password123' }))
  localStorage.setItem(USERS_KEY, JSON.stringify(initial))
  return initial
}

function saveUsers(users: Array<User & { password: string }>) {
  if (typeof window === 'undefined') return
  localStorage.setItem(USERS_KEY, JSON.stringify(users))
}

export function login(email: string, password: string): User | null {
  const users = getStoredUsers()
  const user = users.find(u => u.email === email && u.password === password)
  if (user) {
    const { password: _, ...userData } = user
    localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
    return userData
  }
  return null
}

export function signup(email: string, password: string, name: string): User | null {
  const users = getStoredUsers()
  if (users.find(u => u.email === email)) {
    return null // User already exists
  }
  
  const newUser = {
    id: crypto.randomUUID(),
    email,
    name,
    password,
  }
  
  users.push(newUser)
  saveUsers(users)
  
  const { password: _, ...userData } = newUser
  localStorage.setItem(STORAGE_KEY, JSON.stringify(userData))
  return userData
}

export function logout() {
  if (typeof window === 'undefined') return
  localStorage.removeItem(STORAGE_KEY)
}

export function getCurrentUser(): User | null {
  if (typeof window === 'undefined') return null
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    return JSON.parse(stored)
  }
  return null
}
