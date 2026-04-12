import fs from 'node:fs'
import path from 'node:path'
import { execSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const certDir = path.join(root, 'certs')
const keyPath = path.join(certDir, 'dev-key.pem')
const certPath = path.join(certDir, 'dev-cert.pem')

fs.mkdirSync(certDir, { recursive: true })

const command = [
  'openssl req -x509 -nodes -newkey rsa:2048',
  `-keyout "${keyPath}"`,
  `-out "${certPath}"`,
  '-sha256 -days 3650',
  '-subj "/CN=mock-interview-dev"',
  '-addext "subjectAltName=DNS:localhost,IP:127.0.0.1,IP:0.0.0.0"',
].join(' ')

execSync(command, { stdio: 'inherit' })

console.log(`generated ${keyPath}`)
console.log(`generated ${certPath}`)
