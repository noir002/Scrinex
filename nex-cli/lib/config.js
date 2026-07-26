const fs = require("fs");
const path = require("path");

const CONFIG_FILE = ".nexconfig.json";

function configPath() {
  return path.join(process.cwd(), CONFIG_FILE);
}

function readConfig() {
  const p = configPath();
  if (!fs.existsSync(p)) {
    return null;
  }
  return JSON.parse(fs.readFileSync(p, "utf-8"));
}

function writeConfig(config) {
  fs.writeFileSync(configPath(), JSON.stringify(config, null, 2));
}

function requireConfig() {
  const config = readConfig();
  if (!config) {
    console.error(
      "No .nexconfig.json found here. Run `nex init <repo-name>` first."
    );
    process.exit(1);
  }
  return config;
}

module.exports = { readConfig, writeConfig, requireConfig };
