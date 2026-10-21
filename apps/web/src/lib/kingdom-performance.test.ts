import { describe, expect, it } from "vitest";
import { summarizeFrameWindow, type FramePoint } from "./kingdom-performance";
const points: FramePoint[] = Array.from({ length: 11 }, (_, i) => ({
  time: i * 1000,
  frames: 40 + i,
  width: 1440,
  height: 1000,
  visible: true,
}));
describe("truthful browser performance reports", () => {
  it("does not label browser callbacks as rendered scene frames", () => {
    const window = points.map((p, i) => ({
      ...p,
      frames: 40 + Math.floor(i / 2),
    }));
    const report = summarizeFrameWindow(window, 10000);
    expect(report.scene_frames).toBe(5);
    expect(report.scene_fps).toBe(0.5);
    expect(report.browser_raf_fps).toBe(1);
  });
  it("rejects a stalled scene despite continuing browser callbacks", () => {
    expect(() =>
      summarizeFrameWindow(
        points.map((p) => ({ ...p, frames: 40 })),
        10000,
      ),
    ).toThrow("did not render");
  });
  it.each(["hidden", "resize", "restart", "short"])(
    "rejects an invalid %s sampling window",
    (reason) => {
      const window = points.map((p) => ({ ...p }));
      if (reason === "hidden") window[5].visible = false;
      if (reason === "resize") window[5].width = 1000;
      if (reason === "restart") window[5].frames = 0;
      if (reason === "short") window.pop();
      expect(() => summarizeFrameWindow(window, 10000)).toThrow();
    },
  );
});
