export type FramePoint = {
  time: number;
  frames: number;
  width: number;
  height: number;
  visible: boolean;
};

// Browser frame pacing and actual Three render counts, never GPU timer claims.
export function summarizeFrameWindow(points: FramePoint[], durationMs: number) {
  if (points.length < 2) throw new Error("Incomplete measurement");
  const first = points[0],
    last = points[points.length - 1];
  if (
    points.some(
      (p, i) =>
        !p.visible ||
        p.width !== first.width ||
        p.height !== first.height ||
        p.width <= 0 ||
        p.height <= 0 ||
        !Number.isFinite(p.time) ||
        !Number.isInteger(p.frames) ||
        p.frames < 0 ||
        (i > 0 &&
          (p.time <= points[i - 1].time || p.frames < points[i - 1].frames)),
    )
  )
    throw new Error(
      "Measurement interrupted by visibility, resize or renderer change",
    );
  const elapsed = last.time - first.time;
  if (elapsed < durationMs) throw new Error("Incomplete measurement");
  const frames = last.frames - first.frames;
  if (!frames) throw new Error("The scene did not render any frames");
  const intervals = points
    .slice(1)
    .map((p, i) => p.time - points[i].time)
    .sort((a, b) => a - b);
  return {
    duration_ms: elapsed,
    scene_frames: frames,
    scene_fps: (frames * 1000) / elapsed,
    browser_raf_fps: ((points.length - 1) * 1000) / elapsed,
    median_browser_frame_ms: intervals[Math.floor(intervals.length / 2)],
    p95_browser_frame_ms:
      intervals[
        Math.min(intervals.length - 1, Math.floor(intervals.length * 0.95))
      ],
    canvas_pixels: [first.width, first.height],
  };
}

export function sampleSceneFrames(
  read: () => Omit<FramePoint, "time" | "visible">,
  signal: AbortSignal,
  durationMs = 10000,
) {
  return new Promise<ReturnType<typeof summarizeFrameWindow>>(
    (resolve, reject) => {
      let handle = 0;
      const points: FramePoint[] = [];
      const cleanup = () => {
        cancelAnimationFrame(handle);
        signal.removeEventListener("abort", aborted);
        document.removeEventListener("visibilitychange", visibility);
      };
      const fail = (error: unknown) => {
        cleanup();
        reject(error);
      };
      const aborted = () =>
        fail(new DOMException("Measurement cancelled", "AbortError"));
      const visibility = () => {
        if (document.visibilityState !== "visible")
          fail(new Error("Keep this tab visible during measurement"));
      };
      const tick = (time: number) => {
        try {
          if (signal.aborted) {
            aborted();
            return;
          }
          if (document.visibilityState !== "visible") {
            visibility();
            return;
          }
          points.push({ ...read(), time, visible: true });
          if (points.length > 1 && time - points[0].time >= durationMs) {
            const report = summarizeFrameWindow(points, durationMs);
            cleanup();
            resolve(report);
          } else handle = requestAnimationFrame(tick);
        } catch (error) {
          fail(error);
        }
      };
      if (signal.aborted) {
        aborted();
        return;
      }
      signal.addEventListener("abort", aborted, { once: true });
      document.addEventListener("visibilitychange", visibility);
      handle = requestAnimationFrame(tick);
    },
  );
}

export type BrowserPerformanceReport = ReturnType<
  typeof summarizeFrameWindow
> & {
  schema_version: number;
  captured_at: string;
  world_version: string;
  quality: string;
  citizens: number;
  renderer: string;
  scope: string;
};
