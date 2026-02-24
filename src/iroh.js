import * as fs from 'fs/promises';
import * as path from 'path';
import * as crypto from 'crypto';
import { Iroh, NodeDiscoveryConfig } from '@number0/iroh';
import { CONFIG_DIR, ensureConfigDir } from './config.js';

// Path for the persistent iroh secret key
const IROH_KEY_FILE = path.join(CONFIG_DIR, 'iroh.key');

// The ALPN protocol identifier for WebMCP over iroh
export const WEBMCP_ALPN = new TextEncoder().encode('webmcp/1');

// Module-level state
let irohNode = null;

/**
 * Load or generate the persistent iroh secret key.
 * Stored as a 32-byte hex string in ~/.webmcp/iroh.key
 */
async function loadOrCreateSecretKey() {
    await ensureConfigDir();
    try {
        const hex = (await fs.readFile(IROH_KEY_FILE, 'utf8')).trim();
        if (hex.length === 64) {
            return Array.from(Buffer.from(hex, 'hex'));
        }
    } catch (err) {
        if (err.code !== 'ENOENT') {
            console.error('Warning: could not read iroh key file, generating a new one:', err.message);
        }
    }

    // Generate a fresh Ed25519 secret key (32 random bytes)
    const keyBytes = crypto.randomBytes(32);
    await fs.writeFile(IROH_KEY_FILE, keyBytes.toString('hex'), { encoding: 'utf8', mode: 0o600 });
    return Array.from(keyBytes);
}

/**
 * Start the iroh node. Creates a memory-resident node with a persistent identity
 * derived from the key stored in ~/.webmcp/iroh.key.
 *
 * Returns the started Iroh node instance.
 */
export async function startIrohNode() {
    if (irohNode) {
        return irohNode;
    }

    const secretKey = await loadOrCreateSecretKey();

    irohNode = await Iroh.memory({
        nodeDiscovery: NodeDiscoveryConfig.Default,
        secretKey,
    });

    const nodeId = await irohNode.net.nodeId();
    const nodeAddr = await irohNode.net.nodeAddr();

    console.error(`Iroh node started`);
    console.error(`  NodeId:   ${nodeId}`);
    if (nodeAddr.relayUrl) {
        console.error(`  Relay:    ${nodeAddr.relayUrl}`);
    }
    if (nodeAddr.addresses && nodeAddr.addresses.length > 0) {
        console.error(`  Addrs:    ${nodeAddr.addresses.join(', ')}`);
    }

    return irohNode;
}

/**
 * Shut down the iroh node gracefully.
 */
export async function stopIrohNode() {
    if (irohNode) {
        try {
            await irohNode.node.shutdown();
        } catch (err) {
            console.error('Error shutting down iroh node:', err.message);
        }
        irohNode = null;
    }
}

/**
 * Return the iroh node's public NodeId string, or null if not started.
 */
export async function getIrohNodeId() {
    if (!irohNode) return null;
    return irohNode.net.nodeId();
}

/**
 * Return the iroh node's full NodeAddr (includes relay URL and direct addresses),
 * or null if not started.
 */
export async function getIrohNodeAddr() {
    if (!irohNode) return null;
    return irohNode.net.nodeAddr();
}
