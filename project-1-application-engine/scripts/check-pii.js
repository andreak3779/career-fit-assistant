#!/usr/bin/env node
// Pre-commit / CI guard for app-engine-bundle.md.
//
// Rules:
//   - File MUST NOT be tracked by git (it contains PII: email, phone).
//   - If the file exists locally, scan it for obvious PII patterns.
//   - If the file does not exist (clean CI checkout), pass silently.
//
// Exit codes: 0 = clean, 1 = violation.

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const bundleRel = 'app-engine-bundle.md';

function isTracked() {
  try {
    const out = execSync(`git ls-files --error-unmatch -- ${bundleRel}`, {
      stdio: ['ignore', 'pipe', 'pipe'],
    }).toString();
    return out.trim().length > 0;
  } catch {
    return false;
  }
}

function scanPii(text) {
  const phone = /\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b/;
  const email = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/;
  const violations = [];
  if (phone.test(text)) violations.push('phone');
  if (email.test(text)) violations.push('email');
  return violations;
}

const root = path.resolve(__dirname, '..');
process.chdir(root);

if (isTracked()) {
  console.error(`ERROR: ${bundleRel} is tracked by git.`);
  console.error('       This file contains PII (email, phone). Remove it from the index:');
  console.error(`         git rm --cached ${bundleRel}`);
  process.exit(1);
}

if (fs.existsSync(bundleRel)) {
  const body = fs.readFileSync(bundleRel, 'utf8');
  const hits = scanPii(body);
  if (hits.length > 0) {
    console.error(`ERROR: ${bundleRel} contains: ${hits.join(', ')}.`);
    console.error('       This file is gitignored; never commit it. Regenerate locally via');
    console.error('       project-2 profile-hub-bundle-generator skill and delete it when done.');
    process.exit(1);
  }
  console.log(`Local ${bundleRel} scanned — no phone or email found.`);
} else {
  console.log(`${bundleRel} not present (clean checkout) — PII guard passed.`);
}

process.exit(0);
