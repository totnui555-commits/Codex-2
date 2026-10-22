"use client";
import {
  Component,
  type ReactNode,
  Suspense,
  useEffect,
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  Canvas,
  useFrame,
  useThree,
  type ThreeEvent,
} from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";
import {
  Color,
  Matrix4,
  InstancedMesh,
  MeshStandardMaterial,
  Mesh,
  ShaderMaterial,
  Vector3,
  type Object3D,
  type WebGLRenderer,
} from "three";
import {
  sampleSceneFrames,
  type BrowserPerformanceReport,
} from "@/lib/kingdom-performance";
import {
  citizen,
  kingdomActivity,
  groundHeight,
  landmarks,
  landmark,
  lighthouseState,
  route,
  WORLD_VERSION,
  type Landmark,
  type Point,
} from "@/lib/kingdom";
import { money, type Row, type Snapshot } from "@/lib/domain";
import {
  Anchor,
  Castle,
  Compass,
  Crown,
  Eye,
  Flag,
  Mail,
  Map as MapIcon,
  RotateCcw,
  Shield,
  X,
  ZoomIn,
  ZoomOut,
  Search,
  PanelRightClose,
  Maximize2,
  SlidersHorizontal,
} from "lucide-react";

type Citizen = ReturnType<typeof citizen>;
type Quality = "low" | "balanced" | "high";
const presets = [
  { name: "Whole Kingdom", target: [0, 0, 0], camera: [24, 25, 30], zoom: 31 },
  { name: "Royal Keep", target: [0, 2, -5], camera: [15, 16, 14], zoom: 43 },
  {
    name: "Village Square",
    target: [-2, 1, 1],
    camera: [15, 17, 22],
    zoom: 42,
  },
  {
    name: "Workshop Quarter",
    target: [7, 1, -1],
    camera: [22, 17, 21],
    zoom: 43,
  },
  { name: "Harbor Market", target: [5, 0, 6], camera: [22, 17, 28], zoom: 40 },
  {
    name: "Watchtower Ridge",
    target: [-9, 3, -2],
    camera: [5, 17, 19],
    zoom: 43,
  },
];
function Water({ reduced }: { reduced: boolean }) {
  const material = useRef<ShaderMaterial>(null);
  const uniforms = useMemo(() => ({ time: { value: 0 } }), []);
  useFrame(({ clock }) => {
    if (material.current)
      material.current.uniforms.time.value = reduced ? 0 : clock.elapsedTime;
  });
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.19, 0]}>
      <planeGeometry args={[160, 160, 1, 1]} />
      <shaderMaterial
        ref={material}
        uniforms={uniforms}
        vertexShader={`varying vec2 world; void main(){world=position.xy;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`}
        fragmentShader={`varying vec2 world;uniform float time;
      void main(){vec2 p=world;float a=atan(p.y/10.,p.x/14.);float coast=1.+.045*sin(5.*a)+.025*cos(9.*a);float r=length(p/vec2(14.,10.))/coast;
      float shallow=exp(-max(0.,r-1.)*5.);vec3 deep=vec3(.17,.52,.59);vec3 turquoise=vec3(.37,.76,.74);vec3 col=mix(deep,turquoise,shallow);
      float waves=sin(p.x*2.8+p.y*1.8+time*.7)*sin(p.y*3.8-p.x*.9-time*.45);col+=pow(max(0.,waves),14.)*.1;
      float foam=pow(max(0.,sin((r-1.)*61.-time*1.2)),12.)*exp(-abs(r-1.04)*15.);col=mix(col,vec3(.88,.94,.84),foam*.55);
      float caustic=sin(p.x*6.+sin(p.y*3.+time*.25))*sin(p.y*7.+cos(p.x*4.-time*.2));col+=pow(max(0.,caustic),5.)*shallow*.055;
      gl_FragColor=vec4(col,1.);}`}
      />
    </mesh>
  );
}
function Island({
  onSelect,
  onHover,
  quality,
}: {
  quality: Quality;
  onSelect: (l: Landmark) => void;
  onHover: (l: Landmark | null) => void;
}) {
  const { scene } = useGLTF(
    quality === "high"
      ? "/kingdom/island.glb"
      : `/kingdom/island-${quality}.glb`,
  );
  const model = useMemo(() => {
    const clone = scene.clone(true);
    clone.traverse((o) => {
      if (o instanceof Mesh) {
        o.castShadow = true;
        o.receiveShadow = true;
      }
    });
    return clone;
  }, [scene]);
  const gl = useThree((s) => s.gl);
  useEffect(() => {
    gl.shadowMap.needsUpdate = true;
  }, [gl, model]);
  function hit(e: ThreeEvent<PointerEvent | MouseEvent>) {
    let o: Object3D | null = e.object;
    while (o) {
      const l = landmarks.find((l) => l.id === o!.userData.landmark_id);
      if (l) return l;
      o = o.parent;
    }
    return null;
  }
  return (
    <primitive
      object={model}
      onClick={(e: ThreeEvent<MouseEvent>) => {
        const l = hit(e);
        if (l) {
          e.stopPropagation();
          onSelect(l);
        }
      }}
      onPointerMove={(e: ThreeEvent<PointerEvent>) => {
        const l = hit(e);
        onHover(l);
        document.body.style.cursor = l ? "pointer" : "auto";
      }}
      onPointerOut={() => {
        onHover(null);
        document.body.style.cursor = "auto";
      }}
    />
  );
}
function Villagers({
  citizens,
  selectedId,
  reduced,
  connected,
  onSelect,
  positions,
}: {
  citizens: Citizen[];
  selectedId: string | null;
  reduced: boolean;
  connected: boolean;
  onSelect: (c: Citizen) => void;
  positions: React.RefObject<Map<string, Vector3>>;
}) {
  const { scene } = useGLTF("/kingdom/citizen.glb");
  const parts = useMemo(() => {
    scene.updateMatrixWorld(true);
    const result: {
      name: string;
      geometry: any;
      material: any;
      matrix: Matrix4;
      colored: boolean;
    }[] = [];
    scene.traverse((o) => {
      if (o instanceof Mesh) {
        const colored = ["Tunic", "Hat", "ArmLeft", "ArmRight"].includes(
          o.name,
        );
        const material = colored
          ? (o.material as MeshStandardMaterial).clone()
          : o.material;
        if (colored) (material as MeshStandardMaterial).color.set("white");
        result.push({
          name: o.name,
          geometry: o.geometry,
          material,
          matrix: o.matrixWorld.clone(),
          colored,
        });
      }
    });
    return result;
  }, [scene]);
  const instances = useRef(new Map<string, InstancedMesh>()),
    markers = useRef<InstancedMesh>(null),
    mail = useRef<InstancedMesh>(null);
  const journeys = useRef(
    new Map<
      string,
      {
        position: Vector3;
        path: Point[];
        at: number;
        target: string;
        angle: number;
      }
    >(),
  );
  useEffect(() => {
    for (const c of citizens) {
      let j = journeys.current.get(c.id);
      if (!j) {
        j = {
          position: new Vector3(...c.position),
          path: [],
          at: 0,
          target: c.target,
          angle: 0,
        };
        journeys.current.set(c.id, j);
      }
      if (j.target !== c.target) {
        j.path = route([j.position.x, j.position.y, j.position.z], c.position);
        j.at = 1;
        j.target = c.target;
      }
      if (reduced) {
        j.position.set(...c.position);
        j.at = j.path.length;
      }
    }
    for (const part of parts) {
      const mesh = instances.current.get(part.name);
      if (mesh) {
        citizens.forEach((c, i) =>
          mesh.setColorAt(i, new Color(part.colored ? c.palette : "white")),
        );
        if (mesh.instanceColor) mesh.instanceColor.needsUpdate = true;
      }
    }
  }, [citizens, parts, reduced]);
  useEffect(
    () => () => {
      parts.filter((p) => p.colored).forEach((p) => p.material.dispose());
    },
    [parts],
  );
  const base = useMemo(() => new Matrix4(), []),
    pose = useMemo(() => new Matrix4(), []),
    rotation = useMemo(() => new Matrix4(), []),
    size = useMemo(() => new Matrix4(), []);
  useFrame(({ clock }, delta) => {
    citizens.forEach((c, i) => {
      const j = journeys.current.get(c.id);
      if (!j) return;
      let walking = false;
      if (connected && !reduced && j.at < j.path.length) {
        const to = j.path[j.at];
        const dx = to[0] - j.position.x,
          dz = to[2] - j.position.z,
          dist = Math.hypot(dx, dz);
        if (dist < 0.06) j.at++;
        else {
          const step = Math.min(dist, Math.min(delta, 0.05) * 1.15);
          j.position.x += (dx / dist) * step;
          j.position.z += (dz / dist) * step;
          j.angle = Math.atan2(dx, dz);
          walking = true;
        }
      }
      const t = reduced ? 0 : clock.elapsedTime,
        idle = c.state === "idle",
        drift = idle && !reduced ? Math.sin(t * 0.6 + c.seed) * 0.38 : 0;
      const x = j.position.x + drift,
        z = j.position.z,
        y =
          groundHeight(x, z) + (reduced ? 0 : Math.sin(t * 2 + c.seed) * 0.012);
      positions.current.set(c.id, new Vector3(x, y, z));
      base.makeTranslation(x, y, z);
      rotation.makeRotationY(
        walking ? j.angle : idle ? Math.cos(t * 0.6 + c.seed) * 0.18 : 0,
      );
      base.multiply(rotation);
      for (const part of parts) {
        const mesh = instances.current.get(part.name);
        if (!mesh) continue;
        pose.copy(base).multiply(part.matrix);
        if (/^(Leg|Arm)/.test(part.name)) {
          const left = part.name.endsWith("Left"),
            arms = part.name.startsWith("Arm");
          const gait =
            !reduced && (walking || idle)
              ? Math.sin(t * (walking ? 8 : 3) + (left ? 0 : Math.PI)) *
                (walking ? 0.4 : 0.12)
              : 0;
          const work =
            !reduced && connected && c.working && arms
              ? Math.sin(t * 4 + (left ? 0 : 1)) * 0.25
              : 0;
          rotation.makeRotationX(gait + work);
          pose.multiply(rotation);
        }
        mesh.setMatrixAt(i, pose);
      }
      if (markers.current) {
        pose.makeRotationX(-Math.PI / 2);
        pose.setPosition(x, y + 0.025, z);
        if (!(
          selectedId === c.id ||
          ["quarantined", "blocked", "failed"].includes(c.state)
        ))
          pose.multiply(size.makeScale(0, 0, 0));
        markers.current.setMatrixAt(i, pose);
        markers.current.setColorAt(
          i,
          new Color(
            c.state === "quarantined"
              ? "#b775a3"
              : selectedId === c.id
                ? "#f6c445"
                : "#c17a41",
          ),
        );
      }
      if (mail.current) {
        pose.makeTranslation(x, y + 1.05, z);
        if (c.state !== "waiting_for_approval")
          pose.multiply(size.makeScale(0, 0, 0));
        mail.current.setMatrixAt(i, pose);
      }
    });
    for (const mesh of instances.current.values())
      mesh.instanceMatrix.needsUpdate = true;
    if (markers.current) {
      markers.current.instanceMatrix.needsUpdate = true;
      if (markers.current.instanceColor)
        markers.current.instanceColor.needsUpdate = true;
    }
    if (mail.current) mail.current.instanceMatrix.needsUpdate = true;
  });
  return (
    <group>
      {parts.map((part) => (
        <instancedMesh
          key={part.name}
          args={[part.geometry, part.material, citizens.length]}
          ref={(el) => {
            if (el) instances.current.set(part.name, el);
            else instances.current.delete(part.name);
          }}
          dispose={null}
          frustumCulled={false}
          onClick={(e) => {
            e.stopPropagation();
            if (e.instanceId !== undefined) onSelect(citizens[e.instanceId]);
          }}
          onPointerOver={() => {
            document.body.style.cursor = "pointer";
          }}
          onPointerOut={() => {
            document.body.style.cursor = "auto";
          }}
        />
      ))}
      <instancedMesh
        ref={markers}
        args={[undefined, undefined, citizens.length]}
        frustumCulled={false}
      >
        <ringGeometry args={[0.25, 0.32, 24]} />
        <meshBasicMaterial />
      </instancedMesh>
      <instancedMesh
        ref={mail}
        args={[undefined, undefined, citizens.length]}
        frustumCulled={false}
      >
        <boxGeometry args={[0.17, 0.12, 0.035]} />
        <meshStandardMaterial color="#eac25e" />
      </instancedMesh>
    </group>
  );
}
function Beacon({ severity, reduced }: { severity: string; reduced: boolean }) {
  const light = useRef<Mesh>(null);
  useFrame(({ clock }) => {
    if (light.current)
      light.current.scale.setScalar(
        severity === "critical" && !reduced
          ? 1 + Math.sin(clock.elapsedTime * 1.2) * 0.1
          : 1,
      );
  });
  return (
    <mesh ref={light} position={[-10, 5.42, -2.5]}>
      <sphereGeometry args={[0.36, 20, 16]} />
      <meshBasicMaterial
        color={
          severity === "critical"
            ? "#cc554b"
            : severity === "advisory"
              ? "#f4b44b"
              : "#ffdf9b"
        }
      />
    </mesh>
  );
}
function CameraRig({
  preset,
  reset,
  follow,
  positions,
  zoomDelta,
  labelRefs,
  citizens,
  reduced,
  onReady,
  focus,
}: {
  preset: number;
  reset: number;
  follow: string | null;
  positions: React.RefObject<Map<string, Vector3>>;
  zoomDelta: number;
  labelRefs: React.RefObject<Map<string, HTMLButtonElement>>;
  citizens: Citizen[];
  reduced: boolean;
  onReady: () => void;
  focus: boolean;
}) {
  const controls = useThree((s) => s.controls) as any;
  const { camera, size, gl, scene } = useThree();
  const destination = useRef<Vector3 | null>(null),
    target = useRef(new Vector3()),
    zoom = useRef(25),
    metrics = useRef({ frames: 0, time: 0 });
  useEffect(() => {
    const p = presets[preset];
    destination.current = new Vector3(p.camera[0], p.camera[1], p.camera[2]);
    target.current.set(p.target[0], p.target[1], p.target[2]);
    const availableWidth =
      size.width > 1100
        ? size.width - (focus ? 0 : 530)
        : size.width > 760
          ? size.width - (focus ? 0 : 440)
          : size.width;
    zoom.current = Math.min(p.zoom, availableWidth / (preset === 0 ? 30 : 18));
  }, [preset, reset, size.width, focus]);
  useEffect(() => {
    const offset =
      size.width > 1100 && !focus ? 64 : size.width > 760 && !focus ? 30 : 0;
    if ("setViewOffset" in camera)
      (camera as any).setViewOffset(
        size.width,
        size.height,
        offset,
        0,
        size.width,
        size.height,
      );
    camera.updateProjectionMatrix();
  }, [camera, size.width, size.height, focus]);
  useEffect(() => {
    zoom.current = Math.min(75, Math.max(7, zoom.current + zoomDelta));
  }, [zoomDelta]);
  useEffect(() => {
    gl.shadowMap.needsUpdate = true;
    onReady();
  }, [onReady]);
  useFrame((_, delta) => {
    if (!controls) return;
    if (follow && positions.current.has(follow)) {
      target.current.copy(positions.current.get(follow)!);
      controls.target.lerp(target.current, 0.05);
    } else if (destination.current) {
      camera.position.lerp(destination.current, reduced ? 1 : 0.075);
      controls.target.lerp(target.current, reduced ? 1 : 0.075);
      camera.zoom += (zoom.current - camera.zoom) * (reduced ? 1 : 0.075);
      camera.updateProjectionMatrix();
      if (
        camera.position.distanceTo(destination.current) < 0.03 &&
        Math.abs(camera.zoom - zoom.current) < 0.05
      )
        destination.current = null;
    }
    controls.target.x = Math.max(-13, Math.min(13, controls.target.x));
    controls.target.z = Math.max(-9, Math.min(10, controls.target.z));
    controls.update();
    for (const l of landmarks) {
      const el = labelRefs.current.get(l.id);
      if (!el) continue;
      const p = new Vector3(
        l.position[0],
        l.position[1] +
          (l.id === "lighthouse" ? 5.1 : l.id === "keep" ? 4.7 : 3),
        l.position[2],
      ).project(camera);
      el.style.transform = `translate(-50%, -100%) translate(${(p.x * 0.5 + 0.5) * size.width}px,${(-p.y * 0.5 + 0.5) * size.height}px)`;
      el.style.visibility =
        p.z < 1 && p.x > -1 && p.x < 1 && p.y > -1 && p.y < 1
          ? "visible"
          : "hidden";
    }
    metrics.current.frames++;
    metrics.current.time += delta;
    if (metrics.current.time >= 1) {
      (window as any).__kingdomDiagnostics = {
        fps: Number((metrics.current.frames / metrics.current.time).toFixed(1)),
        drawCalls: gl.info.render.calls,
        triangles: gl.info.render.triangles,
        citizens: citizens.length,
        worldVersion: WORLD_VERSION,
        meshes: scene.children.length,
      };
      metrics.current = { frames: 0, time: 0 };
    }
  });
  return null;
}
function ContextMonitor({ onFailure }: { onFailure: () => void }) {
  const gl = useThree((s) => s.gl);
  useEffect(() => {
    const canvas = gl.domElement;
    const lost = () => {
      if (canvas.isConnected) onFailure();
    };
    canvas.addEventListener("webglcontextlost", lost);
    return () => canvas.removeEventListener("webglcontextlost", lost);
  }, [gl, onFailure]);
  return null;
}
class WorldBoundary extends Component<
  { children: ReactNode; onFailure: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onFailure();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}
