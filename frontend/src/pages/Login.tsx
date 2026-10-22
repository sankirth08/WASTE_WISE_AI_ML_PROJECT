import { useState, type FormEvent } from 'react'
import {
	ArrowLeft,
	ArrowRight,
	Check,
	Eye,
	EyeOff,
	Leaf,
	LockKeyhole,
	Mail,
	Recycle,
	ShieldCheck,
} from 'lucide-react'
import { registerAccount, saveAuthSession, signIn } from '../services/api'

type AuthMode = 'login' | 'register'

type LoginProps = {
	initialMode?: AuthMode
}

function Login({ initialMode = 'login' }: LoginProps) {
	const [mode, setMode] = useState<AuthMode>(initialMode)
	const [showPassword, setShowPassword] = useState(false)
	const [message, setMessage] = useState('')
	const [messageType, setMessageType] = useState<'error' | 'success'>('error')
	const [isSubmitting, setIsSubmitting] = useState(false)

	const isRegister = mode === 'register'

	const changeMode = (nextMode: AuthMode) => {
		setMode(nextMode)
		setMessage('')
		setMessageType('error')
		setShowPassword(false)
	}

	const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
		event.preventDefault()
		const values = new FormData(event.currentTarget)
		const email = String(values.get('email') ?? '')
		const password = String(values.get('password') ?? '')
		setIsSubmitting(true)
		setMessage('')
		try {
			const session = isRegister
				? await registerAccount({ name: String(values.get('name') ?? ''), email, password })
				: await signIn({ email, password })
			saveAuthSession(session)
			setMessageType('success')
			setMessage(isRegister ? `Account created. You’re signed in as ${session.user.email}.` : `Welcome back, ${session.user.name}.`)
			window.setTimeout(() => window.location.assign('/dashboard'), 400)
		} catch (error) {
			setMessageType('error')
			setMessage(error instanceof Error ? error.message : 'Unable to connect to WasteWise. Please try again.')
		} finally {
			setIsSubmitting(false)
		}
	}

	return (
		<div className="outer-frame auth-outer-frame">
			<div className="ambient-mark ambient-mark--top" aria-hidden="true"><i /><i /><i /></div>
			<div className="ambient-diamonds ambient-diamonds--right" aria-hidden="true"><i /><i /><i /><i /></div>
			<div className="site-frame auth-frame">
				<div className="frame-rail frame-rail--top" />
				<header className="auth-header">
					<a className="brand" href="/" aria-label="WasteWise home">
						<span className="brand-symbol"><Recycle size={25} strokeWidth={2.6} /></span>
						<span className="brand-name">WasteWise<span>AI</span></span>
					</a>
					<a className="auth-back-link" href="/">
						<ArrowLeft size={15} /> <span>Back to home</span>
					</a>
				</header>

				<main className="auth-main">
					<section className="auth-story" aria-labelledby="auth-story-title">
						<div className="auth-story-content">
							<p className="eyebrow"><span className="eyebrow-line" /> A fresher way forward</p>
							<h1 id="auth-story-title">Make every<br />good thing <span>count.</span></h1>
							<p className="auth-story-copy">Bring a little more clarity to the choices that keep fresh food moving.</p>
							<div className="auth-story-points">
								<div><span><Leaf size={16} /></span><p><strong>See what’s next</strong><small>Understand demand before you order.</small></p></div>
								<div><span><ShieldCheck size={16} /></span><p><strong>Protect what’s fresh</strong><small>Spot expiry risk while there’s time.</small></p></div>
							</div>
						</div>
						<div className="auth-photo-wrap">
							<img
								src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1000&q=85"
								alt="Fresh produce arranged at a market"
							/>
							<div className="auth-photo-label"><span><Check size={15} /></span> Better choices start here</div>
							<div className="auth-photo-outline" aria-hidden="true" />
						</div>
						<div className="auth-story-mark" aria-hidden="true"><Recycle size={88} strokeWidth={0.8} /></div>
					</section>

					<section className="auth-panel" aria-labelledby="auth-title">
						<div className="auth-panel-topline"><span /><span>WASTEWISE WORKSPACE</span><span /></div>
						<div className="auth-form-wrap" key={mode}>
							<div className="auth-heading">
								<div className="auth-icon"><LockKeyhole size={20} /></div>
								<p className="eyebrow"><span className="eyebrow-line" /> Welcome to WasteWise</p>
								<h2 id="auth-title">{isRegister ? 'Create your account.' : 'Good to see you.'}</h2>
								<p>{isRegister ? 'Start making more thoughtful food decisions.' : 'Sign in to continue to your workspace.'}</p>
							</div>

							<div className="auth-mode-switch" role="tablist" aria-label="Choose sign-in or registration">
								<button type="button" role="tab" aria-selected={!isRegister} className={!isRegister ? 'is-active' : ''} onClick={() => changeMode('login')}>Log in</button>
								<button type="button" role="tab" aria-selected={isRegister} className={isRegister ? 'is-active' : ''} onClick={() => changeMode('register')}>Create account</button>
							</div>

							<form className="auth-form" onSubmit={handleSubmit} aria-busy={isSubmitting}>
								{isRegister && (
									<label className="auth-field">
										<span>Your name</span>
										<div className="auth-input-wrap"><input autoComplete="name" name="name" placeholder="Alex Morgan" required /><span className="auth-field-icon"><Leaf size={17} /></span></div>
									</label>
								)}
								<label className="auth-field">
									<span>Work email</span>
									<div className="auth-input-wrap"><input autoComplete="email" name="email" type="email" placeholder="you@yourteam.com" required /><span className="auth-field-icon"><Mail size={17} /></span></div>
								</label>
								<div className="auth-field">
									<label htmlFor="auth-password">Password</label>
									<div className="auth-input-wrap">
										<input id="auth-password" autoComplete={isRegister ? 'new-password' : 'current-password'} minLength={8} name="password" placeholder="At least 8 characters" required type={showPassword ? 'text' : 'password'} />
										<button className="password-toggle" type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}</button>
									</div>
								</div>
								{!isRegister && <div className="auth-form-options"><label><input type="checkbox" name="remember" /> <span>Remember me</span></label><button type="button" onClick={() => setMessage('Password recovery is not connected to the service yet.')}>Forgot password?</button></div>}
								<button className="auth-submit" disabled={isSubmitting} type="submit">{isSubmitting ? 'Please wait…' : isRegister ? 'Create account' : 'Log in'} <ArrowRight size={17} /></button>
								{message && <p className={`auth-message auth-message--${messageType}`} role={messageType === 'error' ? 'alert' : 'status'}>{message}</p>}
							</form>

							<p className="auth-switch-copy">{isRegister ? 'Already have an account?' : 'New to WasteWise?'} <a href={isRegister ? '/login' : '/register'}>{isRegister ? 'Log in' : 'Create an account'}</a></p>
						</div>
						<div className="auth-panel-footer"><ShieldCheck size={15} /><span>Your team’s data stays yours.</span><span className="auth-footer-dots"><i /><i /><i /></span></div>
					</section>
				</main>
				<footer className="auth-footer"><span>© 2026 WasteWise AI</span><span>Smarter choices for a less wasteful food system.</span><a href="/">Explore WasteWise <ArrowRight size={13} /></a></footer>
				<div className="frame-rail frame-rail--bottom" />
			</div>
		</div>
	)
}

export default Login
