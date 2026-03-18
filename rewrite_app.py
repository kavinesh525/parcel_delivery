import re

with open("client/src/App.jsx", "r", encoding='utf-8') as f:
    content = f.read()

# 1. Replace Imports
content = re.sub(
    r"import \{ MapContainer, TileLayer, Marker, Popup, useMap \} from 'react-leaflet';\nimport 'leaflet/dist/leaflet\.css';\nimport 'leaflet-routing-machine/dist/leaflet-routing-machine\.css';\nimport \{ useEffect \} from 'react';",
    "import React, { useEffect, useState, useMemo } from 'react';\nimport Map, { Marker as MapMarker, Source, Layer, Popup as MapPopup } from 'react-map-gl';\nimport 'maplibre-gl/dist/maplibre-gl.css';",
    content
)

content = content.replace("import { useState, useMemo } from 'react';\n", "")

# 2. Remove leaflet variables and marker config
import_pattern = r"import L from 'leaflet';\nimport '\./App\.css';\n\nimport 'leaflet-routing-machine';[\s\S]*?const weatherLabel = \(w\) => \{\n  if \(w === 0\) return 'Clear';\n  if \(w === 1\) return 'Rainy';\n  return 'Stormy';\n\};\n"

new_imports_and_helpers = """import './App.css';

const weatherLabel = (w) => {
  if (w === 0) return 'Clear';
  if (w === 1) return 'Rainy';
  return 'Stormy';
};

const getRiskColor = (level) => {
  if (level === 'High') return 'bg-rose-500 shadow-rose-500/50';
  if (level === 'Medium') return 'bg-amber-500 shadow-amber-500/50';
  return 'bg-emerald-500 shadow-emerald-500/50';
};
"""
content = re.sub(import_pattern, new_imports_and_helpers, content)

# 3. Remove RoutingMachine
content = re.sub(
    r"// ─── Map Routing Component ───────────────────────[\s\S]*?return null;\n\};\n",
    "",
    content
)

# 4. Add routeLine state and OSRM effect
app_start = "function App() {\n  const [deliveries, setDeliveries] = useState([]);\n"
new_app_start = """function App() {
  const [deliveries, setDeliveries] = useState([]);
  const [routeLine, setRouteLine] = useState(null);
  const [selectedStop, setSelectedStop] = useState(null);
  
  // 3D format routing using OSRM directly to render lines correctly over 3D pitched map
  useEffect(() => {
    if (optimizedRoute && optimizedRoute.features && optimizedRoute.features.length > 0) {
      const getRoute = async () => {
        try {
          const coords = optimizedRoute.features.map(f => `${f.geometry.coordinates[0]},${f.geometry.coordinates[1]}`).join(';');
          const url = `https://router.project-osrm.org/route/v1/driving/${coords}?geometries=geojson&overview=full`;
          const res = await fetch(url);
          const data = await res.json();
          if (data.routes && data.routes[0]) {
            setRouteLine({
              type: 'Feature',
              properties: {},
              geometry: data.routes[0].geometry
            });
          }
        } catch (e) {
          console.error('OSRM fetch error:', e);
        }
      };
      getRoute();
    } else {
      setRouteLine(null);
    }
  }, [optimizedRoute]);
"""
content = content.replace(app_start, new_app_start)

