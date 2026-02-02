import subprocess
import time
import os
import sys

# ================= Configuration =================
# Replace with your actual auth key from https://login.tailscale.com/admin/settings/keys
TAILSCALE_AUTH_KEY = "tskey-auth-kqRAcm3tCZ11CNTRL-Jvpy71eHvpav5G45VTkvoaZBBzJP6ZC7"

# Ports for the local proxies
SOCKS_PORT = "1055"
HTTP_PORT = "1056"
# =================================================

def log(msg, color="white"):
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[0m",
    }
    print(f"{colors.get(color, '')}{msg}\033[0m")

def run_command(cmd, shell=True, check=True, capture_output=False):
    log(f"▶ {cmd}", "cyan")
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        log(f"❌ Error executing command: {e}", "red")
        if e.stderr:
            log(f"Stderr: {e.stderr}", "red")
        return None

def install_tailscale():
    log("Installing/Updating Tailscale...", "blue")
    # Using the official install script
    run_command("curl -fsSL https://tailscale.com/install.sh | sh")

def start_tailscaled():
    log("Starting tailscaled in userspace-networking (netstack) mode...", "blue")
    
    # Check if tailscaled is already running - silence the error log for this check
    try:
        # Use a raw subprocess call to avoid the printing in run_command
        is_running = subprocess.run(["pgrep", "tailscaled"], capture_output=True).returncode == 0
        if is_running:
            log("tailscaled is already running, killing old instance...")
            run_command("pkill tailscaled || true")
    except Exception:
        pass

    # Start tailscaled in the background
    # --tun=userspace-networking allows it to run without /dev/net/tun (common in Colab/Docker)
    # --socks5-server and --outbound-http-proxy-listen provide local proxy access
    cmd = (
        f"nohup tailscaled "
        f"--tun=userspace-networking "
        f"--socks5-server=localhost:{SOCKS_PORT} "
        f"--outbound-http-proxy-listen=localhost:{HTTP_PORT} "
        f"> /tmp/tailscaled.log 2>&1 &"
    )
    subprocess.Popen(cmd, shell=True)
    time.sleep(5)  # Wait for daemon to initialize

def main():
    if os.name == 'nt':
        log("This script is designed for Linux environments (Colab, VPS, etc.).", "red")
        sys.exit(1)

    install_tailscale()
    start_tailscaled()

    log("Connecting to Tailscale and advertising as Exit Node...", "blue")
    
    # --advertise-exit-node: This makes this node appear as an Exit Node choice in the Tailnet
    # --accept-dns=false: Avoids modifying local DNS settings which might fail in userspace mode
    # --hostname: Optional, helps identify the node
    up_cmd = (
        f"tailscale up "
        f"--authkey={TAILSCALE_AUTH_KEY} "
        f"--advertise-exit-node "
        f"--accept-dns=false "
        f"--hostname=exit-node-server"
    )
    
    result = run_command(up_cmd)
    
    if result:
        # Get the IP address
        ip_info = run_command("tailscale ip -4", capture_output=True)
        ts_ip = ip_info.stdout.strip() if ip_info and ip_info.stdout else "Unknown"

        log("\n" + "="*45, "green")
        log("✅ SUCCESS: Tailscale Exit Node is active!", "green")
        log(f"📍 Tailscale IP: {ts_ip}", "white")
        log(f"🧦 SOCKS5 Proxy : 127.0.0.1:{SOCKS_PORT}", "cyan")
        log(f"🌐 HTTP Proxy   : 127.0.0.1:{HTTP_PORT}", "cyan")
        log("\nNext Steps (IMPORTANT):", "white")
        log(f"1. Go to: https://login.tailscale.com/admin/machines", "yellow")
        log(f"2. Find machine: 'exit-node-server' (IP: {ts_ip})", "yellow")
        log("3. Click 'Edit Route Settings' -> Enable 'Exit Node'", "yellow")
        log("4. On your client, select this node as your Exit Node.", "yellow")
        log("="*45, "green")
        
        # Keep the script running
        log("\nScript is running. Press Ctrl+C to stop (though tailscaled will continue in background).", "magenta")
        try:
            while True:
                # Print status every 5 minutes to keep session alive
                time.sleep(300)
                status = run_command("tailscale status", capture_output=True)
                if status:
                    log(f"Health Check: Tailscale is {status.stdout.splitlines()[0] if status.stdout else 'Running'}", "blue")
        except KeyboardInterrupt:
            log("\nStopping script...", "yellow")
    else:
        log("❌ Failed to bring Tailscale up. Check /tmp/tailscaled.log for details.", "red")
        run_command("cat /tmp/tailscaled.log")

if __name__ == "__main__":
    main()
