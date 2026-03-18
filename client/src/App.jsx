import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useState, useMemo, useRef, Component } from 'react';
import Map, { Marker as MapMarker, Source, Layer, Popup as MapPopup } from 'react-map-gl/maplibre';
import 'maplibre-gl/dist/maplibre-gl.css';
import {
  Truck,
  AlertTriangle,
  Cloud,
  ArrowRight,
  Route,
  Shield,
  Zap,
  MapPin,
  Sun,
  CloudRain,
  CloudSnow,
  Package,
  Activity,
  Trash2,
  Navigation,
  ChevronLeft,
  ChevronRight,
  Square,
  CheckCircle2,
} from 'lucide-react';
import axios from 'axios';
import './App.css';

// ─── Helpers ──────────────────────────────────────────
const weatherLabel = (w) => {
  if (w === 0) return 'Clear';
  if (w === 1) return 'Rainy';
  return 'Stormy';
};

const getRiskColor = (level) => {
  if (level === 'High') return 'bg-rose-500';
  if (level === 'Medium') return 'bg-amber-500';
  return 'bg-emerald-500';
};

const getRiskBorderColor = (level) => {
  if (level === 'High') return 'border-rose-400';
  if (level === 'Medium') return 'border-amber-400';
  return 'border-emerald-400';
};

// ─── Weather icon map ──────────────────────────────────
const WeatherIcon = ({ condition, size = 14 }) => {
  if (condition === 0) return <Sun size={size} className="text-amber-400" />;
  if (condition === 1) return <CloudRain size={size} className="text-blue-400" />;
  return <CloudSnow size={size} className="text-slate-700" />;
};

