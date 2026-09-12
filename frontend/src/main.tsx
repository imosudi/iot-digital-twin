import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Metric = { label: string; value: string; unit: string; tone: string };

const metrics: Metric[] = [
  { label: "Site output", value: "482.6", unit: "kW", tone: "lime" },
  { label: "Battery charge", value: "68", unit: "%", tone: "cyan" },
  { label: "Wind speed", value: "8.4", unit: "m/s", tone: "amber" },
  { label: "Active alarms", value: "02", unit: "open", tone: "coral" },
];

function App() {
  return (
    <main className="studio-shell">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">DT</span><span>twinfield</span></div>
        <p className="eyebrow">Workspace</p>
        <nav><a className="active" href="#overview">Overview</a><a href="#topology">Topology</a><a href="#entities">Entities</a><a href="#telemetry">Telemetry</a><a href="#alarms">Alarms <b>2</b></a></nav>
        <div className="site-selector"><span>Active site</span><strong>North Ridge Energy</strong><small>Online · 24 entities</small></div>
        <div className="sidebar-footer"><span className="status-dot" />All systems operational</div>
      </aside>
      <section className="workspace">
        <header className="topbar"><div><span className="breadcrumb">Sites / North Ridge Energy</span><h1>Control room</h1></div><div className="topbar-actions"><span className="live-pill"><i />Live stream</span><button aria-label="Open settings">⚙</button><div className="avatar">MI</div></div></header>
        <div className="content">
          <section className="intro"><div><p className="eyebrow">Sunday, September 13, 2026</p><h2>Good morning, Mosudi.</h2><p className="muted">A clear view of your digital site twin, right now.</p></div><button className="primary">＋ Add entity</button></section>
          <section className="metric-grid">{metrics.map((metric) => <article className={`metric-card ${metric.tone}`} key={metric.label}><span>{metric.label}</span><strong>{metric.value}<small>{metric.unit}</small></strong><em>↗ 4.8% <span>vs yesterday</span></em></article>)}</section>
          <section className="lower-grid"><article className="panel topology-panel"><div className="panel-heading"><div><p className="eyebrow">Live topology</p><h3>North Ridge Energy</h3></div><button className="quiet">Open map ↗</button></div><div className="topology"><div className="node node-site"><span>NR</span><strong>North Ridge</strong><small>Site · healthy</small></div><div className="connector c-one" /><div className="node node-pv"><span>PV</span><strong>Solar array</strong><small>312.4 kW · generating</small></div><div className="connector c-two" /><div className="node node-battery"><span>BT</span><strong>Battery bank</strong><small>68% · charging</small></div><div className="node node-wind"><span>WT</span><strong>Wind turbine</strong><small>170.2 kW · generating</small></div></div></article><article className="panel alarm-panel"><div className="panel-heading"><div><p className="eyebrow">Needs attention</p><h3>Open alarms <mark>2</mark></h3></div><button className="quiet">View all ↗</button></div><div className="alarm"><span className="alarm-icon">!</span><div><strong>Inverter temperature high</strong><small>Inverter 01 · 82.4 °C</small></div><time>4m ago</time></div><div className="alarm"><span className="alarm-icon amber-icon">!</span><div><strong>Battery communication slow</strong><small>Battery bank · 1.8 s latency</small></div><time>18m ago</time></div></article></section>
          <footer className="footer-note"><span>Data refreshed just now</span><span>API status <b className="status-dot" /> healthy</span></footer>
        </div>
      </section>
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);