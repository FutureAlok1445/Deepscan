const THERMAL = [
    [0, 0, 80], [0, 0, 160], [0, 0, 255], [0, 100, 255], [0, 200, 255],
    [0, 255, 180], [0, 255, 80], [120, 255, 0], [230, 255, 0],
    [255, 210, 0], [255, 110, 0], [255, 30, 0], [180, 0, 0],
];

function thermalColor(v) {
    v = Math.max(0, Math.min(1, v));
    const idx = v * (THERMAL.length - 1);
    const lo = Math.floor(idx);
    const hi = Math.min(lo + 1, THERMAL.length - 1);
    const t = idx - lo;
    return THERMAL[lo].map((c, i) => Math.round(c * (1 - t) + THERMAL[hi][i] * t));
}

function gaussBlur(src, W, H, r) {
    const sigma = r / 2.2, sz = r * 2 + 1;
    const k = Array.from({ length: sz }, (_, i) => {
        const x = i - r; return Math.exp(-(x * x) / (2 * sigma * sigma));
    });
    const ks = k.reduce((a, b) => a + b, 0);
    k.forEach((_, i) => k[i] /= ks);
    const tmp = new Float32Array(src.length), out = new Float32Array(src.length);
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        let s = 0; for (let n = 0; n < sz; n++) { const nx = Math.min(Math.max(x + n - r, 0), W - 1); s += src[y * W + nx] * k[n]; } tmp[y * W + x] = s;
    }
    for (let y = 0; y < H; y++) for (let x = 0; x < W; x++) {
        let s = 0; for (let n = 0; n < sz; n++) { const ny = Math.min(Math.max(y + n - r, 0), H - 1); s += tmp[ny * W + x] * k[n]; } out[y * W + x] = s;
    }
    return out;
}

function buildHeatmapFromRegions(regions, W, H) {
    const mask = new Float32Array(W * H);

    regions.forEach(({ polygon, intensity = 0.8 }) => {
        if (!polygon || polygon.length < 3) return;
        const pts = polygon.map(([px, py]) => [px * W, py * H]);

        const ys = pts.map(p => p[1]);
        const yMin = Math.max(0, Math.floor(Math.min(...ys)));
        const yMax = Math.min(H - 1, Math.ceil(Math.max(...ys)));

        for (let y = yMin; y <= yMax; y++) {
            const intersections = [];
            for (let i = 0; i < pts.length; i++) {
                const [x0, y0] = pts[i];
                const [x1, y1] = pts[(i + 1) % pts.length];
                if ((y0 <= y && y1 > y) || (y1 <= y && y0 > y)) {
                    intersections.push(x0 + (y - y0) / (y1 - y0) * (x1 - x0));
                }
            }
            intersections.sort((a, b) => a - b);
            for (let j = 0; j < intersections.length - 1; j += 2) {
                const xL = Math.max(0, Math.floor(intersections[j]));
                const xR = Math.min(W - 1, Math.ceil(intersections[j + 1]));
                for (let x = xL; x <= xR; x++) {
                    mask[y * W + x] = Math.max(mask[y * W + x], intensity);
                }
            }
        }
    });

    const blurred = gaussBlur(mask, W, H, 22);

    let mx = 0;
    for (let i = 0; i < blurred.length; i++) if (blurred[i] > mx) mx = blurred[i];
    if (mx === 0) mx = 1;

    const rgba = new Uint8ClampedArray(W * H * 4);
    for (let i = 0; i < W * H; i++) {
        const v = blurred[i] / mx;
        const [r, g, b] = thermalColor(v);
        rgba[i * 4] = r;
        rgba[i * 4 + 1] = g;
        rgba[i * 4 + 2] = b;
        rgba[i * 4 + 3] = v < 0.08 ? 0 : Math.round(Math.pow(v, 0.6) * 210);
    }
    return rgba;
}

export function compositeHeatmap(imgEl, regions) {
    return new Promise(resolve => {
        const MAX = 700;
        let w = imgEl.naturalWidth, h = imgEl.naturalHeight;
        if (w > MAX) { h = Math.round(h * MAX / w); w = MAX; }
        if (h > MAX) { w = Math.round(w * MAX / h); h = MAX; }

        const out = document.createElement("canvas");
        out.width = w; out.height = h;
        const ctx = out.getContext("2d");
        if (!ctx) return resolve("");

        ctx.drawImage(imgEl, 0, 0, w, h);

        // Desaturate slightly
        ctx.globalCompositeOperation = "saturation";
        ctx.fillStyle = "rgba(80,80,80,0.45)";
        ctx.fillRect(0, 0, w, h);
        ctx.globalCompositeOperation = "source-over";

        if (regions && regions.length > 0) {
            const heatData = buildHeatmapFromRegions(regions, w, h);
            const tmp = document.createElement("canvas");
            tmp.width = w; tmp.height = h;
            tmp.getContext("2d")?.putImageData(new ImageData(heatData, w, h), 0, 0);
            ctx.drawImage(tmp, 0, 0);
        }

        resolve(out.toDataURL("image/png"));
    });
}