export default function Kingdom({
  snapshot,
  connected,
  onVisit,
}: {
  snapshot: Snapshot;
  connected: boolean;
  onVisit: (page: string) => void;
}) {
  const [selected, setSelected] = useState<Landmark | null>(null),
    [selectedId, setSelectedId] = useState<string | null>(null),
    [hover, setHover] = useState<Landmark | null>(null),
    [preset, setPreset] = useState(0),
    [reset, setReset] = useState(0),
    [follow, setFollow] = useState<string | null>(null),
    [quality, setQuality] = useState<Quality>("balanced"),
    [reduced, setReduced] = useState(false),
    [flat, setFlat] = useState(false),
    [ready, setReady] = useState(false),
    [zoom, setZoom] = useState(0),
    [labels, setLabels] = useState(true),
    [failed, setFailed] = useState(false),
    [query, setQuery] = useState(""),
    [directoryOpen, setDirectoryOpen] = useState(false),
    [panelOpen, setPanelOpen] = useState(false),
    [focusIsland, setFocusIsland] = useState(false),
    [displayOpen, setDisplayOpen] = useState(false),
    [measuring, setMeasuring] = useState(false),
    [performanceReport, setPerformanceReport] =
      useState<BrowserPerformanceReport | null>(null),
    [performanceError, setPerformanceError] = useState("");
  const rendererRef = useRef<WebGLRenderer | null>(null);
  const measurement = useRef<AbortController | null>(null);
  const reportReady = useCallback(() => setReady(true), [quality]);
  useEffect(() => {
    setPerformanceReport(null);
    setPerformanceError("");
    setMeasuring(false);
    return () => measurement.current?.abort();
  }, [
    quality,
    reduced,
    flat,
    failed,
    preset,
    reset,
    follow,
    zoom,
    focusIsland,
  ]);
  async function measurePerformance() {
    const renderer = rendererRef.current;
    if (
      !renderer ||
      measurement.current ||
      measuring ||
      reduced ||
      flat ||
      failed ||
      !ready
    )
      return;
    const controller = new AbortController();
    measurement.current = controller;
    setMeasuring(true);
    setPerformanceError("");
    setPerformanceReport(null);
    try {
      const context = renderer.getContext();
      const debug = context.getExtension("WEBGL_debug_renderer_info");
      const rendererName = String(
        context.getParameter(
          debug ? debug.UNMASKED_RENDERER_WEBGL : context.RENDERER,
        ),
      );
      const report = await sampleSceneFrames(() => {
        if (context.isContextLost() || !renderer.domElement.isConnected)
          throw new Error("The 3D renderer is unavailable");
        return {
          frames: renderer.info.render.frame,
          width: renderer.domElement.width,
          height: renderer.domElement.height,
        };
      }, controller.signal);
      setPerformanceReport({
        schema_version: 1,
        captured_at: new Date().toISOString(),
        world_version: WORLD_VERSION,
        quality,
        citizens: citizens.length,
        renderer: rendererName,
        ...report,
        scope:
          "Foreground browser sample; scene frame counts and browser pacing, not GPU timings or hardware certification. No task content, identities or credentials included.",
      });
    } catch (error) {
      if (!controller.signal.aborted)
        setPerformanceError((error as Error).message);
    } finally {
      if (measurement.current === controller) measurement.current = null;
      if (!controller.signal.aborted) setMeasuring(false);
    }
  }
  function downloadPerformanceReport() {
    if (!performanceReport) return;
    const url = URL.createObjectURL(
      new Blob([JSON.stringify(performanceReport, null, 2)], {
        type: "application/json",
      }),
    );
    const link = document.createElement("a");
    link.href = url;
    link.download = "kingdom-performance.json";
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  useEffect(() => {
    const escape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setQuery("");
        setDirectoryOpen(false);
        setDisplayOpen(false);
        setFocusIsland(false);
        setPanelOpen(false);
        setSelected(null);
        setSelectedId(null);
      }
    };
    window.addEventListener("keydown", escape);
    return () => window.removeEventListener("keydown", escape);
  }, []);
  useEffect(() => {
    (window as any).__kingdomDiagnostics = undefined;
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    setReduced(media.matches);
    if (window.matchMedia("(max-width: 680px)").matches) setQuality("low");
    const change = () => setReduced(media.matches);
    media.addEventListener("change", change);
    return () => media.removeEventListener("change", change);
  }, []);
  useEffect(() => {
    document.body.style.cursor = "auto";
    return () => {
      document.body.style.cursor = "auto";
    };
  }, []);
  const citizens = useMemo(
    () => snapshot.roles.map((r) => citizen(r, snapshot)),
    [snapshot],
  );
  const selectedCitizen = citizens.find((c) => c.id === selectedId);
  const beacon = lighthouseState(snapshot),
    labelRefs = useRef(new Map<string, HTMLButtonElement>()),
    positions = useRef(new Map<string, Vector3>());
  const openMail = snapshot.messages.filter((m) => m.state === "open").length;
  const choose = (l: Landmark) => {
    setSelected(l);
    setPanelOpen(true);
    setFocusIsland(false);
    setDirectoryOpen(false);
    setQuery("");
    setSelectedId(null);
    setFollow(null);
  };
  const chooseCitizen = (c: Citizen) => {
    setSelectedId(c.id);
    setFocusIsland(false);
    setPanelOpen(true);
    setQuery("");
    setSelected(null);
  };
  const linkedTasks = selected
    ? snapshot.tasks.filter((t) =>
        snapshot.roles.some(
          (r) =>
            r.key === t.agent_role && citizen(r, snapshot).home === selected.id,
        ),
      )
    : [];
  return (
    <section
      className={"kingdom-edition " + (focusIsland ? "island-focus" : "")}
      aria-label="Kingdom Edition"
      data-world-rendered={ready && !failed && !flat}
    >
      <div className="kingdom-search">
        <Search size={16} />
        <input
          type="search"
          aria-label="Search kingdom"
          placeholder="Search your kingdom"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && query.trim()) {
              const l = landmarks.find((l) =>
                (l.name + " " + l.subtitle)
                  .toLowerCase()
                  .includes(query.trim().toLowerCase()),
              );
              if (l) choose(l);
              else {
                const c = citizens.find((c) =>
                  c.role.config.role
                    .toLowerCase()
                    .includes(query.trim().toLowerCase()),
                );
                if (c) chooseCitizen(c);
              }
            }
          }}
        />
        <kbd>↵</kbd>
        {query.trim() && (
          <div
            className="kingdom-search-results"
            aria-label="Kingdom search results"
          >
            <span>LANDMARKS & CITIZENS</span>
            {landmarks
              .filter((l) =>
                (l.name + " " + l.subtitle)
                  .toLowerCase()
                  .includes(query.trim().toLowerCase()),
              )
              .map((l) => (
                <button key={l.id} onClick={() => choose(l)}>
                  <Castle size={16} />
                  <span>
                    {l.name}
                    <small>{l.subtitle}</small>
                  </span>
                  <b>↗</b>
                </button>
              ))}
            {citizens
              .filter((c) =>
                c.role.config.role
                  .toLowerCase()
                  .includes(query.trim().toLowerCase()),
              )
              .map((c) => (
                <button key={c.id} onClick={() => chooseCitizen(c)}>
                  <i style={{ background: c.palette }} />
                  <span>
                    {c.role.config.role}
                    <small>{c.state.replaceAll("_", " ")}</small>
                  </span>
                  <b>↗</b>
                </button>
              ))}
            {![
              ...landmarks.map((l) => l.name + " " + l.subtitle),
              ...citizens.map((c) => c.role.config.role),
            ].some((s) =>
              s.toLowerCase().includes(query.trim().toLowerCase()),
            ) && <p>No landmarks or citizens found.</p>}
          </div>
        )}
      </div>
      <div className="kingdom-titlebar">
        <div>
          <span className="kingdom-kicker">
            <Crown size={14} /> AI COMPANY OS · KINGDOM EDITION
          </span>
          <h1 aria-label="Kingdom">
            Your kingdom.<em> In good hands.</em>
          </h1>
        </div>
        <div className="kingdom-health">
          <i className={connected ? "live-dot" : "idle-dot"} />
          {connected ? "Live kingdom" : "Connection lost · last known state"}
        </div>
      </div>
      <div className="kingdom-hud" aria-label="Kingdom operational metrics">
        <div>
          <span>Quests running / waiting</span>
          <b>
            {snapshot.kpis.jobs_running} / {snapshot.kpis.jobs_waiting}
          </b>
        </div>
        <div>
          <span>Treasury · available budget</span>
          <b>{money(snapshot.kpis.available_budget, snapshot.kpis.currency)}</b>
        </div>
        <div>
          <span>Products published</span>
          <b>
            {
              (snapshot.products || []).filter((p) => p.data.published === true)
                .length
            }
          </b>
        </div>
        <div>
          <span>Verified revenue ledger</span>
          <b>{snapshot.revenue.filter((r) => r.verified).length} entries</b>
        </div>
        <div>
          <span>Net contribution</span>
          <b>Not measured</b>
        </div>
      </div>
      <div className="kingdom-layout">
        <div className="kingdom-stage">
          <div className="kingdom-toolbar">
            <label className="sr-only" htmlFor="kingdom-camera">
              Kingdom camera preset
            </label>
            <select
              id="kingdom-camera"
              value={preset}
              onChange={(e) => {
                setPreset(Number(e.target.value));
                setFollow(null);
              }}
            >
              {presets.map((p, i) => (
                <option key={p.name} value={i}>
                  {p.name}
                </option>
              ))}
            </select>
            <button
              aria-label="Reset kingdom camera"
              onClick={() => {
                setPreset(0);
                setReset(reset + 1);
                setFollow(null);
              }}
            >
              <RotateCcw size={15} />
            </button>
            <button
              aria-label="Zoom into kingdom"
              onClick={() => {
                setZoom(zoom + 4);
                setReset(reset + 1);
              }}
            >
              <ZoomIn size={15} />
            </button>
            <button
              aria-label="Zoom out of kingdom"
              onClick={() => {
                setZoom(zoom - 4);
                setReset(reset + 1);
              }}
            >
              <ZoomOut size={15} />
            </button>
            <button
              aria-label="Toggle landmark directory"
              aria-pressed={directoryOpen}
              onClick={() => setDirectoryOpen(!directoryOpen)}
            >
              <Castle size={15} />
              <span>Buildings</span>
            </button>
            <button
              aria-pressed={focusIsland}
              aria-label={focusIsland ? "Exit island focus" : "Focus on island"}
              onClick={() => {
                setFocusIsland(!focusIsland);
                setDirectoryOpen(false);
              }}
            >
              <Maximize2 size={15} />
              <span>{focusIsland ? "Exit focus" : "Focus"}</span>
            </button>
            <button
              aria-label="Display settings"
              aria-expanded={displayOpen}
              onClick={() => setDisplayOpen(!displayOpen)}
            >
              <SlidersHorizontal size={15} />
              <span>Display</span>
            </button>
            <button
              aria-pressed={flat}
              onClick={() => {
                setReady(false);
                setFlat(!flat);
              }}
            >
              <MapIcon size={15} />
              {flat ? "3D kingdom" : "Accessible view"}
            </button>
            <button aria-pressed={labels} onClick={() => setLabels(!labels)}>
              Labels
            </button>
          </div>
          <div
            className="kingdom-world"
            role="region"
            aria-label="Interactive island kingdom"
          >
            {!flat && !failed ? (
              <>
                <WorldBoundary onFailure={() => setFailed(true)}>
                  <Canvas
                    orthographic
                    frameloop={reduced ? "demand" : "always"}
                    shadows={quality !== "low"}
                    dpr={
                      quality === "high"
                        ? [1, 1.75]
                        : quality === "low"
                          ? 1
                          : [1, 1.25]
                    }
                    camera={{
                      position: [24, 25, 30],
                      zoom: 31,
                      near: 0.1,
                      far: 250,
                    }}
                    gl={{
                      antialias: quality !== "low",
                      alpha: false,
                      powerPreference: "high-performance",
                    }}
                    onCreated={({ gl }) => {
                      rendererRef.current = gl;
                      gl.setClearColor("#74bdc5");
                      gl.shadowMap.autoUpdate = false;
                    }}
                  >
                    <ContextMonitor onFailure={() => setFailed(true)} />
                    <ambientLight intensity={0.7} />
                    <hemisphereLight args={["#fff4d9", "#4a817c", 0.8]} />
                    <directionalLight
                      position={[-10, 24, 12]}
                      intensity={2.5}
                      color="#fff0d4"
                      castShadow={quality !== "low"}
                      shadow-mapSize={[
                        quality === "high" ? 2048 : 1024,
                        quality === "high" ? 2048 : 1024,
                      ]}
                      shadow-camera-left={-23}
                      shadow-camera-right={23}
                      shadow-camera-top={22}
                      shadow-camera-bottom={-22}
                      shadow-normalBias={0.06}
                    />
                    <Water reduced={reduced} />
                    {selected && (
                      <mesh
                        position={[
                          selected.position[0],
                          groundHeight(
                            selected.position[0],
                            selected.position[2],
                          ) + 0.06,
                          selected.position[2],
                        ]}
                        rotation={[-Math.PI / 2, 0, 0]}
                      >
                        <ringGeometry args={[1.7, 1.77, 64]} />
                        <meshBasicMaterial
                          color="#f6c445"
                          transparent
                          opacity={0.75}
                        />
                      </mesh>
                    )}
                    <Suspense fallback={null}>
                      <Island
                        onSelect={choose}
                        onHover={setHover}
                        quality={quality}
                      />
                      <Villagers
                        citizens={citizens}
                        selectedId={selectedId}
                        reduced={reduced}
                        connected={connected}
                        onSelect={chooseCitizen}
                        positions={positions}
                      />
                      <Beacon severity={beacon.severity} reduced={reduced} />
                      <CameraRig
                        preset={preset}
                        reset={reset}
                        follow={follow}
                        positions={positions}
                        zoomDelta={zoom}
                        labelRefs={labelRefs}
                        citizens={citizens}
                        reduced={reduced}
                        focus={focusIsland}
                        onReady={reportReady}
                      />
                    </Suspense>
                    <OrbitControls
                      makeDefault
                      target={[0, 0, 0]}
                      enableDamping
                      dampingFactor={0.08}
                      minZoom={7}
                      maxZoom={75}
                      maxPolarAngle={Math.PI * 0.43}
                      minPolarAngle={Math.PI * 0.15}
                      minDistance={10}
                      maxDistance={80}
                      onStart={() => {
                        setFollow(null);
                        if (measuring) {
                          measurement.current?.abort();
                          setMeasuring(false);
                          setPerformanceError(
                            "Camera moved. Start a new measurement.",
                          );
                        }
                      }}
                    />
                  </Canvas>
                </WorldBoundary>
                <div className={"kingdom-labels " + (!labels ? "hidden" : "")}>
                  {landmarks.map((l) => (
                    <button
                      key={l.id}
                      ref={(el) => {
                        if (el) labelRefs.current.set(l.id, el);
                        else labelRefs.current.delete(l.id);
                      }}
                      className={
                        "kingdom-map-label " +
                        (preset === 0 &&
                        ![
                          "keep",
                          "guild",
                          "lighthouse",
                          "market",
                          "post",
                        ].includes(l.id) &&
                        selected?.id !== l.id &&
                        hover?.id !== l.id
                          ? "detail-hidden "
                          : "") +
                        (selected?.id === l.id ? "chosen" : "") +
                        (hover?.id === l.id ? " hovered" : "")
                      }
                      data-landmark={l.id}
                      onClick={() => choose(l)}
                      onDoubleClick={() => {
                        setPreset(
                          l.id === "keep"
                            ? 1
                            : l.id === "lighthouse"
                              ? 5
                              : l.id === "market" || l.id === "shipyard"
                                ? 4
                                : l.id === "workshop" ||
                                    l.id === "alchemy" ||
                                    l.id === "atelier"
                                  ? 3
                                  : 2,
                        );
                        setReset(reset + 1);
                      }}
                    >
                      <span>
                        {l.id === "keep"
                          ? "♛"
                          : l.id === "lighthouse"
                            ? "◈"
                            : l.id === "post"
                              ? "✉"
                              : "◆"}
                      </span>
                      {l.name}
                      {l.id === "lighthouse" && beacon.count > 0 && (
                        <b>{beacon.count}</b>
                      )}
                      {l.id === "post" && openMail > 0 && <b>{openMail}</b>}
                    </button>
                  ))}
                </div>
                {!ready && (
                  <div className="kingdom-loading">Charting the island…</div>
                )}
              </>
            ) : (
              <div className="kingdom-flat">
                <h3>
                  {failed
                    ? "3D unavailable · operational map"
                    : "Your kingdom, at a glance"}
                </h3>
                <p>
                  Every landmark opens the same authenticated operational
                  system.
                </p>
                <div>
                  {landmarks.map((l) => (
                    <button key={l.id} onClick={() => choose(l)}>
                      <Castle size={22} />
                      <b>{l.name}</b>
                      <small>{l.subtitle}</small>
                    </button>
                  ))}
                </div>
              </div>
            )}
            {!flat && !failed && (
              <>
                <div className="kingdom-seal">
                  <span>EST. 2026</span>
                  <b>THE SOVEREIGN ISLES</b>
                  <small>One founder. A world of possibility.</small>
                </div>
                <div className="kingdom-compass">
                  <Compass size={33} />
                  <small>N</small>
                </div>
                <div className="kingdom-world-caption">
                  Drag to orbit · right-drag to pan · scroll to zoom
                  <br />
                  <span>
                    Footsteps are cosmetic. Work status comes from the server.
                  </span>
                </div>
              </>
            )}
          </div>
          <div
            className={
              "kingdom-controls " + (displayOpen ? "display-open" : "")
            }
          >
            <label>
              Render quality{" "}
              <select
                aria-label="Kingdom render quality"
                value={quality}
                onChange={(e) => {
                  if (e.target.value !== quality) {
                    setReady(false);
                    setQuality(e.target.value as Quality);
                  }
                }}
              >
                <option value="low">Low</option>
                <option value="balanced">Balanced</option>
                <option value="high">High</option>
              </select>
            </label>
            <label>
              <input
                type="checkbox"
                checked={reduced}
                onChange={(e) => setReduced(e.target.checked)}
              />{" "}
              Reduced motion
            </label>
            <span>
              {citizens.length} persistent citizens ·{" "}
              {citizens.filter((c) => c.working).length} working
            </span>
            <div
              className="kingdom-performance"
              aria-label="Performance diagnostics"
            >
              <button
                className="secondary"
                onClick={measurePerformance}
                disabled={measuring || reduced || flat || failed || !ready}
              >
                {measuring
                  ? "Measuring… keep this tab visible"
                  : "Measure performance (10s)"}
              </button>
              {reduced && (
                <p>Turn off Reduced motion to measure scene frames.</p>
              )}
              {measuring && (
                <button
                  onClick={() => {
                    measurement.current?.abort();
                    setMeasuring(false);
                  }}
                >
                  Cancel measurement
                </button>
              )}
              {performanceError && <p role="alert">{performanceError}</p>}
              {performanceReport && (
                <>
                  <p role="status">
                    {performanceReport.scene_fps.toFixed(1)} scene FPS ·{" "}
                    {performanceReport.scene_frames} rendered frames
                  </p>
                  <p>Browser pacing only. Not a GPU benchmark.</p>
                  <button
                    className="secondary"
                    onClick={downloadPerformanceReport}
                  >
                    Download performance report
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
        <aside
          className={"kingdom-inspector " + (panelOpen ? "panel-open" : "")}
          aria-label="Kingdom inspector"
        >
          <button
            className="kingdom-panel-close"
            aria-label="Close kingdom panel"
            onClick={() => setPanelOpen(false)}
          >
            <PanelRightClose size={17} />
          </button>
          {selectedCitizen ? (
            <>
              <div className="kingdom-inspector-heading">
                <span>CITIZEN PASSPORT</span>
                <button
                  aria-label="Close citizen inspector"
                  onClick={() => {
                    setSelectedId(null);
                    setFollow(null);
                  }}
                >
                  <X size={16} />
                </button>
              </div>
              <div
                className="citizen-portrait"
                style={{
                  background: selectedCitizen.palette + "22",
                  color: selectedCitizen.palette,
                }}
              >
                <span>♟</span>
              </div>
              <h3>{selectedCitizen.role.config.role}</h3>
              <p className="kingdom-state">
                {selectedCitizen.state.replaceAll("_", " ")}
                {!connected ? " · last known" : ""}
              </p>
              <p>{selectedCitizen.role.config.mission}</p>
              <dl>
                <dt>Home guild</dt>
                <dd>{landmark(selectedCitizen.home).name}</dd>
                <dt>Destination</dt>
                <dd>{landmark(selectedCitizen.target).name}</dd>
                <dt>Citizen identity</dt>
                <dd className="kingdom-mono">{selectedCitizen.id}</dd>
                <dt>Linked quest</dt>
                <dd>{selectedCitizen.task?.title || "No current quest"}</dd>
                <dt>Execution evidence</dt>
                <dd>
                  {selectedCitizen.run
                    ? `${selectedCitizen.run.provider} · ${selectedCitizen.run.status}`
                    : "No run in current snapshot"}
                </dd>
                <dt>Last server evidence</dt>
                <dd>
                  {selectedCitizen.lastServerEventAt ||
                    "No execution event recorded"}
                </dd>
                <dt>Run ceiling</dt>
                <dd>{money(selectedCitizen.role.config.max_cost.amount)}</dd>
              </dl>
              {selectedCitizen.task?.error && (
                <p className="form-error">{selectedCitizen.task.error}</p>
              )}
              <div className="kingdom-inspector-actions">
                <button
                  onClick={() => {
                    setFollow(selectedCitizen.id);
                    setPreset(2);
                    setReset(reset + 1);
                  }}
                >
                  <Eye size={14} /> Follow citizen
                </button>
                <button onClick={() => onVisit("Build Inspector")}>
                  Run logs & artifacts ↗
                </button>
                <button onClick={() => onVisit("Tasks")}>
                  Quest & checkpoints ↗
                </button>
              </div>
              <small>
                Configured identity persists independently of worker processes.
                No active run means no claimed work.
              </small>
            </>
          ) : selected ? (
            <>
              <div className="kingdom-inspector-heading">
                <span>LANDMARK INSPECTOR</span>
                <button
                  aria-label="Close landmark inspector"
                  onClick={() => setSelected(null)}
                >
                  <X size={16} />
                </button>
              </div>
              <div className="landmark-crest" style={{ color: selected.color }}>
                {selected.id === "lighthouse" ? (
                  <Shield size={33} />
                ) : selected.id === "market" || selected.id === "shipyard" ? (
                  <Anchor size={33} />
                ) : selected.id === "post" ? (
                  <Mail size={33} />
                ) : (
                  <Castle size={33} />
                )}
              </div>
              <h3>{selected.name}</h3>
              <p>{selected.subtitle}</p>
              {selected.id === "lighthouse" ? (
                <>
                  <p className={"beacon-status " + beacon.severity}>
                    {beacon.severity.toUpperCase()} · {beacon.count} open
                    incidents
                  </p>
                  <p>
                    Independent monitor: {beacon.monitor}. Beacon color reflects
                    actual open incident severity.
                  </p>
                  {snapshot.incidents
                    .filter((i) => i.state === "open")
                    .slice(0, 3)
                    .map((i) => (
                      <p key={i.id}>
                        {i.severity}: {i.kind}
                      </p>
                    ))}
                </>
              ) : selected.id === "treasury" ? (
                <dl>
                  <dt>Real monthly cost</dt>
                  <dd>
                    {money(snapshot.kpis.monthly_spend, snapshot.kpis.currency)}
                  </dd>
                  <dt>Reserved</dt>
                  <dd>
                    {money(snapshot.kpis.reserved, snapshot.kpis.currency)}
                  </dd>
                  <dt>Budget remaining</dt>
                  <dd>
                    {money(
                      snapshot.kpis.available_budget,
                      snapshot.kpis.currency,
                    )}
                  </dd>
                </dl>
              ) : selected.id === "post" ? (
                <>
                  <p>
                    {openMail} open messages · {snapshot.kpis.approvals_needed}{" "}
                    approvals
                  </p>
                  <p>Email channel: {snapshot.integrations.email}</p>
                </>
              ) : selected.id === "market" ? (
                <>
                  <p>
                    {snapshot.opportunities.length} research opportunities ·{" "}
                    {(snapshot.products || []).length} product hypotheses
                  </p>
                  <p>
                    {snapshot.revenue.length} verified ledger records.
                    Hypotheses are not sales.
                  </p>
                </>
              ) : (
                <>
                  <p>{linkedTasks.length} linked quests</p>
                  {linkedTasks.slice(0, 3).map((t) => (
                    <p key={t.id}>
                      <b>{t.title}</b>
                      <br />
                      {t.status.replaceAll("_", " ")}
                    </p>
                  ))}
                </>
              )}
              <button
                className="kingdom-primary"
                onClick={() => onVisit(selected.page)}
              >
                Open {selected.page} ↗
              </button>
              {selected.id === "keep" && (
                <>
                  <button onClick={() => onVisit("Settings")}>
                    Company mode & STOP ALL ↗
                  </button>
                  <button onClick={() => onVisit("Approvals")}>
                    Review royal decisions ↗
                  </button>
                </>
              )}
              <small>
                This is a live view of existing company records. All protected
                actions retain server authorization.
              </small>
            </>
          ) : (
            <>
              <div className="kingdom-inspector-heading">
                <span>
                  <Crown size={16} /> Kingdom overview
                </span>
                <small>{connected ? "Live" : "Offline"}</small>
              </div>
              <div className="kingdom-overview-grid">
                <button onClick={() => onVisit("Agents")}>
                  <i className="blue">
                    <Eye size={19} />
                  </i>
                  <span>
                    Active citizens
                    <strong>
                      {snapshot.kpis.active_agents}
                      <small> / {citizens.length}</small>
                    </strong>
                  </span>
                </button>
                <button onClick={() => onVisit("Tasks")}>
                  <i className="purple">
                    <Flag size={19} />
                  </i>
                  <span>
                    Running quests<strong>{snapshot.kpis.jobs_running}</strong>
                  </span>
                </button>
                <button onClick={() => onVisit("Finance")}>
                  <i className="green">
                    <Anchor size={19} />
                  </i>
                  <span>
                    Monthly cost
                    <strong>
                      {money(
                        snapshot.kpis.monthly_spend,
                        snapshot.kpis.currency,
                      )}
                    </strong>
                  </span>
                </button>
                <button onClick={() => onVisit("Watchtower")}>
                  <i className="orange">
                    <Shield size={19} />
                  </i>
                  <span>
                    Watchtower alerts<strong>{beacon.count}</strong>
                  </span>
                </button>
              </div>
              <div className="kingdom-status-line">
                <i className={connected ? "live-dot" : "idle-dot"} />
                {snapshot.organization.mode.replaceAll("_", " ")}
                <span>
                  {snapshot.organization.paid_execution_authorized
                    ? "Bounded execution"
                    : "Paid execution off"}
                </span>
              </div>
              <div className="kingdom-activity">
                <header>
                  <h3>Live activity</h3>
                  <button onClick={() => onVisit("Audit")}>View all ↗</button>
                </header>
                {snapshot.events.length ? (
                  kingdomActivity(snapshot.events).map(
                    ({ event: e, label, count }) => (
                      <button
                        key={e.id || e.event_id}
                        onClick={() => onVisit("Audit")}
                      >
                        <i />
                        <span>
                          <b>
                            {label}
                            {count > 1 && (
                              <em className="kingdom-event-count">
                                {count} events
                              </em>
                            )}
                          </b>
                          <small>
                            {new Date(
                              e.occurred_at || e.created_at,
                            ).toLocaleTimeString("en", {
                              hour: "2-digit",
                              minute: "2-digit",
                              timeZone: "Asia/Bangkok",
                            })}{" "}
                            · Recorded event
                          </small>
                        </span>
                      </button>
                    ),
                  )
                ) : (
                  <p>No events recorded yet.</p>
                )}
              </div>
              <div className="kingdom-quick-actions">
                <button onClick={() => onVisit("Founder Inbox")}>
                  <Mail size={15} /> Royal inbox <b>{openMail}</b>
                </button>
                <button onClick={() => onVisit("Approvals")}>
                  <Crown size={15} /> Decisions{" "}
                  <b>{snapshot.kpis.approvals_needed}</b>
                </button>
              </div>
            </>
          )}
          <div className="kingdom-citizens">
            <h4>
              Citizens of the realm <span>{citizens.length}</span>
            </h4>
            <div>
              {citizens.map((c) => (
                <button
                  key={c.id}
                  data-citizen={c.role.key}
                  className={selectedId === c.id ? "selected" : ""}
                  onClick={() => chooseCitizen(c)}
                >
                  <i style={{ background: c.palette }} />
                  <span>
                    {c.role.config.role}
                    <small>{c.state.replaceAll("_", " ")}</small>
                  </span>
                  <b>›</b>
                </button>
              ))}
            </div>
          </div>
        </aside>
      </div>
      <button
        className="kingdom-panel-toggle"
        onClick={() => {
          if (!panelOpen) {
            setSelected(null);
            setSelectedId(null);
          }
          setPanelOpen(!panelOpen);
        }}
        aria-expanded={panelOpen}
      >
        <Crown size={16} />
        {panelOpen ? "Close overview" : "Overview"}
      </button>
      <nav
        className={
          "kingdom-destinations " + (directoryOpen ? "directory-open" : "")
        }
        aria-label="Kingdom landmarks"
      >
        {landmarks.map((l) => (
          <button key={l.id} onClick={() => choose(l)}>
            {l.name}
            <span>{l.subtitle}</span>
          </button>
        ))}
      </nav>
    </section>
  );
}
