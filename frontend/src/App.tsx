import { useState } from 'react'
import {
	ArrowDown,
	ArrowDownRight,
	ArrowRight,
	Boxes,
	ChartNoAxesCombined,
	ChevronRight,
	CircleCheck,
	Leaf,
	Menu,
	Recycle,
	ShieldAlert,
	Sparkles,
	X,
} from 'lucide-react'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'

const navigation = [
	{ label: 'Platform', href: '#platform' },
	{ label: 'How it works', href: '#how-it-works' },
	{ label: 'Our impact', href: '#impact' },
]

const capabilities = [
	{
		number: '01',
		icon: ChartNoAxesCombined,
		title: 'See demand sooner',
		detail: 'Turn sales history and calendar patterns into clearer ordering decisions.',
		tone: 'mint',
	},
	{
		number: '02',
		icon: ShieldAlert,
		title: 'Act before expiry',
		detail: 'Bring at-risk batches forward while there is still time to make a difference.',
		tone: 'lime',
	},
	{
		number: '03',
		icon: Leaf,
		title: 'Learn from every day',
		detail: 'Track waste alongside the choices that help prevent it next time.',
		tone: 'soft',
	},
]

function App() {
	const [menuOpen, setMenuOpen] = useState(false)
	const authPath = window.location.pathname
	if (authPath === '/login' || authPath === '/register') {
		return <Login initialMode={authPath === '/register' ? 'register' : 'login'} />
	}
	if (authPath === '/dashboard') return <Dashboard />

	const closeMenu = () => setMenuOpen(false)

	return (
		<div className="outer-frame" id="top">
			<div className="ambient-mark ambient-mark--top" aria-hidden="true"><i /><i /><i /></div>
			<div className="ambient-diamonds ambient-diamonds--right" aria-hidden="true"><i /><i /><i /><i /></div>
			<div className="ambient-diamonds ambient-diamonds--left" aria-hidden="true"><i /><i /><i /><i /></div>
			<div className="ambient-mark ambient-mark--bottom" aria-hidden="true"><i /><i /><i /></div>

			<div className="site-frame">
				<div className="frame-rail frame-rail--top" />
				<header className="site-header">
					<a className="brand" href="#top" aria-label="WasteWise home" onClick={closeMenu}>
						<span className="brand-symbol"><Recycle size={25} strokeWidth={2.6} /></span>
						<span className="brand-name">WasteWise<span>AI</span></span>
					</a>

					<button
						className="menu-toggle"
						type="button"
						aria-label={menuOpen ? 'Close navigation' : 'Open navigation'}
						aria-expanded={menuOpen}
						onClick={() => setMenuOpen(!menuOpen)}
					>
						{menuOpen ? <X size={21} /> : <Menu size={21} />}
					</button>

					<nav className={`main-nav${menuOpen ? ' main-nav--open' : ''}`} aria-label="Main navigation">
						{navigation.map((item) => (
							<a href={item.href} key={item.label} onClick={closeMenu}>{item.label}</a>
						))}
						<a className="nav-contact" href="#contact" onClick={closeMenu}>Get in touch</a>
					</nav>

					  <a className="header-cta" href="/login" aria-label="Log in to WasteWise" title="Log in to WasteWise">
						Log in <ArrowRight size={15} strokeWidth={2.2} />
					</a>
				</header>

				<main>
					<section className="hero" aria-labelledby="hero-title">
						<div className="hero-copy">
							<p className="eyebrow"><span className="eyebrow-line" /> Smarter food, less waste</p>
							  <h1 id="hero-title">Make food<br />go <span>further.</span></h1>
							<div className="hero-ribbon">
								<Leaf size={20} strokeWidth={2.3} />
								<span>Better decisions. Brighter plates.</span>
								<span className="ribbon-spark" aria-hidden="true">✳</span>
							</div>
							<p className="hero-description">
								WasteWise helps food teams spot demand, protect fresh stock, and turn everyday data into less waste.
							</p>
							<div className="hero-actions">
								<a className="button button--green" href="#platform">Discover WasteWise <ArrowRight size={17} /></a>
								<a className="text-link" href="#how-it-works">See how it works <ArrowDownRight size={17} /></a>
							</div>
							<div className="hero-note"><span className="note-dot" /> Practical insight for a more resourceful food system</div>
						</div>

						<div className="hero-visual">
							<div className="photo-outline photo-outline--back" aria-hidden="true" />
							<div className="photo-outline photo-outline--front" aria-hidden="true" />
							<figure className="hero-photo">
								<img
									src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=1300&q=88"
									alt="Fresh produce arranged at a local market"
									fetchPriority="high"
								/>
								<figcaption className="photo-caption">
									<span className="caption-icon"><Leaf size={17} /></span>
									<span><strong>Freshness has a future.</strong><small>Start with a smarter picture of today.</small></span>
									<ArrowDownRight size={18} />
								</figcaption>
							</figure>
							<div className="floating-note floating-note--top"><span className="floating-icon"><Sparkles size={16} /></span><span>Forecast with context</span></div>
							<div className="floating-note floating-note--bottom"><span className="floating-check"><CircleCheck size={17} /></span><span>Catch risk earlier</span></div>
							<span className="hero-cross hero-cross--left" aria-hidden="true">×</span>
							<span className="hero-cross hero-cross--right" aria-hidden="true">×</span>
							<span className="hero-sprout" aria-hidden="true"><Leaf size={39} /></span>
						</div>
					</section>

					<div className="scroll-cue"><span>Scroll to explore</span><ArrowDown size={15} /></div>

					<section className="platform-section section-pad" id="platform" aria-labelledby="platform-title">
						<div className="section-heading">
							<p className="eyebrow"><span className="eyebrow-line" /> Thoughtful tools, everyday impact</p>
							<h2 id="platform-title">A clearer view of<br /><span>what comes next.</span></h2>
							<p className="section-intro">Bring forecasting, freshness, and waste reporting into one practical rhythm for your team.</p>
						</div>
						<div className="capability-grid">
							{capabilities.map(({ number, icon: Icon, title, detail, tone }) => (
								<article className={`capability capability--${tone}`} key={number}>
									<div className="capability-top"><span>{number}</span><Icon size={22} strokeWidth={1.8} /></div>
									<h3>{title}</h3>
									<p>{detail}</p>
									<a href="#workspace" aria-label={`Explore ${title}`}><ArrowRight size={17} /></a>
								</article>
							))}
						</div>
					</section>

					<section className="workspace-section" id="workspace" aria-labelledby="workspace-title">
						<div className="workspace-copy">
							<p className="eyebrow eyebrow--light"><span className="eyebrow-line" /> From insight to action</p>
							<h2 id="workspace-title">Your operation,<br />in a fresher light.</h2>
							<p>See the signals that matter across demand, inventory, expiry risk, and waste, all in one calm workspace.</p>
							<a className="button button--light" href="#contact">Explore the WasteWise approach <ArrowRight size={17} /></a>
						</div>
						<div className="workspace-preview" aria-label="WasteWise workspace preview">
							<div className="preview-topbar"><span className="preview-brand"><Recycle size={16} /> WasteWise</span><span className="preview-period">Today <ChevronRight size={13} /></span></div>
							<div className="preview-title-row"><div><small>OVERVIEW</small><h3>A little more in balance.</h3></div><span className="preview-status"><span /> Live view</span></div>
							<div className="preview-metrics">
								<div className="preview-metric"><span>Demand outlook</span><strong>Steady</strong><small><ChartNoAxesCombined size={13} /> Based on recent sales</small></div>
								<div className="preview-metric"><span>Expiry watch</span><strong>3 batches</strong><small><ShieldAlert size={13} /> Need a closer look</small></div>
								<div className="preview-metric"><span>Waste recorded</span><strong>12.4 <em>kg</em></strong><small><Leaf size={13} /> This week</small></div>
							</div>
							<div className="preview-chart-head"><span>Stock movement</span><span>Last 7 days</span></div>
							<div className="chart-bars" aria-label="Illustrative weekly stock movement chart">
								{[38, 54, 47, 71, 60, 82, 66, 91, 74, 84, 58, 72, 49, 64, 43, 59, 39, 51, 32, 45, 27, 38, 24, 34].map((height, index) => (
									<i className={index > 18 ? 'bar-muted' : ''} key={index} style={{ height: `${height}%` }} />
								))}
							</div>
							<div className="chart-axis"><span>Mon</span><span>Tue</span><span>Wed</span><span>Thu</span><span>Fri</span><span>Sat</span><span>Sun</span></div>
						</div>
						<div className="workspace-decoration" aria-hidden="true"><Boxes size={68} strokeWidth={0.8} /></div>
					</section>

					<section className="impact-section section-pad" id="impact" aria-labelledby="impact-title">
						<div className="impact-icon"><Leaf size={24} /></div>
						<div className="impact-copy"><p className="eyebrow"><span className="eyebrow-line" /> Good food deserves a good plan</p><h2 id="impact-title">Less guesswork.<br /><span>More good going around.</span></h2></div>
						<p className="impact-description">Small, timely choices can help food stay where it belongs: on shelves, on menus, and on plates. WasteWise makes those choices easier to see.</p>
						<a className="impact-link" href="#how-it-works">Our approach <ArrowRight size={17} /></a>
					</section>

					<section className="how-section section-pad" id="how-it-works" aria-labelledby="how-title">
						<div className="how-heading"><div><p className="eyebrow"><span className="eyebrow-line" /> A simple cycle</p><h2 id="how-title">Notice. Act. <span>Improve.</span></h2></div><p>Useful signals are only useful when they lead somewhere. WasteWise connects the view of today to the choices of tomorrow.</p></div>
						<div className="cycle-steps">
							<div><span className="step-icon"><ChartNoAxesCombined size={20} /></span><strong>Notice patterns</strong><small>Read demand and stock signals.</small></div>
							<ArrowRight className="step-arrow" size={20} />
							<div><span className="step-icon"><ShieldAlert size={20} /></span><strong>Make a timely move</strong><small>Prioritize stock that needs attention.</small></div>
							<ArrowRight className="step-arrow" size={20} />
							<div><span className="step-icon"><Leaf size={20} /></span><strong>Keep learning</strong><small>Use outcomes to plan more clearly.</small></div>
						</div>
					</section>

					<section className="contact-section" id="contact">
						<div className="contact-mark"><Recycle size={24} /></div>
						<div><p className="eyebrow eyebrow--light">A more thoughtful food future</p><h2>Let’s make less go to waste.</h2></div>
						<a className="button button--light" href="#top">Back to the beginning <ArrowRight size={17} /></a>
					</section>
				</main>

				<footer className="site-footer">
					<a className="brand brand--footer" href="#top"><span className="brand-symbol"><Recycle size={21} strokeWidth={2.6} /></span><span className="brand-name">WasteWise<span>AI</span></span></a>
					<span>Smarter choices for a less wasteful food system.</span>
					<a href="#top">Back to top <ArrowDown size={14} /></a>
				</footer>
				<div className="frame-rail frame-rail--bottom" />
			</div>
		</div>
	)
}

export default App
