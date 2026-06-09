"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas, useFrame } from "@react-three/fiber";
import { useMemo, useRef } from "react";
import type { Group } from "three";

import type { OrgGraphNode } from "@/types/intelligence";

const fallbackNodes: OrgGraphNode[] = [
  { id: "engineering", label: "Engineering", risk: 72 },
  { id: "platform", label: "Platform", risk: 54 },
  { id: "finance", label: "Finance", risk: 31 },
  { id: "security", label: "Security", risk: 63 },
  { id: "sales", label: "Sales", risk: 47 },
];

function NodeRing({ nodes }: { nodes: OrgGraphNode[] }) {
  const groupRef = useRef<Group>(null);
  const positions = useMemo(
    () =>
      nodes.flatMap((node, nodeIndex) => {
        const satellites = Array.from({ length: 3 }, (_, satelliteIndex) => {
          const angle = ((nodeIndex * 3 + satelliteIndex) / (nodes.length * 3)) * Math.PI * 2;
          const radius = 1.6 + node.risk / 90 + satelliteIndex * 0.18;
          return {
            id: `${node.id}-${nodeIndex}-${satelliteIndex}`,
            position: [Math.cos(angle) * radius, (node.risk - 50) / 145 + satelliteIndex * 0.08, Math.sin(angle) * radius] as const,
            risk: Math.min(100, node.risk + satelliteIndex * 5),
            primary: satelliteIndex === 0,
          };
        });
        return satellites;
      }),
    [nodes],
  );

  useFrame((_, delta) => {
    if (groupRef.current) groupRef.current.rotation.y += delta * 0.08;
  });

  return (
    <group ref={groupRef}>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[2.25, 0.01, 12, 96]} />
        <meshBasicMaterial color="#2EE9D3" transparent opacity={0.55} />
      </mesh>
      <mesh rotation={[Math.PI / 2, 0, 0]}>
        <torusGeometry args={[1.35, 0.01, 12, 96]} />
        <meshBasicMaterial color="#F6B44B" transparent opacity={0.35} />
      </mesh>
      {positions.map((node) => (
        <mesh key={node.id} position={node.position}>
          <sphereGeometry args={[node.primary ? 0.12 : 0.065, 24, 24]} />
          <meshStandardMaterial
            color={node.risk >= 70 ? "#F05D5E" : node.risk >= 55 ? "#F6B44B" : "#8EE3FF"}
            emissive={node.risk >= 70 ? "#F05D5E" : "#2EE9D3"}
            emissiveIntensity={0.22 + node.risk / 240}
          />
        </mesh>
      ))}
      <mesh>
        <icosahedronGeometry args={[0.62, 1]} />
        <meshStandardMaterial color="#2EE9D3" emissive="#2EE9D3" emissiveIntensity={0.25} wireframe />
      </mesh>
    </group>
  );
}

export function EnterpriseTwinScene({ nodes = fallbackNodes }: { nodes?: OrgGraphNode[] }) {
  const highRisk = nodes.reduce((max, node) => Math.max(max, node.risk), 0);
  return (
    <section className="relative h-[420px] overflow-hidden border border-line/80 bg-panel/85 shadow-control backdrop-blur">
      <div className="absolute z-10 p-5">
        <p className="text-xs uppercase text-cyan">Shadow Company AI</p>
        <h2 className="mt-2 max-w-sm text-2xl font-semibold text-white">Digital twin simulation core</h2>
        <p className="mt-2 text-xs text-slate-500">{nodes.length} live org nodes, peak risk {highRisk}%</p>
      </div>
      <Canvas camera={{ position: [0, 2.2, 5.2], fov: 48 }}>
        <color attach="background" args={["#070B10"]} />
        <ambientLight intensity={0.6} />
        <pointLight position={[3, 3, 3]} intensity={1.3} color="#8EE3FF" />
        <NodeRing nodes={nodes} />
        <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.7} />
      </Canvas>
    </section>
  );
}
