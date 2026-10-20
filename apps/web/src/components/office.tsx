"use client";
import { useRef, useState, Suspense, useCallback, useEffect } from "react";
import { Vector3, Group } from "three";
import { Canvas, ThreeEvent, useFrame } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

import { floors, agentState, type Snapshot, type Row } from "@/lib/domain";

type Vec = [number, number, number];
function Box({
  p,
  s,
  c,
  metal = 0,
  transparent = false,
  opacity = 1,
}: {
  p: Vec;
  s: Vec;
  c: string;
  metal?: number;
  transparent?: boolean;
  opacity?: number;
}) {
  return (
    <mesh position={p} castShadow receiveShadow>
      <boxGeometry args={s} />
      <meshStandardMaterial
        color={c}
        metalness={metal}
        roughness={0.45}
        transparent={transparent}
        opacity={opacity}
      />
    </mesh>
  );
}
function Plant({ p, scale = 1 }: { p: Vec; scale?: number }) {
  return (
    <group position={p} scale={scale}>
      <mesh position={[0, 0.16, 0]} castShadow>
        <cylinderGeometry args={[0.2, 0.14, 0.32, 10]} />
        <meshStandardMaterial color="#dbd4c6" />
      </mesh>
      <mesh position={[0, 0.46, 0]}>
        <cylinderGeometry args={[0.025, 0.025, 0.5, 6]} />
        <meshStandardMaterial color="#627646" />
      </mesh>
      {[
        [-0.1, 0.55, 0],
        [0.12, 0.7, 0.06],
        [0, 0.8, -0.07],
        [-0.14, 0.74, 0.05],
      ].map((v, i) => (
        <mesh
          key={i}
          position={v as Vec}
          scale={[0.16, 0.29, 0.11]}
          rotation={[0.2, i * 1.8, 0.5]}
          castShadow
        >
          <sphereGeometry args={[1, 8, 8]} />
          <meshStandardMaterial color={i % 2 ? "#7b9750" : "#9caf6c"} />
        </mesh>
      ))}
    </group>
  );
}
function Robot({
  p,
  color,
  active,
}: {
  p: Vec;
  color: string;
  active: boolean;
}) {
  const arms = useRef<Group>(null);
  useFrame(({ clock }) => {
    if (arms.current)
      arms.current.rotation.x = active
        ? Math.sin(clock.elapsedTime * 5) * 0.12
        : 0;
  });
  return (
    <group position={p}>
      <Box p={[0, 0.23, 0]} s={[0.29, 0.32, 0.23]} c={color} />
      <mesh position={[0, 0.53, 0]} castShadow>
        <boxGeometry args={[0.36, 0.3, 0.31]} />
        <meshStandardMaterial color={color} roughness={0.35} />
      </mesh>
      <Box p={[0, 0.54, 0.161]} s={[0.27, 0.14, 0.015]} c="#24353a" />
      <Box
        p={[-0.065, 0.56, 0.172]}
        s={[0.037, 0.027, 0.015]}
        c={active ? "#bfffba" : "#dbe8db"}
      />
      <Box
        p={[0.065, 0.56, 0.172]}
        s={[0.037, 0.027, 0.015]}
        c={active ? "#bfffba" : "#dbe8db"}
      />
      <group ref={arms}>
        {[-1, 1].map((n) => (
          <group key={n}>
            <Box p={[n * 0.09, 0.035, 0]} s={[0.1, 0.15, 0.16]} c="#394449" />
            <Box p={[n * 0.21, 0.26, 0]} s={[0.1, 0.27, 0.12]} c={color} />
          </group>
        ))}
      </group>
    </group>
  );
}
function Desk({
  p,
  role,
  snapshot,
  onAgent,
  index,
  color,
}: {
  p: Vec;
  role?: Row;
  snapshot: Snapshot;
  onAgent: (r: Row) => void;
  index: number;
  color: string;
}) {
  const active = role ? agentState(role.key, snapshot) !== "idle" : false;
  return (
    <group
      position={p}
      onClick={
        role
          ? (e: ThreeEvent<MouseEvent>) => {
              e.stopPropagation();
              onAgent(role);
            }
          : undefined
      }
      onPointerOver={(e) => {
        e.stopPropagation();
        document.body.style.cursor = "pointer";
      }}
      onPointerOut={() => {
        document.body.style.cursor = "auto";
      }}
    >
      <Box p={[0, 0.65, 0]} s={[1.75, 0.09, 0.85]} c="#d5b788" />
      {[-0.66, 0.66].map((x) => (
        <Box key={x} p={[x, 0.3, 0]} s={[0.07, 0.65, 0.65]} c="#454d48" />
      ))}
      <Box p={[0, 1.02, -0.18]} s={[0.72, 0.44, 0.045]} c="#28383a" />
      <Box
        p={[0, 1.02, -0.15]}
        s={[0.64, 0.35, 0.012]}
        c={active ? "#a6d6c7" : "#526d6a"}
      />
      <Box p={[0, 0.78, -0.18]} s={[0.05, 0.2, 0.05]} c="#313e3e" />
      <Box p={[0, 0.713, 0.13]} s={[0.48, 0.02, 0.17]} c="#e8e7df" />
      <Box p={[0.58, 0.77, 0.1]} s={[0.13, 0.2, 0.13]} c="#f5cc43" />
      <Box p={[0, 0.34, 0.8]} s={[0.52, 0.1, 0.5]} c="#374744" />
      <Box p={[0, 0.59, 1]} s={[0.5, 0.47, 0.08]} c="#374744" />
      <Robot p={[0, 0.41, 0.65]} color={color} active={active} />
    </group>
  );
}
function Building({
  snapshot,
  selectedFloor,
  onFloor,
  onAgent,
}: {
  snapshot: Snapshot;
  selectedFloor: number | null;
  onFloor: (n: number) => void;
  onAgent: (r: Row) => void;
}) {
  return (
    <group position={[-1, 0, 0]}>
      <Box p={[0, -0.18, 0]} s={[16, 0.35, 9.6]} c="#ddd9cb" />
      {floors.map((floor, f) => {
        const y = f * 2.32;
        const roles = snapshot.roles.filter(
          (r) => r.config.floor === floor.name,
        );
        return (
          <group key={floor.name} position={[0, y, 0]}>
            <mesh
              position={[0, 0.05, 0]}
              receiveShadow
              onClick={(e) => {
                e.stopPropagation();
                onFloor(f);
              }}
            >
              <boxGeometry args={[14.2, 0.2, 7.4]} />
              <meshStandardMaterial
                color={selectedFloor === f ? "#f6dc78" : "#f2efe4"}
              />
            </mesh>
            <Box p={[0, -0.05, 3.69]} s={[14.35, 0.16, 0.12]} c="#f5c932" />
            <Box
              p={[0, 1.12, -3.55]}
              s={[14, 2.05, 0.06]}
              c="#c4d6d2"
              transparent
              opacity={0.36}
            />
            <Box
              p={[-7, 1.12, 0]}
              s={[0.07, 2.1, 7.2]}
              c="#b1c6bf"
              transparent
              opacity={0.18}
            />
            {[-7, -3.5, 0, 3.5, 7].map((x) => (
              <group key={x}>
                <Box p={[x, 1.15, -3.57]} s={[0.085, 2.3, 0.09]} c="#4e5b55" />
                {Math.abs(x) === 7 && (
                  <Box p={[x, 1.15, 3.58]} s={[0.1, 2.3, 0.1]} c="#e9e8dc" />
                )}
              </group>
            ))}
            <Box p={[7.02, 1.1, -1.8]} s={[0.16, 2.2, 3.7]} c="#f2c42a" />
            {Array.from({ length: 12 }, (_, i) => (
              <Box
                key={i}
                p={[7.13, 1.1, -3.5 + i * 0.3]}
                s={[0.04, 2.1, 0.035]}
                c="#dcb21b"
              />
            ))}
            <Box p={[0, 2.14, -3.5]} s={[14, 0.08, 0.06]} c="#374d44" />
            {[0, 1].flatMap((row) =>
              [0, 1, 2, 3].map((col) => {
                const idx = row * 4 + col;
                if (idx >= Math.max(roles.length, 4)) return null;
                return (
                  <Desk
                    key={idx}
                    p={[-5.35 + col * 3.3, 0.16, 1.0 - row * 3.4]}
                    role={roles[idx]}
                    snapshot={snapshot}
                    onAgent={onAgent}
                    index={idx}
                    color={floor.color}
                  />
                );
              }),
            )}
            <Plant p={[-6.35, 0.16, 2.8]} scale={1.15} />
            <Plant p={[6.25, 0.16, 2.6]} scale={1.2} />
            <Plant p={[-0.1, 0.16, -3.1]} scale={0.7} />
          </group>
        );
      })}
      <group position={[0, 14.02, 0]}>
        <Box p={[0, 0, 0]} s={[14.4, 0.25, 7.6]} c="#f5f2e5" />
        <Box p={[3, 0.16, -0.5]} s={[5.5, 0.12, 5]} c="#a6b287" />
        <Box p={[-3, 0.3, -2.8]} s={[5, 0.6, 0.16]} c="#f6ca35" />
        <Box p={[-3, 0.31, 1.4]} s={[3.2, 0.6, 0.95]} c="#d8d7c6" />
        <Box p={[-3, 0.6, 1.8]} s={[3.2, 0.3, 0.17]} c="#c7cbb9" />
        <Box p={[-3, 0.36, -0.3]} s={[1.6, 0.15, 0.7]} c="#af9677" />
        {[-6.1, 6.1].map((x) => (
          <Plant key={x} p={[x, 0.15, -2.6]} scale={1.7} />
        ))}
        <Box p={[2, 1, -2.9]} s={[4.4, 1.8, 0.1]} c="#293d37" />

        <Box p={[0, 0.45, 3.68]} s={[14, 0.06, 0.06]} c="#4c5c4d" />
        {[-6.9, 0, 6.9].map((x) => (
          <Box
            key={x}
            p={[x, 0.25, 3.68]}
            s={[0.055, 0.45, 0.055]}
            c="#4c5c4d"
          />
        ))}
      </group>
      <group position={[8.2, 0, -0.7]}>
        <Box
          p={[0, 7, 0]}
          s={[1.7, 14.2, 3]}
          c="#afc6c0"
          transparent
          opacity={0.19}
        />
        {[-0.85, 0.85].map((x) => (
          <Box key={x} p={[x, 7, 1.5]} s={[0.13, 14.2, 0.13]} c="#35473c" />
        ))}
        {floors.map((f, i) => (
          <group key={i}>
            <Box p={[0, i * 2.32 + 0.1, 0]} s={[1.8, 0.15, 3.1]} c="#ecd15e" />
            <mesh position={[0, i * 2.32 + 1, 1.56]}>
              <circleGeometry args={[0.23, 20]} />
              <meshBasicMaterial color="#2d3f35" />
            </mesh>
          </group>
        ))}
        <Box p={[0, 14.25, 0]} s={[2.2, 0.35, 3.5]} c="#ebc73d" />
      </group>
      <Box p={[0, -0.28, 6]} s={[24, 0.15, 3.7]} c="#e4e0d4" />
      {[-10, -6, 0, 6, 10].map((x, i) => (
        <group key={i}>
          <Plant p={[x, -0.2, 7]} scale={2.3} />
          <Box p={[x, -0.18, 7]} s={[1.5, 0.1, 1.4]} c="#c4c9a4" />
        </group>
      ))}
      <Box p={[1, -0.15, 8]} s={[2.5, 0.06, 0.08]} c="#f6c437" />
      <group position={[-7, 0.15, 5]}>
        <Box p={[0, 0.5, 0]} s={[3, 1, 0.14]} c="#f1c735" />
      </group>
    </group>
  );
}
type Label = {
  key: string;
  x: number;
  y: number;
  role?: Row;
  floor?: number;
  sign?: boolean;
};
function ProjectLabels({
  snapshot,
  onProject,
}: {
  snapshot: Snapshot;
  onProject: (labels: Label[]) => void;
}) {
  const last = useRef("");
  useFrame(({ camera, size }) => {
    const signature = [
      ...camera.matrixWorld.elements,
      camera.zoom,
      size.width,
      size.height,
    ]
      .map((n) => n.toFixed(3))
      .join(",");
    if (last.current === signature) return;
    last.current = signature;
    const project = (p: Vec) => {
      const v = new Vector3(...p).project(camera);
      return {
        x: ((v.x + 1) * size.width) / 2,
        y: ((1 - v.y) * size.height) / 2,
      };
    };
    const labels: Label[] = [];
    floors.forEach((f, i) => {
      labels.push({
        key: "floor" + i,
        floor: i,
        ...project([-8.7, i * 2.32 + 0.7, 3.7]),
      });
      snapshot.roles
        .filter((r) => r.config.floor === f.name)
        .forEach((role, j) => {
          labels.push({
            key: role.key,
            role,
            ...project([
              -6.35 + (j % 4) * 3.3,
              i * 2.32 + 1.8,
              1.0 - Math.floor(j / 4) * 3.4,
            ]),
          });
        });
    });
    labels.push({ key: "roof", sign: true, ...project([1, 15.12, -2.82]) });
    onProject(labels);
  });
  return null;
}
function CameraFocus({
  floor,
  agent,
  snapshot,
}: {
  floor: number | null;
  agent?: Row;
  snapshot: Snapshot;
}) {
  const change = useRef(0);
  const target = useRef(new Vector3(0, 7, 0));
  const zoom = useRef(28);
  useEffect(() => {
    if (agent) {
      const level = floors.findIndex((f) => f.name === agent.config.floor);
      const index = snapshot.roles
        .filter((r) => r.config.floor === agent.config.floor)
        .findIndex((r) => r.key === agent.key);
      target.current.set(
        -6.35 + (index % 4) * 3.3,
        level * 2.32 + 1.1,
        1 - Math.floor(index / 4) * 3.4,
      );
      zoom.current = 48;
    } else if (floor !== null) {
      target.current.set(0, floor * 2.32 + 1.5, 0);
      zoom.current = 35;
    } else {
      target.current.set(0, 7, 0);
      zoom.current = 28;
    }
    change.current = 50;
  }, [floor, agent?.key]);
  useFrame((state) => {
    if (change.current <= 0) return;
    change.current--;
    const controls = state.controls as any;
    if (!controls?.target) return;
    controls.target.lerp(target.current, 0.12);
    const wanted = target.current.clone().add(new Vector3(25, 14, 29));
    state.camera.position.lerp(wanted, 0.1);
    if ("zoom" in state.camera) {
      state.camera.zoom += (zoom.current - state.camera.zoom) * 0.1;
      state.camera.updateProjectionMatrix();
    }
    controls.update();
  });
  return null;
}
export default function Office({
  snapshot,
  selectedFloor,
  onFloor,
  onAgent,
  resetKey,
  focusedAgent,
}: {
  snapshot: Snapshot;
  selectedFloor: number | null;
  onFloor: (n: number) => void;
  onAgent: (r: Row) => void;
  resetKey: number;
  focusedAgent?: Row;
}) {
  const [labels, setLabels] = useState<Label[]>([]);
  return (
    <div className="webgl-office">
      <Canvas
        fallback={
          <div className="scene-loading">
            3D is unavailable. Choose the accessible 2D view above.
          </div>
        }
        key={resetKey}
        shadows
        orthographic
        dpr={[1, 1.6]}
        gl={{
          antialias: true,
          alpha: true,
          powerPreference: "high-performance",
        }}
        camera={{ position: [25, 21, 29], zoom: 28, near: 0.1, far: 200 }}
      >
        <color attach="background" args={["#eeece2"]} />
        <fog attach="fog" args={["#eeece2", 60, 130]} />
        <ambientLight intensity={1.7} />
        <hemisphereLight args={["#fffdf4", "#bcc5a7", 1.3]} />
        <directionalLight
          position={[-12, 30, 20]}
          intensity={3}
          castShadow
          shadow-mapSize={[2048, 2048]}
          shadow-camera-left={-26}
          shadow-camera-right={26}
          shadow-camera-top={25}
          shadow-camera-bottom={-25}
          shadow-bias={-0.0005}
        />
        <Suspense fallback={null}>
          <Building
            snapshot={snapshot}
            selectedFloor={selectedFloor}
            onFloor={onFloor}
            onAgent={onAgent}
          />
        </Suspense>
        <mesh
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, -0.4, 0]}
          receiveShadow
        >
          <planeGeometry args={[200, 200]} />
          <meshStandardMaterial color="#eeece2" roughness={1} />
        </mesh>
        <OrbitControls
          makeDefault
          target={[0, 7, 0]}
          minZoom={16}
          maxZoom={70}
          maxPolarAngle={Math.PI / 2.1}
          minPolarAngle={0.25}
          enableDamping
          dampingFactor={0.08}
        />
        <CameraFocus
          floor={selectedFloor}
          agent={focusedAgent}
          snapshot={snapshot}
        />
        <ProjectLabels snapshot={snapshot} onProject={setLabels} />
      </Canvas>
      <div className="office-labels">
        {labels.map((l) => (
          <div
            className="projected-label"
            key={l.key}
            style={{ left: l.x, top: l.y }}
          >
            {l.role ? (
              <button
                className={
                  "desk-label " +
                  (agentState(l.role.key, snapshot) !== "idle" ? "working" : "")
                }
                onClick={() => onAgent(l.role!)}
              >
                <span
                  className={
                    agentState(l.role.key, snapshot) !== "idle"
                      ? "live-dot"
                      : "idle-dot"
                  }
                />
                {l.role.config.role}
              </button>
            ) : l.floor !== undefined ? (
              <button
                className={
                  "floor-tag " + (selectedFloor === l.floor ? "selected" : "")
                }
                onClick={() => onFloor(l.floor!)}
              >
                <b>{floors[l.floor].short}</b>
                <span>{floors[l.floor].name}</span>
              </button>
            ) : (
              <div className="roof-sign">
                BUILD SOMETHING
                <br />
                <strong>THAT MATTERS.</strong>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
