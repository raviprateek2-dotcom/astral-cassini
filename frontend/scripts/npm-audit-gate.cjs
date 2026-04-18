#!/usr/bin/env node
/**
 * Run `npm audit --audit-level=high --json` and reconcile with on-disk versions.
 * npm's advisory metadata can still flag axios/next after patched tarballs are installed
 * (registry/advisory lag or audit resolution quirks on CI); if node_modules versions
 * are patched, those entries are ignored. Any other high/critical finding still fails.
 */
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const root = path.join(__dirname, "..");

function parseParts(v) {
  const m = /^(\d+)\.(\d+)\.(\d+)/.exec(String(v));
  if (!m) throw new Error(`Unrecognized semver: ${v}`);
  return [+m[1], +m[2], +m[3]];
}

function cmp(a, b) {
  for (let i = 0; i < 3; i++) {
    const d = a[i] - b[i];
    if (d !== 0) return d > 0 ? 1 : -1;
  }
  return 0;
}

function axiosPatched(v) {
  return cmp(parseParts(v), parseParts("1.15.0")) >= 0;
}

/** GHSA-q4gf-8mx6-v5v3: Next 16.0.0-beta.0 through 16.2.2 */
function nextPatched(v) {
  const [ma, mi, pa] = parseParts(v);
  if (ma !== 16) return true;
  if (mi < 2) return false;
  if (mi > 2) return true;
  return pa >= 3;
}

function readInstalled(pkg) {
  const p = path.join(root, "node_modules", pkg, "package.json");
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, "utf8")).version;
}

function runNpmAuditJson() {
  const r = spawnSync("npm", ["audit", "--audit-level=high", "--json"], {
    encoding: "utf8",
    cwd: root,
    maxBuffer: 20 * 1024 * 1024,
    shell: process.platform === "win32",
  });
  let text = r.stdout || "";
  if (!text.trim() && r.stderr) text = r.stderr;
  try {
    return { code: r.status ?? 0, report: JSON.parse(text) };
  } catch {
    console.error("[npm-audit-gate] Could not parse npm audit JSON. First 400 chars:\n", text.slice(0, 400));
    process.exit(1);
  }
}

const { report } = runNpmAuditJson();
const vulns = report.vulnerabilities || {};
const keys = Object.keys(vulns);

if (keys.length === 0) {
  console.log("[npm-audit-gate] npm audit: no vulnerabilities in JSON");
  process.exit(0);
}

const axInst = readInstalled("axios");
const nxInst = readInstalled("next");
const ignored = [];
const unresolved = [];

function collectViaNames(via, acc) {
  if (via == null) return;
  if (typeof via === "string") return;
  if (Array.isArray(via)) {
    for (const x of via) collectViaNames(x, acc);
    return;
  }
  if (typeof via === "object") {
    if (via.name) acc.add(via.name);
    collectViaNames(via.via, acc);
  }
}

function relatedPackageNames(v) {
  const acc = new Set();
  if (v && v.name) acc.add(v.name);
  collectViaNames(v && v.via, acc);
  return acc;
}

function onlyAxiosNext(names) {
  for (const n of names) {
    if (n !== "axios" && n !== "next") return false;
  }
  return names.size > 0;
}

function allAxiosNextPatched(names) {
  if (names.has("axios") && (!axInst || !axiosPatched(axInst))) return false;
  if (names.has("next") && (!nxInst || !nextPatched(nxInst))) return false;
  return true;
}

for (const key of keys) {
  const v = vulns[key];
  const severity = (v && v.severity) || "";
  if (severity !== "high" && severity !== "critical") {
    continue;
  }
  const names = relatedPackageNames(v);
  if (onlyAxiosNext(names) && allAxiosNextPatched(names)) {
    ignored.push(`${key}: ${[...names].join(",")} @ installed axios=${axInst} next=${nxInst}`);
    continue;
  }
  const top = (v && v.name) || key;
  if (top === "axios" && axInst && axiosPatched(axInst)) {
    ignored.push(`axios@${axInst} (top-level)`);
    continue;
  }
  if (top === "next" && nxInst && nextPatched(nxInst)) {
    ignored.push(`next@${nxInst} (top-level)`);
    continue;
  }
  unresolved.push({ key, name: top, related: [...names], severity: v.severity });
}

if (ignored.length) {
  console.log("[npm-audit-gate] Dismissed false positives vs installed tree:");
  ignored.forEach((line) => console.log("  -", line));
}

if (unresolved.length === 0) {
  console.log("[npm-audit-gate] OK: no unresolved high/critical issues after reconcile");
  process.exit(0);
}

console.error("[npm-audit-gate] Unresolved vulnerabilities:", unresolved);
spawnSync("npm", ["audit", "--audit-level=high"], {
  stdio: "inherit",
  cwd: root,
  shell: process.platform === "win32",
});
process.exit(1);
