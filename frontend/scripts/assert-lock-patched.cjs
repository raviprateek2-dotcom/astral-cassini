#!/usr/bin/env node
/**
 * Fail fast if package-lock.json still pins vulnerable axios / next (npm audit advisories).
 * Run from repo root: node frontend/scripts/assert-lock-patched.cjs
 * Or from frontend/: node scripts/assert-lock-patched.cjs
 */
const fs = require("fs");
const path = require("path");

const lockPath = path.join(__dirname, "..", "package-lock.json");
const lock = JSON.parse(fs.readFileSync(lockPath, "utf8"));

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

const ax = lock.packages["node_modules/axios"]?.version;
const nx = lock.packages["node_modules/next"]?.version;

if (!ax || !axiosPatched(ax)) {
  console.error(
    `[assert-lock-patched] axios in lockfile is "${ax}"; need >= 1.15.0 (GHSA-3p68-rc4w-qgx5). Run: cd frontend && npm install`,
  );
  process.exit(1);
}
if (!nx || !nextPatched(nx)) {
  console.error(
    `[assert-lock-patched] next in lockfile is "${nx}"; need >= 16.2.3 for 16.2.x (GHSA-q4gf-8mx6-v5v3). Run: cd frontend && npm install`,
  );
  process.exit(1);
}

console.log(`[assert-lock-patched] OK axios@${ax} next@${nx}`);
