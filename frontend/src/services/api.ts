export type AuthUser = {
	id: number
	name: string
	email: string
}

export type AuthSession = {
	access_token: string
	token_type: 'bearer'
	user: AuthUser
}

type AuthCredentials = {
	email: string
	password: string
}

type RegistrationDetails = AuthCredentials & {
	name: string
}

const AUTH_STORAGE_KEY = 'wastewise.auth'

export function getAuthSession(): AuthSession | null {
	try {
		const stored = localStorage.getItem(AUTH_STORAGE_KEY)
		return stored ? JSON.parse(stored) as AuthSession : null
	} catch {
		return null
	}
}

export function clearAuthSession(): void {
	localStorage.removeItem(AUTH_STORAGE_KEY)
}

export async function protectedRequest<T>(path: string): Promise<T> {
	const session = getAuthSession()
	if (!session) {
		throw new Error('Please sign in to continue.')
	}
	const response = await fetch(`/api/v1/${path}`, {
		headers: { Authorization: `Bearer ${session.access_token}` },
	})
	const result = await response.json().catch(() => null) as T | { detail?: string } | null
	if (response.status === 401) {
		clearAuthSession()
		throw new Error('Your session expired. Please sign in again.')
	}
	if (!response.ok) {
		throw new Error(result && typeof result === 'object' && 'detail' in result ? result.detail || 'Request failed.' : 'Request failed.')
	}
	return result as T
}

async function authRequest(path: string, body: AuthCredentials | RegistrationDetails): Promise<AuthSession> {
	const response = await fetch(`/api/v1/auth/${path}`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body),
	})
	const result = await response.json().catch(() => null) as AuthSession | { detail?: string | { msg?: string }[] } | null
	if (!response.ok) {
		const detail = result && 'detail' in result ? result.detail : null
		const message = Array.isArray(detail) ? detail.map((item) => item.msg).filter(Boolean).join('. ') : detail
		throw new Error(message || 'Unable to connect to WasteWise. Please try again.')
	}
	return result as AuthSession
}

export function registerAccount(details: RegistrationDetails): Promise<AuthSession> {
	return authRequest('register', details)
}

export function signIn(credentials: AuthCredentials): Promise<AuthSession> {
	return authRequest('login', credentials)
}

export function saveAuthSession(session: AuthSession): void {
	localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(session))
}

export async function logout(): Promise<void> {
	const session = getAuthSession()
	if (session) {
		await fetch('/api/v1/auth/logout', {
			method: 'POST',
			headers: { Authorization: `Bearer ${session.access_token}` },
		}).catch(() => undefined)
	}
	clearAuthSession()
}
