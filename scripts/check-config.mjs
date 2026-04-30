import fs from "node:fs";
import path from "node:path";
import process from "node:process";

const root = process.cwd();
const configDir = path.join(root, "config");
const requiredFiles = [
  "miktex.json",
  "nodejs.json",
  "claude-code.json",
  "providers.json",
  "jianying.json",
  "project-defaults.json",
];

let failed = false;

console.log("Checking config files in", configDir);
for (const name of requiredFiles) {
  const fullPath = path.join(configDir, name);
  const exists = fs.existsSync(fullPath);
  console.log(`${exists ? "OK " : "MISS"} ${name}`);
  if (!exists) {
    failed = true;
    continue;
  }
  try {
    JSON.parse(fs.readFileSync(fullPath, "utf8"));
  } catch (error) {
    console.log(`ERR ${name}: ${error.message}`);
    failed = true;
  }
}

const packageJson = path.join(root, "package.json");
if (!fs.existsSync(packageJson)) {
  console.log("MISS package.json");
  failed = true;
} else {
  console.log("OK  package.json");
}

process.exit(failed ? 1 : 0);