# 5. Overwrite MapContainer with Maplibre setup
map_pattern = r"<MapContainer[\s\S]*?</MapContainer>"
new_map = """<Map
                  initialViewState={{
                    longitude: 77.5946,
                    latitude: 12.9716,
                    zoom: 12.5,
                    pitch: 60,
                    bearing: -20
                  }}
                  mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
                  style={{ width: '100%', height: '100%' }}
                >
                  {routeLine && (
                    <Source type="geojson" data={routeLine}>
                      <Layer 
                        id="route-line" 
                        type="line" 
                        paint={{
                          'line-color': '#6366f1',
                          'line-width': 4,
                          'line-opacity': 0.8
                        }} 
                      />
                    </Source>
                  )}

                  {(optimizedRoute ? optimizedRoute.features : deliveries).map((item, idx) => {
                    const stop = optimizedRoute ? item.properties : item;
                    const lat = optimizedRoute ? item.geometry.coordinates[1] : item.lat;
                    const lng = optimizedRoute ? item.geometry.coordinates[0] : item.lng;
                    const data = stop.details || stop;
                    const risk = stop.risk_level || 'Pending';
                    const isDepot = (stop.id || stop.stop_id) === 1;

                    return (
                      <MapMarker 
                        key={idx} 
                        longitude={lng} 
                        latitude={lat}
                        anchor="bottom"
                        onClick={(e) => {
                          e.originalEvent.stopPropagation();
                          setSelectedStop({ stop, data, lat, lng, risk });
                        }}
                      >
                        {isDepot ? (
                          <div className="w-8 h-8 rounded-full bg-violet-600 border-2 border-white flex items-center justify-center shadow-lg shadow-violet-600/50 cursor-pointer hover:scale-110 transition-transform">
                            <Activity size={16} className="text-white" />
                          </div>
                        ) : (
                          <div className={`w-8 h-8 rounded-full border-2 border-white flex items-center justify-center shadow-lg cursor-pointer hover:scale-110 transition-transform ${getRiskColor(risk)}`}>
                            <span className="text-white text-xs font-bold">{stop.id || stop.stop_id}</span>
                          </div>
                        )}
                      </MapMarker>
                    );
                  })}
                  
                  {selectedStop && (
                    <MapPopup
                      longitude={selectedStop.lng}
                      latitude={selectedStop.lat}
                      anchor="top"
                      closeButton={true}
                      closeOnClick={false}
                      onClose={() => setSelectedStop(null)}
                      className="custom-map-popup"
                    >
                      <div className="p-2 min-w-[160px]">
                        <div className="flex items-center justify-between border-b border-gray-100 pb-2 mb-2">
                          <strong className="text-[13px] text-gray-800 flex items-center gap-1.5">
                            {(selectedStop.stop.id || selectedStop.stop.stop_id) === 1 ? (
                              <><Activity size={14} className="text-violet-600" /> Depot</>
                            ) : (
                              <><Package size={14} className="text-indigo-600" /> Stop #{selectedStop.stop.id || selectedStop.stop.stop_id}</>
                            )}
                          </strong>
                          {(selectedStop.stop.id || selectedStop.stop.stop_id) !== 1 && (
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                              selectedStop.risk === 'High' ? 'bg-rose-100 text-rose-700' :
                              selectedStop.risk === 'Medium' ? 'bg-amber-100 text-amber-700' :
                              'bg-emerald-100 text-emerald-700'
                            }`}>
                              {selectedStop.risk}
                            </span>
                          )}
                        </div>
                        
                        {(selectedStop.stop.id || selectedStop.stop.stop_id) !== 1 && (
                            <div className="space-y-1.5 text-[11px] text-gray-600">
                              <div className="flex items-center justify-between">
                                <span className="flex items-center gap-1"><Shield size={12} className="text-gray-400"/> Confidence:</span>
                                <strong className="font-medium">{(selectedStop.stop.risk_probability * 100 || selectedStop.data.risk_probability * 100 || 0).toFixed(1)}%</strong>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="flex items-center gap-1"><Truck size={12} className="text-gray-400"/> Traffic:</span>
                                <strong className="font-medium">{selectedStop.stop.traffic || selectedStop.data.traffic_level}/5</strong>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="flex items-center gap-1"><Cloud size={12} className="text-gray-400"/> Weather:</span>
                                <strong className="font-medium flex items-center gap-1">
                                  {weatherLabel(selectedStop.stop.weather ?? selectedStop.data.weather_condition)}
                                </strong>
                              </div>
                              <div className="flex items-center justify-between">
                                <span className="flex items-center gap-1"><MapPin size={12} className="text-gray-400"/> Distance:</span>
                                <strong className="font-medium">{selectedStop.stop.distance || selectedStop.data.distance} km</strong>
                              </div>
                            </div>
                        )}
                        {(selectedStop.stop.id || selectedStop.stop.stop_id) === 1 && (
                          <p className="text-[11px] text-gray-500 text-center italic mt-1">Route starting point</p>
                        )}
                      </div>
                    </MapPopup>
                  )}
                </Map>"""

content = re.sub(map_pattern, new_map, content)

with open("client/src/App.jsx", "w", encoding='utf-8') as f:
    f.write(content)

print("Modification complete")
