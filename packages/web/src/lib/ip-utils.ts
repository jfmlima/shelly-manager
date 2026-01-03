/**
 * IP and CIDR validation utilities.
 *
 * Provides validation and calculation functions for IPv4 addresses and CIDR notation
 * without requiring external npm packages.
 */

/**
 * Validate IPv4 address format.
 *
 * @param ip - IP address string to validate
 * @returns true if valid IPv4, false otherwise
 */
export function isValidIPv4(ip: string): boolean {
  const ipv4Regex =
    /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
  return ipv4Regex.test(ip.trim());
}

/**
 * Validate CIDR notation format.
 *
 * @param cidr - CIDR string to validate (e.g., "192.168.1.0/24")
 * @returns true if valid CIDR notation, false otherwise
 */
export function isValidCIDR(cidr: string): boolean {
  const parts = cidr.trim().split("/");
  if (parts.length !== 2) return false;

  const [ip, prefixStr] = parts;

  // Validate IP part
  if (!isValidIPv4(ip)) return false;

  // Validate prefix length (0-32)
  const prefix = parseInt(prefixStr, 10);
  if (isNaN(prefix) || prefix < 0 || prefix > 32) return false;

  return true;
}

/**
 * Convert IPv4 address string to 32-bit integer.
 *
 * @param ip - IPv4 address string
 * @returns 32-bit integer representation
 */
export function ipToInt(ip: string): number {
  const parts = ip.split(".").map(Number);
  return (
    ((parts[0] << 24) | (parts[1] << 16) | (parts[2] << 8) | parts[3]) >>> 0
  ); // Unsigned right shift to ensure positive
}

/**
 * Convert 32-bit integer to IPv4 address string.
 *
 * @param int - 32-bit integer representation of IP
 * @returns IPv4 address string
 */
export function intToIP(int: number): string {
  return [
    (int >>> 24) & 0xff,
    (int >>> 16) & 0xff,
    (int >>> 8) & 0xff,
    int & 0xff,
  ].join(".");
}

/**
 * Parse CIDR notation and return start IP, end IP, and count.
 *
 * @param cidr - CIDR notation string (e.g., "192.168.1.0/24")
 * @returns Object with start, end, and count, or null if invalid
 */
export function cidrToRange(cidr: string): {
  start: string;
  end: string;
  count: number;
} | null {
  if (!isValidCIDR(cidr)) return null;

  const [ip, prefixStr] = cidr.split("/");
  const prefix = parseInt(prefixStr, 10);

  // Calculate network address (start IP)
  const ipInt = ipToInt(ip);
  const mask = (0xffffffff << (32 - prefix)) >>> 0;
  const networkInt = (ipInt & mask) >>> 0;

  // Calculate broadcast address (end IP)
  const hostMask = ~mask >>> 0;
  const broadcastInt = (networkInt | hostMask) >>> 0;

  // Calculate host count
  const count = broadcastInt - networkInt + 1;

  return {
    start: intToIP(networkInt),
    end: intToIP(broadcastInt),
    count,
  };
}

/**
 * Calculate number of IPs between start and end (inclusive).
 *
 * @param startIP - Start IPv4 address
 * @param endIP - End IPv4 address
 * @returns Number of IPs in range, or null if invalid
 */
export function calculateIPCount(
  startIP: string,
  endIP: string,
): number | null {
  if (!isValidIPv4(startIP) || !isValidIPv4(endIP)) return null;

  const startInt = ipToInt(startIP);
  const endInt = ipToInt(endIP);

  if (startInt > endInt) return null; // Invalid range

  return endInt - startInt + 1;
}

/**
 * Validate that start IP is less than or equal to end IP.
 *
 * @param startIP - Start IPv4 address
 * @param endIP - End IPv4 address
 * @returns true if valid range order, false otherwise
 */
export function isValidIPRange(startIP: string, endIP: string): boolean {
  if (!isValidIPv4(startIP) || !isValidIPv4(endIP)) return false;
  return ipToInt(startIP) <= ipToInt(endIP);
}

/**
 * Get CIDR notation for common network sizes.
 *
 * @param baseIP - Base IP address (e.g., "192.168.1.0")
 * @param size - Network size ("24", "16", "8")
 * @returns CIDR notation string
 */
export function getCommonCIDR(baseIP: string, size: "24" | "16" | "8"): string {
  // Normalize base IP to network address
  const cidr = `${baseIP}/${size}`;
  const range = cidrToRange(cidr);
  return range ? `${range.start}/${size}` : cidr;
}

/**
 * Validate a target string (IP, Range, or CIDR).
 *
 * @param target - String to validate
 * @returns true if valid target, false otherwise
 */
export function isValidTarget(target: string): boolean {
  const trimmed = target.trim();
  if (!trimmed) return false;

  // Single IP
  if (isValidIPv4(trimmed)) return true;

  // CIDR
  if (trimmed.includes("/") && isValidCIDR(trimmed)) return true;

  // Range (start-end)
  if (trimmed.includes("-")) {
    const parts = trimmed.split("-");
    if (parts.length !== 2) return false;
    const [start, end] = parts;

    // Handle full range: 192.168.1.1-192.168.1.50
    if (isValidIPv4(start) && isValidIPv4(end)) {
      return isValidIPRange(start, end);
    }

    // Handle short range: 192.168.1.1-50
    if (isValidIPv4(start) && !end.includes(".")) {
      const startParts = start.split(".");
      const fullEnd = [...startParts.slice(0, 3), end].join(".");
      return isValidIPv4(fullEnd) && isValidIPRange(start, fullEnd);
    }
  }

  return false;
}

/**
 * Parse and clean a list of manual IPs.
 * Splits by comma, space, or newline and removes invalid entries.
 *
 * @param input - Raw input string
 * @returns Array of valid IP strings
 */
export function parseManualIPs(input: string): string[] {
  if (!input) return [];

  return input
    .split(/[,\s\n]+/)
    .map((ip) => ip.trim())
    .filter((ip) => !!ip && isValidIPv4(ip));
}

/**
 * Validate a range or CIDR string.
 */
export function isValidRangeOrCIDR(input: string): boolean {
  const trimmed = input.trim();
  if (!trimmed) return false;

  // CIDR
  if (trimmed.includes("/") && isValidCIDR(trimmed)) return true;

  // Range
  if (trimmed.includes("-")) {
    const parts = trimmed.split("-");
    if (parts.length !== 2) return false;
    const [start, end] = parts;

    if (isValidIPv4(start)) {
      if (isValidIPv4(end)) return isValidIPRange(start, end);
      if (!end.includes(".")) {
        const startParts = start.split(".");
        const fullEnd = [...startParts.slice(0, 3), end].join(".");
        return isValidIPv4(fullEnd) && isValidIPRange(start, fullEnd);
      }
    }
  }

  return false;
}