// ─── Error Boundary ────────────────────────────────────
class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { hasError: false, error: null }; }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  render() {
    if (this.state.hasError) {
      return (
        <div className="flex h-screen items-center justify-center bg-slate-50 text-slate-900 flex-col gap-4">
          <AlertTriangle size={48} className="text-rose-400" />
          <h2 className="text-xl font-bold">Something went wrong</h2>
          <p className="text-slate-600 text-sm max-w-md text-center">{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()} className="px-4 py-2 bg-slate-600 rounded-lg text-sm hover:bg-slate-500 transition-colors">
            Reload page
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

// ─── Animated counter ──────────────────────────────────
const AnimatedNumber = ({ value, suffix = '' }) => (
  <motion.span
    key={value}
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    transition={{ type: 'spring', stiffness: 200, damping: 20 }}
    className="tabular-nums"
  >
    {value}{suffix}
  </motion.span>
);

// ─── Navigation HUD (floating overlay panel) ───────────
const NavigationHUD = ({ features, currentIdx, onPrev, onNext, onStop, visitedSet }) => {
  if (!features || features.length === 0) return null;
  const stop = features[currentIdx]?.properties;
  const total = features.length;
  const isLast = currentIdx === total - 1;
  const nextStop = !isLast ? features[currentIdx + 1]?.properties : null;
  const riskLower = (stop?.risk_level || 'low').toLowerCase();

  return (
    <motion.div
      initial={{ y: 80, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      exit={{ y: 80, opacity: 0 }}
      transition={{ type: 'spring', stiffness: 260, damping: 26 }}
      className="absolute bottom-5 left-1/2 -translate-x-1/2 z-[2000] w-[520px] max-w-[95vw]"
    >
      <div className="nav-hud rounded-2xl overflow-hidden shadow-2xl shadow-black/60">
        {/* Progress bar */}
        <div className="h-1 bg-slate-100/60">
          <motion.div
            className="h-full bg-gradient-to-r from-blue-600 to-blue-500"
            animate={{ width: `${((currentIdx + 1) / total) * 100}%` }}
            transition={{ duration: 0.4 }}
          />
        </div>

        <div className="px-5 py-4">
          {/* Top row: current stop */}
          <div className="flex items-start gap-4 mb-4">
            {/* Step badge */}
            <div className="flex-shrink-0 w-12 h-12 rounded-xl bg-blue-600/10 border border-blue-500/40 flex flex-col items-center justify-center">
              <span className="text-[10px] text-blue-600 font-semibold">STOP</span>
              <span className="text-lg font-bold text-slate-900 leading-none">{currentIdx + 1}</span>
            </div>

            {/* Stop details */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1.5">
                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full text-white ${getRiskColor(stop?.risk_level)}`}>
                  {stop?.risk_level || 'Low'} Risk
                </span>
                <span className="text-[10px] text-slate-600">Stop ID #{stop?.stop_id}</span>
                <span className="text-[10px] text-slate-500 ml-auto">{currentIdx + 1} / {total}</span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div className="flex items-center gap-1.5 text-slate-700">
                  <Truck size={11} className="text-slate-500" />
                  Traffic: <strong>{stop?.traffic}/5</strong>
                </div>
                <div className="flex items-center gap-1.5 text-slate-700">
                  <MapPin size={11} className="text-slate-500" />
                  Dist: <strong>{stop?.distance} km</strong>
                </div>
                <div className="flex items-center gap-1.5 text-slate-700">
                  <Cloud size={11} className="text-slate-500" />
                  {weatherLabel(stop?.weather)}
                </div>
              </div>
            </div>
          </div>

          {/* Next stop preview */}
          {nextStop && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/60 border border-slate-200/50 mb-4 text-[11px]">
              <ArrowRight size={12} className="text-slate-400 flex-shrink-0" />
              <span className="text-slate-600">Next:</span>
              <span className="text-slate-800 font-medium">Stop #{nextStop.stop_id}</span>
              <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded text-white ${getRiskColor(nextStop.risk_level)}`}>
                {nextStop.risk_level}
              </span>
            </div>
          )}

          {isLast && (
            <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 mb-4 text-[11px]">
              <CheckCircle2 size={12} className="text-emerald-400" />
              <span className="text-emerald-300 font-medium">All stops completed!</span>
            </div>
          )}

          {/* Controls */}
          <div className="flex items-center gap-2">
            <button
              onClick={onPrev}
              disabled={currentIdx === 0}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-slate-100/60 hover:bg-slate-200 disabled:opacity-30 disabled:cursor-not-allowed text-white text-xs font-medium transition-all"
            >
              <ChevronLeft size={14} /> Prev
            </button>

            <button
              onClick={onNext}
              disabled={isLast}
              className="flex-1 flex items-center justify-center gap-1.5 px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:opacity-30 disabled:cursor-not-allowed text-white text-xs font-semibold transition-all"
            >
              Next Stop <ChevronRight size={14} />
            </button>

            <button
              onClick={onStop}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-rose-600/80 hover:bg-rose-500 text-white text-xs font-medium transition-all"
            >
              <Square size={12} /> End
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// ─── Main Component ────────────────────────────────────
function App() {
  const [deliveries, setDeliveries] = useState([]);
  const [optimizedRoute, setOptimizedRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [routeLine, setRouteLine] = useState(null);
  const [selectedStop, setSelectedStop] = useState(null);
  const mapRef = useRef(null);

  // ── Navigation state ──
  const [navActive, setNavActive] = useState(false);
  const [navIdx, setNavIdx] = useState(0);
  const [visitedSet, setVisitedSet] = useState(new Set());

  // Fetch real road geometry from OSRM for 3D pitched map rendering, fallback to straight lines
  useEffect(() => {
    if (optimizedRoute && optimizedRoute.features && optimizedRoute.features.length > 0) {
      const getRoute = async () => {
        try {
          const coords = optimizedRoute.features.map(f => `${f.geometry.coordinates[0]},${f.geometry.coordinates[1]}`).join(';');
          const url = `https://router.project-osrm.org/route/v1/driving/${coords}?geometries=geojson&overview=full`;
          const res = await fetch(url);
          const data = await res.json();
          if (data.routes && data.routes[0]) {
            setRouteLine({ type: 'Feature', properties: {}, geometry: data.routes[0].geometry });
          } else {
            throw new Error('No valid routes received from OSRM');
          }
        } catch (e) {
          console.error('OSRM fetch error, falling back to straight lines:', e);
          // Fallback: draw straight lines between stops
          const coordinates = optimizedRoute.features.map(f => f.geometry.coordinates);
          setRouteLine({
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'LineString',
              coordinates: coordinates
            }
          });
        }
      };
      getRoute();
    } else {
      setRouteLine(null);
    }
  }, [optimizedRoute]);

  // Fly camera to current nav stop when index changes
  useEffect(() => {
    if (!navActive || !optimizedRoute?.features) return;
    const f = optimizedRoute.features[navIdx];
    if (!f) return;
    const [lng, lat] = f.geometry.coordinates;
    const stopProps = f.properties;
    
    if (mapRef.current) {
      mapRef.current.flyTo({ center: [lng, lat], zoom: 15, pitch: 65, bearing: navIdx * 15, duration: 1400, essential: true });
    }
    // Mark stop as visited
    setVisitedSet(prev => new Set([...prev, navIdx]));
  }, [navActive, navIdx, optimizedRoute]);

  // ── Handlers ──
  const handleStartNavigation = () => {
    if (!optimizedRoute?.features?.length) return;
    setNavIdx(0);
    setVisitedSet(new Set([0]));
    setNavActive(true);
  };

  const handleStopNavigation = () => {
    setNavActive(false);
    setNavIdx(0);
    setVisitedSet(new Set());
    // Reset camera to overview
    if (mapRef.current) {
      const features = optimizedRoute?.features;
      if (features?.length) {
        const lngs = features.map(f => f.geometry.coordinates[0]);
        const lats = features.map(f => f.geometry.coordinates[1]);
        const centerLng = (Math.min(...lngs) + Math.max(...lngs)) / 2;
        const centerLat = (Math.min(...lats) + Math.max(...lats)) / 2;
        mapRef.current.flyTo({ center: [centerLng, centerLat], zoom: 12.5, pitch: 60, bearing: -20, duration: 1200 });
      }
    }
  };

  const handleNavNext = () => {
    const nextIdx = navIdx + 1;
    if (nextIdx < (optimizedRoute?.features?.length || 0)) setNavIdx(nextIdx);
  };

  const handleNavPrev = () => {
    if (navIdx > 0) setNavIdx(navIdx - 1);
  };

  const handleOptimize = async () => {
    if (deliveries.length === 0) { alert('Please upload a CSV file first!'); return; }
    setLoading(true);
    try {
      const response = await axios.post('http://localhost:8000/optimize_route', { deliveries });
      setOptimizedRoute(response.data.optimized_route);
    } catch (error) {
      console.error('Optimization failed:', error);
      alert('Optimization service unavailable. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    if (!file.name.endsWith('.csv')) { alert('Please upload a CSV file'); return; }
    setLoading(true);
    setUploadedFileName(file.name);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await axios.post('http://localhost:8000/upload_csv', formData);
      if (response.data.error) {
        alert(`Error: ${response.data.error}`);
        setDeliveries([]); setOptimizedRoute(null);
      } else {
        setDeliveries(response.data.deliveries.map(d => ({
          id: d.id, distance: d.distance, traffic_level: d.traffic_level,
          delivery_time: d.delivery_time, weather_condition: d.weather_condition,
          lat: d.lat, lng: d.lng, status: 'Pending'
        })));
        setOptimizedRoute(response.data.optimized_route);
      }
    } catch (error) {
      console.error('Upload failed:', error);
      const serverError = error.response?.data?.error;
      const errMsg = serverError ? `Backend Error: ${serverError}` : 'Failed to upload CSV. Please check the file format or backend connection.';
      alert(errMsg);
      setDeliveries([]); setOptimizedRoute(null);
    } finally {
      setLoading(false);
    }
  };

  const handleClearData = () => {
    setDeliveries([]); setOptimizedRoute(null); setUploadedFileName('');
    setRouteLine(null); setSelectedStop(null);
    setNavActive(false); setNavIdx(0); setVisitedSet(new Set());
    const input = document.getElementById('csv-upload');
    if (input) input.value = '';
  };

  // ── Derived stats ──
  const stats = useMemo(() => {
    if (!optimizedRoute || !optimizedRoute.features)
      return { totalStops: deliveries.length, highRisk: 0, avgProb: 0, optimized: false };
    const high = optimizedRoute.features.filter(s => s.properties.risk_level === 'High').length;
    const avgP = optimizedRoute.features.reduce((a, s) => a + s.properties.risk_probability, 0) / optimizedRoute.features.length;
    return { totalStops: optimizedRoute.features.length, highRisk: high, avgProb: (avgP * 100).toFixed(1), optimized: true };
  }, [optimizedRoute, deliveries]);

  return (
    <div className="flex h-screen overflow-hidden relative">
      <div className="app-bg" />

      {/* ──────── SIDEBAR ──────── */}
      <aside className="sidebar w-64 flex flex-col shrink-0">
        <div className="px-6 py-6 border-b border-black/5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-blue-500 flex items-center justify-center shadow-lg shadow-blue-500/20">
              <Truck size={18} className="text-white" />
            </div>
            <div>
              <h1 className="sidebar-logo text-lg font-bold tracking-tight">RouteOptimizer</h1>
              <p className="text-[11px] text-slate-500 font-medium tracking-wide">AI-POWERED OPTIMIZATION</p>
            </div>
          </div>
        </div>

        <div className="flex-1 px-4 py-5 flex flex-col gap-4">
          <div>
            <h3 className="text-xs font-semibold text-slate-600 uppercase tracking-wider mb-3">Data Input</h3>
            <label className="block">
              <input type="file" accept=".csv" onChange={handleFileUpload} className="hidden" id="csv-upload" />
              <div className="cursor-pointer bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 transition-all p-4 rounded-xl text-center group">
                <Package size={32} className="mx-auto mb-2 text-white group-hover:scale-110 transition-transform" />
                <p className="text-white font-semibold text-sm">Upload CSV File</p>
                <p className="text-slate-100 text-xs mt-1">Click to select file</p>
              </div>
            </label>
          </div>

          {uploadedFileName && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
              className="bg-white/50 border border-slate-200 rounded-lg p-3">
              <p className="text-xs text-slate-600 mb-1">Loaded File:</p>
              <p className="text-sm text-slate-900 font-medium truncate">{uploadedFileName}</p>
              <p className="text-xs text-emerald-400 mt-1">✓ {deliveries.length} deliveries loaded</p>
            </motion.div>
          )}

          {deliveries.length > 0 && (
            <button onClick={handleClearData}
              className="w-full bg-slate-200 hover:bg-rose-600 hover:text-white text-slate-800 px-4 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-center gap-2">
              <Trash2 size={16} /> Clear Data
            </button>
          )}

          <div className="p-4 bg-white/30 rounded-lg border border-slate-200/50">
            <h4 className="text-xs font-semibold text-slate-700 mb-2">Required CSV Columns:</h4>
            <ul className="text-[10px] text-slate-500 space-y-1">
              <li>• distance (km)</li><li>• traffic_level (1-5)</li>
              <li>• delivery_time (min)</li><li>• weather_condition (0-2)</li>
              <li>• lat (latitude)</li><li>• lng (longitude)</li>
            </ul>
          </div>
        </div>

        <div className="px-4 py-4">
          <div className="system-status">
            <div className="flex items-center gap-2 mb-3">
              <div className="status-dot" />
              <span className="text-xs font-semibold text-slate-700">System Online</span>
            </div>
            <div className="space-y-2 text-[11px] text-slate-500">
              <div className="flex justify-between"><span>ML Model</span><span className="text-blue-600 font-medium">v1.0 Active</span></div>
              <div className="flex justify-between"><span>GA Optimizer</span><span className="text-emerald-400 font-medium">Ready</span></div>
              <div className="flex justify-between"><span>Backend</span><span className="text-emerald-400 font-medium">Connected</span></div>
            </div>
          </div>
        </div>
      </aside>

      {/* ──────── MAIN CONTENT ──────── */}
      <main className="flex-1 flex flex-col overflow-hidden relative z-10">
        {/* Header */}
        <header className="app-header h-16 flex items-center justify-between px-6 shrink-0">
          <div>
            <h2 className="text-base font-semibold text-slate-900">Operations Dashboard</h2>
            <p className="text-xs text-slate-500 mt-0.5">Upload CSV &amp; calculate optimized route</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Start Navigation Button — only visible when route is optimized and not navigating */}
            <AnimatePresence>
              {stats.optimized && !navActive && (
                <motion.button
                  id="start-nav-btn"
                  key="nav-btn"
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.85 }}
                  onClick={handleStartNavigation}
                  className="nav-start-btn flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-white text-sm font-semibold"
                >
                  <Navigation size={16} />
                  Start Navigation
                </motion.button>
              )}
              {navActive && (
                <motion.div
                  key="nav-active-badge"
                  initial={{ opacity: 0, scale: 0.85 }}
                  animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.85 }}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 text-sm font-semibold"
                >
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Navigating — Stop {navIdx + 1} / {optimizedRoute?.features?.length}
                </motion.div>
              )}
            </AnimatePresence>

            <button
              id="optimize-btn"
              onClick={handleOptimize}
              disabled={loading || deliveries.length === 0}
              className="optimize-btn flex items-center gap-2.5 px-5 py-2.5 rounded-xl text-white text-sm font-semibold"
            >
              {loading ? (
                <><span className="loading-spinner" /> Optimizing…</>
              ) : (
                <><Route size={16} /> Calculate Optimal Route <ArrowRight size={14} /></>
              )}
            </button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-auto p-5 custom-scrollbar">
          {/* Stat Cards */}
          <div className="grid grid-cols-4 gap-4 mb-5">
            {[
              { label: 'Total Stops', value: stats.totalStops, icon: MapPin, color: 'from-blue-500/15 to-blue-500/5', iconBg: 'bg-blue-500/15 text-blue-600' },
              { label: 'High Risk', value: stats.highRisk, icon: AlertTriangle, color: 'from-rose-500/20 to-rose-500/5', iconBg: 'bg-rose-500/15 text-rose-500' },
              { label: 'Avg Confidence', value: stats.optimized ? stats.avgProb : '—', suffix: stats.optimized ? '%' : '', icon: Shield, color: 'from-emerald-500/15 to-emerald-500/5', iconBg: 'bg-emerald-500/15 text-emerald-600' },
              { label: 'Status', value: navActive ? 'Navigating' : stats.optimized ? 'Optimized' : 'Pending', icon: navActive ? Navigation : Zap, color: navActive ? 'from-emerald-500/15 to-emerald-500/5' : stats.optimized ? 'from-blue-500/15 to-blue-500/5' : 'from-slate-500/10 to-slate-500/5', iconBg: navActive ? 'bg-emerald-500/15 text-emerald-600' : stats.optimized ? 'bg-blue-500/15 text-blue-600' : 'bg-slate-500/10 text-slate-500' },
            ].map((stat, idx) => {
              const Icon = stat.icon;
              return (
                <motion.div key={stat.label} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.08, type: 'spring', stiffness: 180, damping: 22 }} className="stat-card">
                  <div className={`absolute inset-0 bg-gradient-to-br ${stat.color} rounded-2xl pointer-events-none`} />
                  <div className="relative flex items-start justify-between">
                    <div>
                      <p className="text-[11px] text-slate-500 font-medium uppercase tracking-wider mb-1.5">{stat.label}</p>
                      <p className="text-2xl font-bold text-slate-900"><AnimatedNumber value={stat.value} suffix={stat.suffix || ''} /></p>
                    </div>
                    <div className={`stat-icon ${stat.iconBg}`}><Icon size={20} /></div>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* Map + Risk Panel */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-5" style={{ height: 'calc(100vh - 240px)' }}>
            {/* Map */}
            <div className="lg:col-span-2 map-panel rounded-2xl flex flex-col relative">
              {/* Legend */}
              <div className="absolute top-4 left-4 z-[1000] map-legend px-4 py-3">
                <h3 className="text-xs font-semibold text-slate-800 mb-2 flex items-center gap-1.5">
                  <Activity size={12} className="text-slate-400" />
                  {navActive ? '🧭 Navigation Mode' : 'Live Route Map'}
                </h3>
                <div className="flex items-center gap-3 text-[10px] text-slate-600">
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-emerald-400" /> Low</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-amber-400" /> Medium</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-rose-400" /> High</span>
                  <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-gray-400" /> Depot</span>
                  {navActive && <span className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" /> Current</span>}
                </div>
              </div>

              <div className="flex-1 min-h-0 rounded-2xl overflow-hidden relative">
                <Map
                  ref={mapRef}
                  initialViewState={{ longitude: 77.5946, latitude: 12.9716, zoom: 12.5, pitch: 60, bearing: -20 }}
                  mapStyle="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
                  style={{ width: '100%', height: '100%' }}
                >
                  {/* Route line */}
                  {routeLine && (
                    <Source type="geojson" data={routeLine}>
                      <Layer id="route-line-bg" type="line" paint={{ 'line-color': '#bfdbfe', 'line-width': 8, 'line-opacity': 0.6 }} />
                      <Layer id="route-line" type="line" paint={{ 'line-color': navActive ? '#0ea5e9' : '#2563eb', 'line-width': 4, 'line-opacity': 0.9 }} />
                    </Source>
                  )}

                  {/* Markers */}
                  {(optimizedRoute ? optimizedRoute.features : deliveries).map((item, idx) => {
                    const stop = optimizedRoute ? item.properties : item;
                    const lat = optimizedRoute ? item.geometry.coordinates[1] : item.lat;
                    const lng = optimizedRoute ? item.geometry.coordinates[0] : item.lng;
                    const data = stop.details || stop;
                    const risk = stop.risk_level || 'Pending';
                    const isDepot = (stop.id || stop.stop_id) === 1;
                    const isCurrent = navActive && idx === navIdx;
                    const isVisited = navActive && visitedSet.has(idx) && !isCurrent;

                    return (
                      <MapMarker key={idx} longitude={lng} latitude={lat} anchor="bottom"
                        onClick={(e) => { e.originalEvent.stopPropagation(); if (!navActive) setSelectedStop({ stop, data, lat, lng, risk }); }}>
                        {isCurrent ? (
                          // Pulsing current-stop marker
                          <div className="relative flex items-center justify-center">
                            <span className="absolute w-14 h-14 rounded-full bg-cyan-400/30 animate-ping" />
                            <span className="absolute w-10 h-10 rounded-full bg-cyan-400/20 animate-pulse" />
                            <div className="relative w-10 h-10 rounded-full bg-cyan-400 border-3 border-white flex items-center justify-center shadow-xl shadow-cyan-400/50 cursor-pointer z-10">
                              <Navigation size={18} className="text-white" />
                            </div>
                          </div>
                        ) : isDepot ? (
                          <div className="w-8 h-8 rounded-full bg-gray-600 border-2 border-white flex items-center justify-center shadow-lg cursor-pointer hover:scale-110 transition-transform">
                            <Activity size={16} className="text-white" />
                          </div>
                        ) : (
                          <div className={`w-8 h-8 rounded-full border-2 flex items-center justify-center shadow-lg cursor-pointer transition-transform
                            ${isVisited ? 'border-slate-400 bg-slate-600 scale-90 opacity-60' : `border-white ${getRiskColor(risk)} hover:scale-110`}
                            ${navActive && !isCurrent && !isVisited ? `border-dashed ${getRiskBorderColor(risk)} bg-white` : ''}`}>
                            {isVisited
                              ? <CheckCircle2 size={14} className="text-emerald-400" />
                              : <span className="text-white text-xs font-bold">{stop.id || stop.stop_id}</span>
                            }
                          </div>
                        )}
                      </MapMarker>
                    );
                  })}

                  {/* Popup (only when not navigating) */}
                  {selectedStop && !navActive && (
                    <MapPopup longitude={selectedStop.lng} latitude={selectedStop.lat}
                      anchor="top" closeButton={true} closeOnClick={false}
                      onClose={() => setSelectedStop(null)}>
                      <div className="p-2 min-w-[160px]">
                        <div className="flex items-center justify-between border-b border-gray-100 pb-2 mb-2">
                          <strong className="text-[13px] text-gray-800 flex items-center gap-1.5">
                            {(selectedStop.stop.id || selectedStop.stop.stop_id) === 1
                              ? <><Activity size={14} className="text-gray-600" /> Depot</>
                              : <><Package size={14} className="text-slate-600" /> Stop #{selectedStop.stop.id || selectedStop.stop.stop_id}</>}
                          </strong>
                          {(selectedStop.stop.id || selectedStop.stop.stop_id) !== 1 && (
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md text-white ${getRiskColor(selectedStop.risk)}`}>
                              {selectedStop.risk}
                            </span>
                          )}
                        </div>
                        {(selectedStop.stop.id || selectedStop.stop.stop_id) !== 1 && (
                          <div className="space-y-1.5 text-[11px] text-gray-600">
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1"><Shield size={12} className="text-gray-400" /> Confidence:</span>
                              <strong>{((selectedStop.stop.risk_probability || selectedStop.data.risk_probability || 0) * 100).toFixed(1)}%</strong>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1"><Truck size={12} className="text-gray-400" /> Traffic:</span>
                              <strong>{selectedStop.stop.traffic || selectedStop.data.traffic_level}/5</strong>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1"><Cloud size={12} className="text-gray-400" /> Weather:</span>
                              <strong>{weatherLabel(selectedStop.stop.weather ?? selectedStop.data.weather_condition)}</strong>
                            </div>
                            <div className="flex items-center justify-between">
                              <span className="flex items-center gap-1"><MapPin size={12} className="text-gray-400" /> Distance:</span>
                              <strong>{selectedStop.stop.distance || selectedStop.data.distance} km</strong>
                            </div>
                          </div>
                        )}
                        {(selectedStop.stop.id || selectedStop.stop.stop_id) === 1 && (
                          <p className="text-[11px] text-gray-500 text-center italic mt-1">Route starting point</p>
                        )}
                      </div>
                    </MapPopup>
                  )}
                </Map>

                {/* Navigation HUD overlay */}
                <AnimatePresence>
                  {navActive && (
                    <NavigationHUD
                      features={optimizedRoute?.features}
                      currentIdx={navIdx}
                      onPrev={handleNavPrev}
                      onNext={handleNavNext}
                      onStop={handleStopNavigation}
                      visitedSet={visitedSet}
                    />
                  )}
                </AnimatePresence>
              </div>
            </div>

            {/* Right Panel: Risk Analysis */}
            <div className="risk-panel rounded-2xl flex flex-col overflow-hidden">
              <div className="px-5 py-4 border-b border-black/5 shrink-0">
                <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
                  <AlertTriangle size={16} className="text-amber-400" />
                  {navActive ? `Delivery Sequence` : 'Risk Analysis'}
                </h3>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {navActive ? `Stop ${navIdx + 1} of ${optimizedRoute?.features?.length} — follow the order below` : 'AI-predicted delivery risk levels'}
                </p>
              </div>

              <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 custom-scrollbar">
                <AnimatePresence mode="wait">
                  {!optimizedRoute ? (
                    <motion.div key="empty" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
                      className="empty-state h-full">
                      <div className="empty-state-icon text-blue-500 bg-blue-50 border-blue-100"><Route size={28} /></div>
                      <p className="text-sm font-medium text-slate-600">No route optimized yet</p>
                      <p className="text-xs text-slate-600 text-center max-w-[200px]">
                        Click <b>"Calculate Optimal Route"</b> to run AI risk prediction and genetic algorithm optimization.
                      </p>
                    </motion.div>
                  ) : (
                    optimizedRoute.features.map((item, idx) => {
                      const stop = item.properties;
                      const riskLower = (stop.risk_level || 'low').toLowerCase();
                      const probPercent = (stop.risk_probability * 100).toFixed(1);
                      const isCurrent = navActive && idx === navIdx;
                      const isVisited = navActive && visitedSet.has(idx) && !isCurrent;
                      const probColor = riskLower === 'high' ? 'bg-rose-500' : riskLower === 'medium' ? 'bg-amber-500' : 'bg-emerald-500';

                      return (
                        <motion.div
                          key={`stop-${idx}`}
                          initial={{ opacity: 0, x: 20 }}
                          animate={{ opacity: isCurrent ? 1 : isVisited ? 0.5 : 1, x: 0, scale: isCurrent ? 1.02 : 1 }}
                          transition={{ delay: idx * 0.04, type: 'spring', stiffness: 200, damping: 24 }}
                          className={`risk-card risk-${riskLower} relative ${isCurrent ? 'ring-2 ring-cyan-400/70' : ''}`}
                        >
                          {isCurrent && (
                            <div className="absolute -left-1 top-1/2 -translate-y-1/2 w-1.5 h-8 rounded-full bg-cyan-400 animate-pulse" />
                          )}

                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <span className={`text-xs font-bold px-2.5 py-1 rounded-lg ${isCurrent ? 'bg-cyan-400/20 text-cyan-300' : 'text-slate-700 bg-white/80'}`}>
                                #{idx + 1}
                              </span>
                              <span className="text-xs text-slate-500">Stop {stop.stop_id}</span>
                              {isCurrent && <span className="text-[9px] font-bold text-cyan-400 bg-cyan-400/10 px-1.5 py-0.5 rounded-full animate-pulse">CURRENT</span>}
                              {isVisited && <CheckCircle2 size={12} className="text-emerald-400" />}
                            </div>
                            <span className={`risk-badge risk-badge-${riskLower}`}>{stop.risk_level}</span>
                          </div>

                          <div className="grid grid-cols-3 gap-3 text-xs">
                            <div className="flex flex-col items-center gap-1 py-2 rounded-lg bg-slate-50/40">
                              <Truck size={13} className="text-slate-600" />
                              <span className="text-slate-500">Traffic</span>
                              <span className="text-slate-900 font-semibold">{stop.traffic}/5</span>
                            </div>
                            <div className="flex flex-col items-center gap-1 py-2 rounded-lg bg-slate-50/40">
                              <WeatherIcon condition={stop.weather} size={13} />
                              <span className="text-slate-500">Weather</span>
                              <span className="text-slate-900 font-semibold">{weatherLabel(stop.weather)}</span>
                            </div>
                            <div className="flex flex-col items-center gap-1 py-2 rounded-lg bg-slate-50/40">
                              <MapPin size={13} className="text-slate-600" />
                              <span className="text-slate-500">Dist</span>
                              <span className="text-slate-900 font-semibold">{stop.distance}km</span>
                            </div>
                          </div>

                          <div className="mt-3">
                            <div className="flex justify-between items-center text-[10px]">
                              <span className="text-slate-500">Confidence</span>
                              <span className="text-slate-600 font-medium">{probPercent}%</span>
                            </div>
                            <div className="prob-bar-track">
                              <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${probPercent}%` }}
                                transition={{ delay: idx * 0.04 + 0.3, duration: 0.6, ease: 'easeOut' }}
                                className={`prob-bar-fill ${probColor}`}
                              />
                            </div>
                          </div>
                        </motion.div>
                      );
                    })
                  )}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

function AppWithBoundary() {
  return <ErrorBoundary><App /></ErrorBoundary>;
}

export default AppWithBoundary;
