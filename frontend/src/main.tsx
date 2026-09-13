import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { useState } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import "./styles.css";

type Metric = { label: string; value: string; unit: string; tone: string };

const metrics: Metric[] = [
  { label: "Site output", value: "482.6", unit: "kW", tone: "lime" },
  { label: "Battery charge", value: "68", unit: "%", tone: "cyan" },
  { label: "Wind speed", value: "8.4", unit: "m/s", tone: "amber" },
  { label: "Active alarms", value: "02", unit: "open", tone: "coral" },
];

function App() {
  const [activeSection, setActiveSection] = useState("overview");
  const [dialog, setDialog] = useState<string | null>(null);

  const navigateTo = (section: string) => {
    setActiveSection(section);
    document.getElementById(section)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <main className="studio-shell min-vh-100">
      <aside className="sidebar">
        <div className="brand"><span className="brand-mark">DT</span><span>twinfield</span></div>
        <p className="eyebrow">Workspace</p>
        <nav className="nav nav-pills flex-column gap-1"><a className={`nav-link ${activeSection === "overview" ? "active" : ""}`} href="#overview" onClick={(event) => { event.preventDefault(); navigateTo("overview"); }}>Overview</a><a className={`nav-link ${activeSection === "topology" ? "active" : ""}`} href="#topology" onClick={(event) => { event.preventDefault(); navigateTo("topology"); }}>Topology</a><a className={`nav-link ${activeSection === "entities" ? "active" : ""}`} href="#entities" onClick={(event) => { event.preventDefault(); navigateTo("entities"); }}>Entities</a><a className={`nav-link ${activeSection === "telemetry" ? "active" : ""}`} href="#telemetry" onClick={(event) => { event.preventDefault(); navigateTo("telemetry"); }}>Telemetry</a><a className={`nav-link d-flex justify-content-between ${activeSection === "alarms" ? "active" : ""}`} href="#alarms" onClick={(event) => { event.preventDefault(); navigateTo("alarms"); }}><span>Alarms</span><b className="badge rounded-pill">2</b></a></nav>
        <div className="site-selector"><span>Active site</span><strong>North Ridge Energy</strong><small>Online · 24 entities</small></div>
        <div className="sidebar-footer"><span className="status-dot" />All systems operational</div>
      </aside>
      <section className="workspace">
        <header className="topbar"><div><span className="breadcrumb">Sites / North Ridge Energy</span><h1>Control room</h1></div><div className="topbar-actions"><span className="live-pill"><i />Live stream</span><button className="btn btn-link" aria-label="Open settings" onClick={() => setDialog("Settings")}>⚙</button><div className="avatar">MI</div></div></header>
        <div className="content container-fluid" id="overview">
          <section className="intro"><div><p className="eyebrow">Sunday, September 13, 2026</p><h2>Good morning, Mosudi.</h2><p className="muted">A clear view of your digital site twin, right now.</p></div><button className="btn btn-primary primary" onClick={() => setDialog("Add entity")}>＋ Add entity</button></section>
          <section className="row g-3 metric-grid" id="telemetry">{metrics.map((metric) => <article className={`col-12 col-sm-6 col-xl-3`} key={metric.label}><div className={`metric-card ${metric.tone} h-100`}><span>{metric.label}</span><strong>{metric.value}<small>{metric.unit}</small></strong><em>↗ 4.8% <span>vs yesterday</span></em></div></article>)}</section>
          <section className="row g-3 lower-grid"><article className="col-12 col-xl-7" id="topology"><div className="panel topology-panel h-100"><div className="panel-heading"><div><p className="eyebrow">Live topology</p><h3>North Ridge Energy</h3></div><button className="btn btn-sm btn-outline-secondary quiet" onClick={() => setDialog("Topology map")}>Open map ↗</button></div><div className="topology"><div className="node node-site"><span>NR</span><strong>North Ridge</strong><small>Site · healthy</small></div><div className="connector c-one" /><div className="node node-pv"><span>PV</span><strong>Solar array</strong><small>312.4 kW · generating</small></div><div className="connector c-two" /><div className="node node-battery"><span>BT</span><strong>Battery bank</strong><small>68% · charging</small></div><div className="node node-wind"><span>WT</span><strong>Wind turbine</strong><small>170.2 kW · generating</small></div></div></div></article><article className="col-12 col-xl-5" id="alarms"><div className="panel alarm-panel h-100"><div className="panel-heading"><div><p className="eyebrow">Needs attention</p><h3>Open alarms <mark>2</mark></h3></div><button className="btn btn-sm btn-outline-secondary quiet" onClick={() => setDialog("Open alarms")}>View all ↗</button></div><div className="alarm"><span className="alarm-icon">!</span><div><strong>Inverter temperature high</strong><small>Inverter 01 · 82.4 °C</small></div><time>4m ago</time></div><div className="alarm"><span className="alarm-icon amber-icon">!</span><div><strong>Battery communication slow</strong><small>Battery bank · 1.8 s latency</small></div><time>18m ago</time></div></div></article></section>
          <section id="entities" className="visually-hidden" aria-label="Entities" />
          <footer className="footer-note"><span>Data refreshed just now</span><span>API status <b className="status-dot" /> healthy</span></footer>
        </div>
      </section>
      {dialog && <div className="action-dialog-backdrop" role="presentation" onClick={() => setDialog(null)}><div className="action-dialog" role="dialog" aria-modal="true" aria-labelledby="action-dialog-title" onClick={(event) => event.stopPropagation()}><div className="d-flex justify-content-between align-items-center mb-3"><h2 id="action-dialog-title" className="h5 mb-0">{dialog}</h2><button className="btn-close" aria-label="Close" onClick={() => setDialog(null)} /></div><p className="mb-0 text-secondary">This workspace action is connected and ready for the next platform workflow.</p><button className="btn btn-primary mt-4" onClick={() => setDialog(null)}>Done</button></div></div>}
    </main>
  );
}

createRoot(document.getElementById("root")!).render(<StrictMode><App /></StrictMode>);