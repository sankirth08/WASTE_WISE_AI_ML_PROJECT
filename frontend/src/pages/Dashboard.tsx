import { useEffect, useState } from 'react'
import { BarChart3, ChevronDown, CircleHelp, ClipboardList, Leaf, LogOut, Recycle, Settings, ShieldAlert, Sparkles } from 'lucide-react'
import { clearAuthSession, getAuthSession, logout, protectedRequest } from '../services/api'

type DashboardData = {
	as_of: string
	period_days: number
	products: number
	units_sold: number
	waste_units: number
	batches_at_risk: number
	metrics: {
		demand_forecast?: { mae: number; r2: number }
		expiry_risk?: { accuracy: number; roc_auc: number }
		food_waste?: { mae: number; r2: number }
		discount_recommendation_prototype?: { r2: number }
	}
}

type RiskItem = {
	batch_id: number
	product_id: string
	category: string
	days_to_expiry: number
	quantity_remaining: number
	risk_probability: number
}

function Dashboard() {
	const session = getAuthSession()
	const [data, setData] = useState<DashboardData | null>(null)
	const [riskItems, setRiskItems] = useState<RiskItem[]>([])
	const [error, setError] = useState('')
	const [periodDays, setPeriodDays] = useState<7 | 30>(7)

	useEffect(() => {
		if (!session) {
			window.location.assign('/login')
			return
		}
		Promise.all([
			protectedRequest<DashboardData>(`analytics/dashboard?days=${periodDays}`),
			protectedRequest<{ items: RiskItem[] }>('analytics/expiry-risk'),
		]).then(([dashboard, risk]) => {
			setData(dashboard)
			setRiskItems(risk.items.slice(0, 4))
		}).catch((reason: Error) => {
			setError(reason.message)
			if (reason.message.includes('session')) window.location.assign('/login')
		})
	}, [session?.access_token, periodDays])

	const signOut = async () => {
		await logout()
		clearAuthSession()
		window.location.assign('/login')
	}

	if (!session) return null

	return (
		<div className="workspace-shell">
			<aside className="workspace-sidebar">
				<a className="workspace-brand" href="/" aria-label="Back to WasteWise"><span><Recycle size={22} /></span><strong>WasteWise</strong><small>FOOD, THOUGHTFULLY</small></a>
				<p className="sidebar-label">Workspace</p>
				<nav className="workspace-nav" aria-label="Workspace navigation">
					<a className="is-current" href="#overview"><BarChart3 size={16} /> Overview</a>
					<a href="#forecast"><BarChart3 size={16} /> Demand forecast</a>
					<a href="#freshness"><ShieldAlert size={16} /> Expiry & freshness <b>{data?.batches_at_risk ?? '...'}</b></a>
					<a href="#waste"><ClipboardList size={16} /> Waste reports</a>
					<a href="#recommendations"><Sparkles size={16} /> Recommendations</a>
				</nav>
				<div className="sidebar-note"><span><Leaf size={17} /></span><strong>Little steps add up.</strong><p>Every good decision keeps food in the picture.</p><a href="#recommendations">See today’s ideas <span>→</span></a></div>
				<a className="sidebar-back" href="/">← Back to WasteWise</a>
			</aside>
			<main className="workspace-content" id="overview">
				<header className="workspace-topbar"><div className="mobile-workspace-brand"><Recycle size={20} /> WasteWise</div><div className="workspace-actions"><button type="button" aria-label="Help"><CircleHelp size={17} /></button><button type="button" aria-label="Settings"><Settings size={17} /></button><span className="user-avatar">{session.user.name.slice(0, 1).toUpperCase()}</span><button className="workspace-logout" type="button" onClick={signOut}><LogOut size={15} /> Log out</button></div></header>
				<section className="workspace-heading"><div><p className="workspace-eyebrow"><span /> Your food, in focus</p><h1>Good morning, {session.user.name.split(' ')[0]} <span>✳</span></h1><p>Here’s the good you’re doing, and where a little attention can go a long way.</p></div><label className="range-select"><span>Showing</span><select aria-label="Reporting period" value={periodDays} onChange={(event) => setPeriodDays(Number(event.target.value) as 7 | 30)}><option value={7}>7 days</option><option value={30}>30 days</option></select><ChevronDown size={15} /></label></section>
				<div className="preview-banner"><Sparkles size={15} /><strong>Preview workspace</strong><span>These illustrative numbers are sample data, not live business results.</span><a href="#models">About this preview</a></div>
				{error && <p className="dashboard-error" role="alert">{error}</p>}
				<section className="workspace-kpis" aria-label="Workspace overview">
					<div><span className="kpi-icon kpi-icon--mint"><Leaf size={16} /></span><small>Waste prevented</small><strong>{data ? `${Math.round(data.waste_units * 1.6)} kg` : '...'}</strong><em>↑ 12.8%</em><p>vs. previous {periodDays} days · illustrative</p></div>
					<div><span className="kpi-icon kpi-icon--blue"><BarChart3 size={16} /></span><small>Waste rate</small><strong>{data ? `${(data.waste_units / Math.max(data.units_sold, 1) * 100).toFixed(1)}%` : '...'} </strong><em className="status-text">on track</em><p>of tracked inventory · illustrative</p></div>
					<div><span className="kpi-icon kpi-icon--yellow"><ShieldAlert size={16} /></span><small>Items nearing expiry</small><strong>{data?.batches_at_risk ?? '...' } <i>items</i></strong><em className="status-text">needs a look</em><p>4 need attention today · illustrative</p></div>
					<div><span className="kpi-icon kpi-icon--green"><BarChart3 size={16} /></span><small>Demand forecast</small><strong>{data?.metrics.demand_forecast ? `${Math.max(0, Math.round(data.metrics.demand_forecast.r2 * 100))}.4%` : '...'} </strong><em className="status-text">steady</em><p>sample model estimate · illustrative</p></div>
				</section>
				<section className="workspace-grid">
					<article className="workspace-card chart-card" id="waste"><div className="card-kicker">A little progress, every day</div><div className="card-title-row"><div><h2>Food waste prevented</h2><strong>{data ? `${Math.round(data.waste_units * 1.6)} kg` : '...'} <small>↑ 12.8% &nbsp; saved from waste</small></strong></div><label className="chart-range"><select aria-label="Chart reporting period" value={periodDays} onChange={(event) => setPeriodDays(Number(event.target.value) as 7 | 30)}><option value={7}>7 days</option><option value={30}>30 days</option></select><ChevronDown size={13} /></label></div><div className="line-chart" aria-label="Illustrative food waste prevented chart"><div className="chart-grid-lines"><span>90 kg</span><span>67 kg</span><span>58 kg</span><span>29 kg</span><span>0 kg</span></div><svg viewBox="0 0 620 180" role="img" aria-label="Food waste prevented trend"><path d="M35 130 L130 93 L225 115 L320 70 L415 105 L510 48 L600 82" /><path className="chart-area" d="M35 130 L130 93 L225 115 L320 70 L415 105 L510 48 L600 82 L600 160 L35 160 Z" /></svg><div className="chart-days"><span>{periodDays === 7 ? 'Mon' : '1–7'}</span><span>{periodDays === 7 ? 'Tue' : '8–14'}</span><span>{periodDays === 7 ? 'Wed' : '15–21'}</span><span>{periodDays === 7 ? 'Thu' : '22–28'}</span><span>{periodDays === 7 ? 'Fri' : '29–30'}</span><span>{periodDays === 7 ? 'Sat' : ''}</span><span>{periodDays === 7 ? 'Sun' : ''}</span></div></div><p className="chart-note"><span /> Waste prevented <small>Illustrative sample · {periodDays} days</small></p></article>
					<article className="workspace-card category-card"><div className="card-kicker">What needs a hand?</div><div className="card-title-row"><h2>Waste by category</h2><button className="icon-menu" type="button" aria-label="Category options">•••</button></div><div className="donut-wrap"><div className="donut"><strong>4<small>categories</small></strong></div><ul><li><i className="dot dot--green" /> Fresh produce <b>42%</b></li><li><i className="dot dot--yellow" /> Bakery <b>26%</b></li><li><i className="dot dot--blue" /> Dairy <b>19%</b></li><li><i className="dot dot--grey" /> Other <b>13%</b></li></ul></div><p className="chart-note">Illustrative distribution of recorded food waste.</p></article>
					<article className="workspace-card freshness-card" id="freshness"><div className="card-kicker">Freshness check <span>{riskItems.length || 4}</span></div><div className="card-title-row"><h2>Needs a little attention</h2><a href="#freshness">View all <span>→</span></a></div><table><thead><tr><th>Item</th><th>Quantity</th><th>Best before</th><th>Risk</th><th /></tr></thead><tbody>{riskItems.length ? riskItems.map((item) => <tr key={item.batch_id}><td><strong>{item.category}</strong><small>Batch {item.batch_id}</small></td><td>{item.quantity_remaining} units</td><td>{item.days_to_expiry <= 1 ? 'Today' : `${item.days_to_expiry} days`}</td><td><span className="risk-high">● High</span></td><td><button type="button">Review</button></td></tr>) : <tr><td colSpan={5}>Loading freshness signals...</td></tr>}</tbody></table></article>
					<article className="workspace-card ideas-card" id="recommendations"><div className="card-kicker">Thoughtful next steps</div><div className="card-title-row"><h2>Today’s ideas</h2><Sparkles size={15} /></div><div className="idea"><small>01</small><div><strong>Give greens a second look</strong><p>Plan a feature for the freshest batch today.</p></div><span>↗</span></div><div className="idea"><small>02</small><div><strong>Review the closest expiry</strong><p>Make a timely move while there’s still time.</p></div><span>↗</span></div></article>
				</section>
				<section className="models-strip" id="models"><div><p className="card-kicker">Model signals</p><h2>Built to help you act earlier.</h2></div><span>Demand MAE {data?.metrics.demand_forecast?.mae.toFixed(2) ?? '...'} · Expiry ROC AUC {data?.metrics.expiry_risk?.roc_auc.toFixed(2) ?? '...'} · Discount recommendations use simulated scenarios.</span></section>
			</main>
		</div>
	)
}

export default Dashboard
