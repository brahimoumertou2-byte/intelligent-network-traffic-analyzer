const API = window.API_BASE || "http://127.0.0.1:8000/api";
const COLORS = ["#45d6a5", "#68a8ff", "#f5ba63", "#bba0ff", "#ff7185", "#68d8e9"];
const state = { traffic: [], alerts: [], devices: [], timelineChart: null, protocolChart: null };
const el = id => document.getElementById(id);
const escapeHtml = value => String(value ?? "—").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
const formatNumber = value => Number(value || 0).toLocaleString();
const formatBytes = value => {
  const bytes = Number(value || 0);
  if (!bytes) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toLocaleString(undefined, { maximumFractionDigits: index ? 1 : 0 })} ${units[index]}`;
};
const formatTime = value => value ? new Date(value).toLocaleString() : "—";
async function get(path) { const response = await fetch(`${API}${path}`); if (!response.ok) throw new Error(`API returned ${response.status}`); return response.json(); }
function setConnection(connected, message) { el("api-status").textContent = connected ? "API Connected" : "API Disconnected"; el("api-dot").classList.toggle("online", connected); el("last-update").textContent = message; }
function setChart(current, id, config) { if (current) current.destroy(); return new Chart(el(id), config); }
function listItems(items, formatter, empty) { return items.length ? items.map(formatter).join("") : `<li class="empty-list">${empty}</li>`; }
function renderCharts(timeline, protocols) {
  el("timeline-empty").hidden = timeline.length > 0;
  el("protocols-empty").hidden = protocols.length > 0;
  state.timelineChart = setChart(state.timelineChart, "timeline", { type: "line", data: { labels: timeline.map(item => new Date(item.timestamp).toLocaleString()), datasets: [{ label: "Packets", data: timeline.map(item => item.packets), borderColor: COLORS[0], backgroundColor: "#45d6a51a", borderWidth: 2, pointRadius: 2, fill: true, tension: .3 }] }, options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { ticks: { color: "#91a4b9", maxRotation: 0 }, grid: { color: "#1d3044" } }, y: { beginAtZero: true, ticks: { color: "#91a4b9" }, grid: { color: "#1d3044" } } } } });
  state.protocolChart = setChart(state.protocolChart, "protocols", { type: "doughnut", data: { labels: protocols.map(item => item.protocol), datasets: [{ data: protocols.map(item => item.count), backgroundColor: protocols.map((_, index) => COLORS[index % COLORS.length]), borderWidth: 0 }] }, options: { responsive: true, maintainAspectRatio: false, cutout: "68%", plugins: { legend: { display: false } } } });
  const total = protocols.reduce((sum, item) => sum + item.count, 0);
  el("protocol-legend").innerHTML = protocols.map((item, index) => `<span class="legend-item"><i class="legend-dot" style="background:${COLORS[index % COLORS.length]}"></i>${escapeHtml(item.protocol)} ${total ? Math.round(item.count / total * 100) : 0}%</span>`).join("") || "No protocol data available";
}
function renderTopLists(ips, ports) {
  el("source-ips").innerHTML = listItems(ips.sources, item => `<li><span>${escapeHtml(item.ip)}</span><b>${formatNumber(item.count)}</b></li>`, "No source IP data available");
  el("destination-ips").innerHTML = listItems(ips.destinations, item => `<li><span>${escapeHtml(item.ip)}</span><b>${formatNumber(item.count)}</b></li>`, "No destination IP data available");
  el("top-ports").innerHTML = listItems(ports, item => `<li><span>Port ${escapeHtml(item.port)}</span><b>${formatNumber(item.count)}</b></li>`, "No destination port data available");
}
function renderTraffic() {
  const search = el("traffic-search").value.trim().toLowerCase();
  const protocol = el("protocol-filter").value;
  const rows = state.traffic.filter(item => (!search || item.source_ip.includes(search) || item.destination_ip.includes(search)) && (!protocol || item.protocol === protocol));
  el("traffic-rows").innerHTML = rows.length ? rows.map(item => `<tr><td>${escapeHtml(item.source_ip)}</td><td>${escapeHtml(item.destination_ip)}</td><td><span class="protocol-badge">${escapeHtml(item.protocol)}</span></td><td>${escapeHtml(item.source_port)}</td><td>${escapeHtml(item.destination_port)}</td><td>${formatBytes(item.packet_size)}</td><td>${formatTime(item.timestamp)}</td></tr>`).join("") : `<tr><td class="empty-row" colspan="7">No traffic records available</td></tr>`;
}
function renderAlerts() {
  const severity = el("severity-filter").value;
  const status = el("alert-status-filter").value;
  const rows = state.alerts.filter(item => (!severity || item.severity === severity) && (!status || item.status === status));
  el("alerts-list").innerHTML = rows.length ? rows.map(item => `<article class="alert-row ${escapeHtml(item.severity)}"><strong>${escapeHtml(item.type)}</strong><span class="severity-badge ${escapeHtml(item.severity)}">${escapeHtml(item.severity)}</span><span>${escapeHtml(item.source_ip)}</span><p>${escapeHtml(item.description)}</p><span class="status-badge ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span><span class="alert-meta">${formatTime(item.timestamp)}</span></article>`).join("") : `<p class="empty-list">No alerts match the selected filters</p>`;
}
function renderDevices() { el("device-rows").innerHTML = state.devices.length ? state.devices.map(item => `<tr><td>${escapeHtml(item.ip_address)}</td><td>${escapeHtml(item.hostname)}</td><td><span class="status-badge ${escapeHtml(item.status)}">${item.status === "active" ? "online" : escapeHtml(item.status)}</span></td><td>${formatTime(item.last_seen)}</td></tr>`).join("") : `<tr><td class="empty-row" colspan="4">No devices detected</td></tr>`; }
function setProtocolOptions() { const select = el("protocol-filter"); const current = select.value; const protocols = [...new Set(state.traffic.map(item => item.protocol))].sort(); select.innerHTML = `<option value="">All protocols</option>${protocols.map(protocol => `<option value="${escapeHtml(protocol)}">${escapeHtml(protocol)}</option>`).join("")}`; select.value = protocols.includes(current) ? current : ""; }
async function refresh() { try {
  const [overview, protocols, ips, ports, timeline, traffic, alerts, devices] = await Promise.all([get("/statistics/overview"), get("/statistics/protocols"), get("/statistics/top-ips"), get("/statistics/top-ports"), get("/statistics/timeline"), get("/traffic?limit=50"), get("/alerts?limit=50"), get("/devices?limit=50")]);
  el("packets").textContent = formatNumber(overview.total_packets); el("volume").textContent = formatBytes(overview.traffic_volume); el("devices-count").textContent = formatNumber(overview.active_devices); el("alerts-count").textContent = formatNumber(overview.total_alerts);
  state.traffic = traffic; state.alerts = alerts; state.devices = devices; setProtocolOptions(); renderCharts(timeline, protocols); renderTopLists(ips, ports); renderTraffic(); renderAlerts(); renderDevices(); setConnection(true, `Last updated: ${new Date().toLocaleTimeString()}`);
 } catch (error) { console.error("Dashboard API refresh failed:", error); setConnection(false, error.message); } }
el("traffic-search").addEventListener("input", renderTraffic); el("protocol-filter").addEventListener("change", renderTraffic); el("severity-filter").addEventListener("change", renderAlerts); el("alert-status-filter").addEventListener("change", renderAlerts); el("refresh-button").addEventListener("click", refresh);
refresh(); setInterval(refresh, 15000);
