const fs = require('fs')
const path = require('path')

const sourceDir = path.resolve(__dirname, 'node_modules', 'cesium', 'Build', 'Cesium')
const targetDir = path.resolve(__dirname, 'public', 'cesium')

const dirsToCopy = ['Workers', 'Assets', 'Widgets', 'ThirdParty']

if (!fs.existsSync(sourceDir)) {
  console.error('Cesium source directory not found. Run "npm install" first.')
  process.exit(1)
}

function copyDir(src, dest) {
  if (!fs.existsSync(dest)) {
    fs.mkdirSync(dest, { recursive: true })
  }
  const entries = fs.readdirSync(src, { withFileTypes: true })
  for (const entry of entries) {
    const srcPath = path.join(src, entry.name)
    const destPath = path.join(dest, entry.name)
    if (entry.isDirectory()) {
      copyDir(srcPath, destPath)
    } else {
      fs.copyFileSync(srcPath, destPath)
    }
  }
}

if (fs.existsSync(targetDir)) {
  fs.rmSync(targetDir, { recursive: true, force: true })
}
fs.mkdirSync(targetDir, { recursive: true })

for (const dir of dirsToCopy) {
  const src = path.join(sourceDir, dir)
  const dest = path.join(targetDir, dir)
  if (fs.existsSync(src)) {
    copyDir(src, dest)
    console.log(`Copied: ${dir}/`)
  } else {
    console.warn(`Warning: ${dir}/ not found in Cesium source`)
  }
}

console.log('Cesium static assets copied to public/cesium/')
