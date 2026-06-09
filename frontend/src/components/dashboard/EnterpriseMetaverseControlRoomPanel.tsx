"use client";

import { Edges, Line, OrbitControls, Text } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { Group } from "three";
import {
  BarChart3,
  Bot,
  Building2,
  Cable,
  Command,
  Layers3,
  Loader2,
  Mic,
  Play,
  Radio,
  RefreshCw,
  Route,
  Send,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import type {
  EnterpriseMetaverseControlRoomResponse,
  MetaverseAgentAvatar,
  MetaverseConnection,
  MetaverseOverlay,
  MetaverseRoom,
  MetaverseVoiceNavigationResponse,
} from "@/types/enterprise-metaverse";

const retryDelay = (attempt: number) => new Promise((resolve) => window.setTimeout(resolve, 900 * (attempt + 1)));

const riskTone = {
  low: "border-mint/30 bg-mint/10 text-mint",
  medium: "border-amber/30 bg-amber/10 text-amber",
  high: "border-orange-400/30 bg-orange-400/10 text-orange-300",
  critical: "border-rose/30 bg-rose/10 text-rose",
} satisfies Record<MetaverseRoom["riskLevel"], string>;

export function EnterpriseMetaverseControlRoomPanel() {
  const [controlRoom, setControlRoom] = useState<EnterpriseMetaverseControlRoomResponse | null>(null);
  const [selectedRoomId, setSelectedRoomId] = useState("executive-command-center");
  const [voiceCommand, setVoiceCommand] = useState("Show highest risk department.");
  const [voiceResponse, setVoiceResponse] = useState<MetaverseVoiceNavigationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [navigating, setNavigating] = useState(false);
  const [streamStatus, setStreamStatus] = useState("connecting");
  const [error, setError] = useState("");
  const manualUpdateUntil = useRef(0);

  const loadDefault = useCallback(async () => {
    setLoading(true);
    setError("");
    manualUpdateUntil.current = 0;
    try {
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          const payload = await fetchJson<EnterpriseMetaverseControlRoomResponse>("/api/metaverse/control-room/default");
          if (!isMetaverse(payload)) throw new Error("Malformed metaverse payload");
          setControlRoom(payload);
          setSelectedRoomId(payload.navigation.selectedRoomId);
          setStreamStatus((status) => (status === "connecting" ? "polling" : status));
          return;
        } catch (loadError) {
          if (attempt === 2) throw loadError;
          await retryDelay(attempt);
        }
      }
    } catch {
      setError("Enterprise Metaverse Control Room could not load live virtual company data.");
    } finally {
      setLoading(false);
    }
  }, []);

  const runSimulation = useCallback(async () => {
    setSimulating(true);
    setError("");
    manualUpdateUntil.current = Date.now() + 30000;
    try {
      const payload = await fetchJson<EnterpriseMetaverseControlRoomResponse>("/api/metaverse/control-room/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenarioType: "mass_resignation",
          question: "What happens if 30% of Engineering resigns?",
          targetRoomId: selectedRoomId || "engineering-room",
          magnitudePercent: 30,
          horizonMonths: 6,
        }),
      });
      if (!isMetaverse(payload)) throw new Error("Malformed simulation payload");
      setControlRoom(payload);
      setSelectedRoomId(payload.navigation.selectedRoomId);
    } catch {
      setError("Metaverse simulation visualization failed.");
    } finally {
      setSimulating(false);
    }
  }, [selectedRoomId]);

  const runVoiceNavigation = useCallback(async () => {
    if (!voiceCommand.trim()) return;
    setNavigating(true);
    try {
      const payload = await fetchJson<MetaverseVoiceNavigationResponse>("/api/metaverse/control-room/voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: voiceCommand }),
      });
      if (!isVoiceNavigation(payload)) throw new Error("Malformed voice navigation payload");
      setVoiceResponse(payload);
      setSelectedRoomId(payload.targetRoomId);
    } catch {
      setError("Voice navigation command failed.");
    } finally {
      setNavigating(false);
    }
  }, [voiceCommand]);

  useEffect(() => {
    const timer = window.setTimeout(() => void loadDefault(), 0);
    return () => window.clearTimeout(timer);
  }, [loadDefault]);

  useEffect(() => {
    const source = new EventSource("/api/metaverse/control-room/stream");
    source.addEventListener("enterprise_metaverse", (event) => {
      if (Date.now() < manualUpdateUntil.current) return;
      try {
        const payload = JSON.parse((event as MessageEvent).data) as EnterpriseMetaverseControlRoomResponse;
        if (isMetaverse(payload)) {
          setControlRoom(payload);
          setStreamStatus("live");
        }
      } catch {
        setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
      }
    });
    source.onerror = () => setStreamStatus((status) => (status === "live" ? "live" : "degraded"));
    return () => source.close();
  }, []);

  const selectedRoom = useMemo(
    () => controlRoom?.rooms.find((room) => room.roomId === selectedRoomId) ?? controlRoom?.rooms[0] ?? null,
    [controlRoom, selectedRoomId],
  );
  const selectedOverlays = useMemo(
    () => controlRoom?.overlays.filter((overlay) => overlay.roomId === selectedRoom?.roomId) ?? [],
    [controlRoom, selectedRoom],
  );
  const riskChartData = useMemo(
    () =>
      controlRoom?.rooms
        .filter((room) => room.roomType === "department" || room.roomType === "data_room" || room.roomType === "crisis_command_room")
        .slice(0, 10)
        .map((room) => ({
          room: room.name.replace(" Room", "").replace(" Intelligence", ""),
          risk: Math.round(room.riskScore),
          health: Math.round(room.healthScore),
        })) ?? [],
    [controlRoom],
  );

  return (
    <section id="enterprise-metaverse-control-room-panel" data-testid="enterprise-metaverse-control-room-panel" className="min-w-0 overflow-x-hidden bg-void text-slate-100">
      <div className="relative min-h-[820px] overflow-hidden border border-line/80 bg-[#050A0F] shadow-control sm:min-h-[720px]">
        <div className="absolute inset-x-0 top-0 z-20 flex max-w-full flex-col gap-3 p-4 sm:right-auto sm:max-w-4xl sm:p-5">
          <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
            <Layers3 className="size-4" />
            <span className="min-w-0 break-words">Enterprise Metaverse Control Room</span>
            <span className="border border-cyan/25 bg-cyan/10 px-2 py-1 text-cyan">{streamStatus}</span>
          </div>
          <h1 className="max-w-full text-2xl font-semibold leading-tight text-white sm:text-3xl md:max-w-3xl md:text-4xl">3D virtual company intelligence platform</h1>
          <p className="max-w-full break-words text-sm leading-6 text-slate-400 md:max-w-3xl">
            {controlRoom?.executiveBrief ??
              "Verifying 3D rendering, virtual company rooms, analytics overlays, Digital Twin sync, simulations, voice navigation, and agent avatars."}
          </p>
        </div>

        <div className="absolute left-4 right-4 top-[18rem] z-20 flex flex-wrap justify-start gap-2 sm:left-auto sm:right-4 sm:top-4 sm:justify-end">
          <button
            type="button"
            onClick={() => void loadDefault()}
            className="inline-flex h-10 items-center gap-2 border border-line bg-panel/90 px-3 text-sm text-white transition hover:border-cyan/60"
          >
            {loading ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
            Refresh
          </button>
          <button
            type="button"
            onClick={() => void runSimulation()}
            className="inline-flex h-10 items-center gap-2 border border-amber/35 bg-amber/10 px-3 text-sm text-amber transition hover:border-amber"
          >
            {simulating ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />}
            Simulate
          </button>
        </div>

        <MetaverseScene
          rooms={controlRoom?.rooms ?? []}
          connections={controlRoom?.connections ?? []}
          overlays={controlRoom?.overlays ?? []}
          avatars={controlRoom?.agentAvatars ?? []}
          selectedRoomId={selectedRoom?.roomId ?? ""}
          onSelect={setSelectedRoomId}
        />

        <div className="absolute bottom-4 left-4 right-4 z-20 grid min-w-0 gap-3 xl:grid-cols-[1fr_0.85fr]">
          <div className="min-w-0 border border-line/80 bg-panel/90 p-3 backdrop-blur">
            <div className="flex flex-wrap items-center gap-2 text-xs uppercase text-cyan">
              <Mic className="size-4" />
              <span>Voice Navigation</span>
              <span className="border border-line/60 bg-void/60 px-2 py-1 text-slate-400">{voiceResponse?.interpretedAction ?? "ready"}</span>
            </div>
            <div className="mt-3 flex flex-col gap-2 md:flex-row">
              <input
                value={voiceCommand}
                onChange={(event) => setVoiceCommand(event.target.value)}
                className="h-11 min-w-0 flex-1 border border-line bg-void px-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-cyan/70"
                aria-label="Voice command text fallback"
              />
              <button
                type="button"
                onClick={() => void runVoiceNavigation()}
                className="inline-flex h-11 w-full items-center justify-center gap-2 border border-cyan/40 bg-cyan/10 px-4 text-sm text-cyan transition hover:border-cyan md:w-auto"
              >
                {navigating ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
                Execute
              </button>
            </div>
            {voiceResponse ? <p className="mt-3 text-xs leading-5 text-slate-300">{voiceResponse.spokenResponse}</p> : null}
          </div>

          <div className="min-w-0 border border-line/80 bg-panel/90 p-3 backdrop-blur">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-xs uppercase text-cyan">Selected Space</p>
                <h2 className="mt-1 text-lg font-semibold text-white">{selectedRoom?.name ?? "Loading virtual company"}</h2>
              </div>
              {selectedRoom ? <span className={`border px-2 py-1 text-xs uppercase ${riskTone[selectedRoom.riskLevel]}`}>{selectedRoom.riskLevel}</span> : null}
            </div>
            <div className="mt-3 grid min-w-0 grid-cols-3 gap-2">
              <MiniMetric label="Health" value={selectedRoom ? `${Math.round(selectedRoom.healthScore)}%` : "--"} />
              <MiniMetric label="Risk" value={selectedRoom ? `${Math.round(selectedRoom.riskScore)}%` : "--"} />
              <MiniMetric label="Occupancy" value={selectedRoom ? String(selectedRoom.occupancy) : "--"} />
            </div>
          </div>
        </div>
      </div>

      {error ? <div className="mt-4 border border-rose/40 bg-rose/10 px-3 py-2 text-sm text-rose">{error}</div> : null}

      <div className="mt-4 grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Metric icon={Building2} label="Rooms" value={controlRoom ? String(controlRoom.summary.roomCount) : "verifying"} />
        <Metric icon={Layers3} label="Departments" value={controlRoom ? String(controlRoom.summary.departmentRooms) : "verifying"} />
        <Metric icon={BarChart3} label="Overlays" value={controlRoom ? String(controlRoom.summary.activeOverlays) : "verifying"} />
        <Metric icon={Bot} label="Agent Avatars" value={controlRoom ? String(controlRoom.summary.agentAvatars) : "verifying"} />
        <Metric icon={ShieldAlert} label="Highest Risk" value={controlRoom ? `${Math.round(controlRoom.summary.highestRiskScore)}%` : "verifying"} />
        <Metric icon={Sparkles} label="Wow Factor" value={controlRoom ? `${Math.round(controlRoom.summary.judgeWowFactorScore)}%` : "verifying"} />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <Panel title="Room Risk Map" icon={Route}>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={riskChartData}>
                <CartesianGrid stroke="#233142" strokeDasharray="3 3" />
                <XAxis dataKey="room" tick={{ fill: "#94A3B8", fontSize: 10 }} interval={0} angle={-20} height={58} />
                <YAxis tick={{ fill: "#94A3B8", fontSize: 11 }} domain={[0, 100]} />
                <Tooltip contentStyle={{ background: "#0B111B", border: "1px solid #233142", color: "#E5E7EB" }} />
                <Bar dataKey="risk" fill="#F05D5E" radius={[3, 3, 0, 0]} />
                <Bar dataKey="health" fill="#2EE9D3" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Panel>

        <Panel title="Analytics Overlays" icon={Radio}>
          <div className="grid gap-2">
            {selectedOverlays.length ? (
              selectedOverlays.map((overlay) => (
                <div key={overlay.overlayId} className="border border-line/70 bg-void/40 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-semibold text-white">{overlay.label}</span>
                    <span className={`border px-2 py-1 text-[10px] uppercase ${riskTone[overlay.severity]}`}>{Math.round(overlay.value)}%</span>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-500">{overlay.explanation}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500">Select a room to inspect risk, burnout, revenue, security, and simulation overlays.</p>
            )}
          </div>
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-3">
        <Panel title="Digital Twin Sync" icon={Cable}>
          <div className="space-y-2">
            {controlRoom?.digitalTwinSync.map((sync) => (
              <div key={sync.twin} className="border border-line/70 bg-void/35 p-3">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm font-semibold capitalize text-white">{sync.twin} twin</span>
                  <span className="border border-mint/30 bg-mint/10 px-2 py-1 text-[10px] uppercase text-mint">{sync.status}</span>
                </div>
                <p className="mt-2 text-xs leading-5 text-slate-500">{sync.latestSignal}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Agent Avatars" icon={Bot}>
          <div className="space-y-2">
            {controlRoom?.agentAvatars.slice(0, 6).map((avatar) => (
              <div key={avatar.avatarId} className="border border-line/70 bg-void/35 p-3">
                <div className="flex items-center gap-2">
                  <span className="size-2" style={{ backgroundColor: avatar.color }} />
                  <span className="text-sm font-semibold text-white">{avatar.agentName}</span>
                  <span className="text-[10px] uppercase text-slate-500">{Math.round(avatar.confidence * 100)}%</span>
                </div>
                <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-500">{avatar.recommendation}</p>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Simulation Visualization" icon={Command}>
          {controlRoom?.simulation ? (
            <div className="space-y-3">
              <p className="text-sm leading-6 text-slate-300">{controlRoom.simulation.question}</p>
              <div className="grid grid-cols-2 gap-2">
                <MiniMetric label="Risk Delta" value={`+${Math.round(controlRoom.simulation.riskDelta)}%`} />
                <MiniMetric label="Revenue" value={`${Math.round(controlRoom.simulation.revenueImpactPercent)}%`} />
                <MiniMetric label="Burnout" value={`+${Math.round(controlRoom.simulation.burnoutDelta)}%`} />
                <MiniMetric label="Productivity" value={`${Math.round(controlRoom.simulation.productivityDelta)}%`} />
              </div>
              <div className="space-y-1">
                {controlRoom.simulation.recommendedActions.slice(0, 3).map((action) => (
                  <p key={action} className="border border-line/70 bg-void/35 px-3 py-2 text-xs leading-5 text-slate-400">
                    {action}
                  </p>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Run a scenario to visualize risk propagation through the virtual company.</p>
          )}
        </Panel>
      </div>

      <div className="mt-4 border border-line/80 bg-panel/85 p-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-xs uppercase text-cyan">Final Verification</p>
            <h2 className="mt-1 text-xl font-semibold text-white">{controlRoom?.finalVerdict ?? "Enterprise Metaverse Control Room verification running"}</h2>
          </div>
          <div className="grid gap-2 sm:grid-cols-3 lg:min-w-[520px]">
            <MiniMetric label="Production" value={controlRoom ? `${Math.round(controlRoom.summary.productionReadinessScore)}%` : "--"} />
            <MiniMetric label="Innovation" value={controlRoom ? `${Math.round(controlRoom.summary.innovationScore)}%` : "--"} />
            <MiniMetric label="FPS Target" value={controlRoom ? `${controlRoom.performance.estimatedFps}` : "--"} />
          </div>
        </div>
      </div>
    </section>
  );
}

function MetaverseScene({
  rooms,
  connections,
  overlays,
  avatars,
  selectedRoomId,
  onSelect,
}: {
  rooms: MetaverseRoom[];
  connections: MetaverseConnection[];
  overlays: MetaverseOverlay[];
  avatars: MetaverseAgentAvatar[];
  selectedRoomId: string;
  onSelect: (roomId: string) => void;
}) {
  return (
    <Canvas className="absolute inset-0 h-full w-full" camera={{ position: [10, 8, 12], fov: 48 }} dpr={[1, 1.6]}>
      <color attach="background" args={["#050A0F"]} />
      <fog attach="fog" args={["#050A0F", 16, 34]} />
      <ambientLight intensity={0.55} />
      <pointLight position={[0, 8, 0]} intensity={1.4} color="#8EE3FF" />
      <pointLight position={[-7, 5, -6]} intensity={1.2} color="#F05D5E" />
      <pointLight position={[7, 5, 6]} intensity={1.1} color="#2EE9D3" />
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.08, 0]}>
        <planeGeometry args={[22, 22, 32, 32]} />
        <meshStandardMaterial color="#08111B" metalness={0.2} roughness={0.72} />
      </mesh>
      <gridHelper args={[22, 22, "#233142", "#0E1B2A"]} position={[0, 0.01, 0]} />
      <VirtualCompanyWorld rooms={rooms} connections={connections} overlays={overlays} avatars={avatars} selectedRoomId={selectedRoomId} onSelect={onSelect} />
      <OrbitControls enablePan enableZoom autoRotate autoRotateSpeed={0.22} maxDistance={24} minDistance={5} />
    </Canvas>
  );
}

function VirtualCompanyWorld({
  rooms,
  connections,
  overlays,
  avatars,
  selectedRoomId,
  onSelect,
}: {
  rooms: MetaverseRoom[];
  connections: MetaverseConnection[];
  overlays: MetaverseOverlay[];
  avatars: MetaverseAgentAvatar[];
  selectedRoomId: string;
  onSelect: (roomId: string) => void;
}) {
  const groupRef = useRef<Group>(null);
  const roomLookup = useMemo(() => new Map(rooms.map((room) => [room.roomId, room])), [rooms]);

  useFrame((_, delta) => {
    if (groupRef.current) groupRef.current.rotation.y += delta * 0.015;
  });

  return (
    <group ref={groupRef}>
      {connections.map((connection, index) => {
        const source = roomLookup.get(connection.sourceRoomId);
        const target = roomLookup.get(connection.targetRoomId);
        if (!source || !target) return null;
        const color = connection.connectionType === "risk_propagation" ? "#F05D5E" : connection.connectionType === "data_link" ? "#8EE3FF" : "#2EE9D3";
        return (
          <Line
            key={`${connection.sourceRoomId}-${connection.targetRoomId}-${index}`}
            points={[
              [source.position.x, source.position.y + 0.12, source.position.z],
              [target.position.x, target.position.y + 0.12, target.position.z],
            ]}
            color={color}
            transparent
            opacity={0.2 + connection.strength * 0.35}
            lineWidth={connection.connectionType === "risk_propagation" ? 2 : 1}
          />
        );
      })}
      {rooms.map((room) => (
        <RoomMesh key={room.roomId} room={room} selected={room.roomId === selectedRoomId} onSelect={onSelect} />
      ))}
      {overlays
        .filter((overlay) => overlay.severity === "high" || overlay.severity === "critical" || overlay.overlayType === "simulation")
        .slice(0, 24)
        .map((overlay) => {
          const room = roomLookup.get(overlay.roomId);
          if (!room) return null;
          return <OverlayBeacon key={overlay.overlayId} overlay={overlay} room={room} selected={room.roomId === selectedRoomId} />;
        })}
      {avatars.map((avatar) => (
        <AgentAvatarMesh key={avatar.avatarId} avatar={avatar} />
      ))}
    </group>
  );
}

function RoomMesh({ room, selected, onSelect }: { room: MetaverseRoom; selected: boolean; onSelect: (roomId: string) => void }) {
  const meshRef = useRef<Group>(null);
  useFrame((state) => {
    if (!meshRef.current || !selected) return;
    meshRef.current.position.y = room.position.y + Math.sin(state.clock.elapsedTime * 2.2) * 0.05;
  });
  const height = Math.max(0.28, room.size.y);
  return (
    <group ref={meshRef} position={[room.position.x, room.position.y + height / 2, room.position.z]}>
      <mesh onClick={(event) => { event.stopPropagation(); onSelect(room.roomId); }} scale={[room.size.x, height, room.size.z]}>
        <boxGeometry args={[1, 1, 1]} />
        <meshStandardMaterial color={room.color} emissive={room.glowColor} emissiveIntensity={selected ? 0.52 : 0.18 + room.riskScore / 420} metalness={0.35} roughness={0.36} />
        <Edges color={selected ? "#FFFFFF" : room.glowColor} />
      </mesh>
      <mesh position={[0, height / 2 + 0.12, 0]} rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[Math.max(room.size.x, room.size.z) * 0.43, selected ? 0.025 : 0.012, 12, 80]} />
        <meshBasicMaterial color={room.glowColor} transparent opacity={selected ? 0.92 : 0.34} />
      </mesh>
      <Text position={[0, height / 2 + 0.34, 0]} fontSize={selected ? 0.22 : 0.16} color="#E5E7EB" anchorX="center" anchorY="middle" maxWidth={2.4}>
        {room.name}
      </Text>
    </group>
  );
}

function OverlayBeacon({ overlay, room, selected }: { overlay: MetaverseOverlay; room: MetaverseRoom; selected: boolean }) {
  return (
    <group position={[room.position.x, room.position.y + room.size.y + 0.7, room.position.z]}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[selected ? 0.46 : 0.32, 0.018, 10, 72]} />
        <meshBasicMaterial color={overlay.color} transparent opacity={selected ? 0.9 : 0.58} />
      </mesh>
      <mesh>
        <sphereGeometry args={[selected ? 0.11 : 0.07, 20, 20]} />
        <meshStandardMaterial color={overlay.color} emissive={overlay.color} emissiveIntensity={0.7} />
      </mesh>
    </group>
  );
}

function AgentAvatarMesh({ avatar }: { avatar: MetaverseAgentAvatar }) {
  const groupRef = useRef<Group>(null);
  useFrame((state) => {
    if (!groupRef.current) return;
    groupRef.current.position.y = avatar.position.y + Math.sin(state.clock.elapsedTime * 2.5 + avatar.position.x) * 0.08;
  });
  return (
    <group ref={groupRef} position={[avatar.position.x, avatar.position.y, avatar.position.z]}>
      <mesh>
        <sphereGeometry args={[0.16, 24, 24]} />
        <meshStandardMaterial color={avatar.color} emissive={avatar.color} emissiveIntensity={0.48} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[0.24, 0.01, 10, 48]} />
        <meshBasicMaterial color={avatar.color} transparent opacity={0.7} />
      </mesh>
    </group>
  );
}

function Metric({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <div className="min-w-0 border border-line/80 bg-panel/85 p-3">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs uppercase text-slate-500">{label}</span>
        <Icon className="size-4 text-cyan" />
      </div>
      <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}

function MiniMetric({ label, value }: { label: string; value: string }) {
  return (
    <div className="min-w-0 overflow-hidden border border-line/70 bg-void/50 p-2">
      <p className="text-[10px] uppercase text-slate-500">{label}</p>
      <p className="mt-1 truncate text-sm font-semibold text-white">{value}</p>
    </div>
  );
}

function Panel({ title, icon: Icon, children }: { title: string; icon: LucideIcon; children: React.ReactNode }) {
  return (
    <section className="min-w-0 overflow-hidden border border-line/80 bg-panel/85 p-4">
      <div className="mb-3 flex items-center gap-2 text-xs uppercase text-cyan">
        <Icon className="size-4" />
        <span>{title}</span>
      </div>
      {children}
    </section>
  );
}

async function fetchJson<T>(input: string, init?: RequestInit): Promise<T> {
  const response = await fetch(input, { ...init, cache: "no-store" });
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};
  if (!response.ok) throw new Error(typeof payload?.detail === "string" ? payload.detail : "Request failed");
  return payload as T;
}

function isMetaverse(value: unknown): value is EnterpriseMetaverseControlRoomResponse {
  return Boolean(
    value &&
      typeof value === "object" &&
      "summary" in value &&
      "rooms" in value &&
      Array.isArray((value as EnterpriseMetaverseControlRoomResponse).rooms) &&
      "performance" in value,
  );
}

function isVoiceNavigation(value: unknown): value is MetaverseVoiceNavigationResponse {
  return Boolean(value && typeof value === "object" && "targetRoomId" in value && "spokenResponse" in value && "navigation" in value);
}
