import subprocess
import time
import os
import sys
import platform
import shutil

# ================= Configuration =================
TAILSCALE_AUTH_KEY = "tskey-auth-kqRAcm3tCZ11CNTRL-Jvpy71eHvpav5G45VTkvoaZBBzJP6ZC7"
SOCKS_PORT = "1055"
HTTP_PORT = "1056"

# Proxy Configuration
USE_PROXY = True
PROXY_URL = "http://stc-in-sid-329997018:pgw-aa7114fb13386cec3e5e5b3d64384eae058bea140e0d46fc@37.221.93.235:5959"

WORKING_DIR = os.getcwd()
BIN_DIR = os.path.join(WORKING_DIR, "ts_bin")
STATE_DIR = os.path.join(WORKING_DIR, "ts_state")
TAILSCALED_SOCKET = os.path.join(WORKING_DIR, "tailscaled.sock")
LOG_FILE = "/tmp/tailscaled.log"
# =================================================

def log(msg, color="white"):
    colors = {"red": "\033[91m", "green": "\033[92m", "yellow": "\033[93m", "blue": "\033[94m", "cyan": "\033[96m", "white": "\033[0m"}
    print(f"{colors.get(color, '')}{msg}\033[0m")

def run_command(cmd, capture_output=False, env=None):
    cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
    log(f"▶ {cmd_str}", "cyan")
    try:
        return subprocess.run(cmd, shell=isinstance(cmd, str), check=True, capture_output=capture_output, text=True, env=env)
    except subprocess.CalledProcessError as e:
        log(f"❌ Command failed: {e}", "red")
        return None

def setup_portable_tailscale():
    for d in [BIN_DIR, STATE_DIR]:
        if not os.path.exists(d): os.makedirs(d)
    ts_path, tsd_path = os.path.join(BIN_DIR, "tailscale"), os.path.join(BIN_DIR, "tailscaled")
    if os.path.exists(ts_path) and os.path.exists(tsd_path): return ts_path, tsd_path
    log("Downloading portable Tailscale binaries...", "blue")
    arch = "amd64" if platform.machine() in ["x86_64", "amd64"] else "arm64"
    VERSION = "1.94.1"
    URL = f"https://pkgs.tailscale.com/stable/tailscale_{VERSION}_{arch}.tgz"
    run_command(f"curl -L {URL} -o tailscale.tgz")
    run_command("tar xzf tailscale.tgz")
    folder = f"tailscale_{VERSION}_{arch}"
    shutil.move(f"{folder}/tailscale", ts_path)
    shutil.move(f"{folder}/tailscaled", tsd_path)
    run_command(f"rm -rf tailscale.tgz {folder}")
    os.chmod(ts_path, 0o755); os.chmod(tsd_path, 0o755)
    return ts_path, tsd_path

def setup_gost():
    gost_path = os.path.join(BIN_DIR, "gost")
    if os.path.exists(gost_path): return gost_path
    log("Downloading portable Gost (proxy bridge)...", "blue")
    arch = "amd64" if platform.machine() in ["x86_64", "amd64"] else "arm64"
    VERSION = "2.11.5"
    URL = f"https://github.com/ginuerzh/gost/releases/download/v{VERSION}/gost-linux-{arch}-{VERSION}.gz"
    
    # Use a fixed temporary name to avoid filename confusion
    run_command(f"curl -L {URL} -o gost.gz")
    run_command("gunzip -f gost.gz")
    # gunzip gost.gz produces a file named 'gost'
    if os.path.exists("gost"):
        shutil.move("gost", gost_path)
    else:
        # Fallback for different gunzip behaviors
        long_name = f"gost-linux-{arch}-{VERSION}"
        if os.path.exists(long_name):
            shutil.move(long_name, gost_path)
    
    if not os.path.exists(gost_path):
        log("❌ Failed to setup gost. Manual check required.", "red")
        sys.exit(1)
        
    os.chmod(gost_path, 0o755)
    return gost_path

def main():
    if os.name == 'nt': log("Use Linux/WSL.", "red"); sys.exit(1)
    ts_path, tsd_path = setup_portable_tailscale()

    log("Cleaning up previous instances...", "yellow")
    subprocess.run(["pkill", "-9", "-f", tsd_path], capture_output=True)
    subprocess.run(["pkill", "-9", "-f", "gost"], capture_output=True) # Clean up previous gost
    if os.path.exists(TAILSCALED_SOCKET):
        try: os.remove(TAILSCALED_SOCKET)
        except: pass
    
    env = os.environ.copy()
    if USE_PROXY and PROXY_URL:
        gost_path = setup_gost()
        # Bridge HTTP Proxy -> Local SOCKS5 (Tailscale netstack works best with SOCKS5)
        local_bridge = "127.0.0.1:1080"
        # Gost command: -L=socks5://:1080 -F=http://user:pass@ip:port
        gost_cmd = [gost_path, "-L", f"socks5://{local_bridge}", "-F", PROXY_URL]
        
        log(f"🚀 Starting proxy bridge (Gost) to Indian IP...", "yellow")
        # Redirect gost output to a log file for debugging
        gost_log = os.path.join(WORKING_DIR, "gost.log")
        with open(gost_log, "w") as f:
            subprocess.Popen(gost_cmd, stdout=f, stderr=f)
        
        # Verify bridge is working
        log("⏳ Verifying proxy bridge and testing speed...", "blue")
        time.sleep(3)
        try:
            # 1. Basic IP Check
            test_cmd = f'curl -s --socks5-hostname {local_bridge} https://ipinfo.io/json'
            test_result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True, timeout=10)
            
            if test_result.returncode == 0:
                data = subprocess.run(f'curl -s --socks5-hostname {local_bridge} https://ipinfo.io/ip', shell=True, capture_output=True, text=True).stdout.strip()
                log(f"✅ Proxy bridge verified! IP: {data}", "green")
                
                # 2. Google Connectivity & Latency Check
                log("📡 Checking Google connectivity...", "blue")
                # Time the request to get a sense of speed/latency
                start_time = time.time()
                google_check = subprocess.run(f'curl -s -I --socks5-hostname {local_bridge} https://www.google.com', shell=True, capture_output=True, text=True, timeout=10)
                latency = (time.time() - start_time) * 1000
                
                if google_check.returncode == 0:
                    log(f"✅ Google is reachable! Latency: {latency:.1f}ms", "green")
                    if latency > 1000:
                        log("⚠️ Warning: High latency detected. Speed might be slow.", "yellow")
                else:
                    log("❌ Proxy is up but Google is unreachable. Check your proxy provider.", "red")
                    sys.exit(1)
            else:
                log("⚠️ Proxy bridge verification failed. Check gost.log", "red")
                if os.path.exists(gost_log):
                    with open(gost_log, "r") as f: log(f.read()[-500:], "yellow")
                sys.exit(1)
        except Exception as e:
            log(f"⚠️ Proxy verification error: {e}", "red")
            sys.exit(1)

        proxy_url = f"socks5://{local_bridge}"
        # Set all possible proxy variables
        for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
            env[var] = proxy_url
            
        # These are the magic knobs for Tailscale's userspace networking
        # standard socks5:// is preferred for the Go netstack
        env["TS_DEBUG_USERNET_PROXY"] = proxy_url
        env["TS_DEBUG_NETSTACK_PROXY"] = proxy_url
        
        # MTU Tweak: Helps prevent packet drops over slow/proxied connections
        env["TS_USERSPACE_MTU"] = "1280"
        
        display_url = PROXY_URL.split("@")[-1] if "@" in PROXY_URL else PROXY_URL
        log(f"🌐 Proxy Tunnel Active: Outbound traffic forced through {display_url}", "green")

    tsd_cmd = [
        tsd_path, "--tun=userspace-networking",
        f"--socket={TAILSCALED_SOCKET}",
        f"--state={os.path.join(STATE_DIR, 'tailscaled.state')}",
        f"--socks5-server=localhost:{SOCKS_PORT}",
        f"--outbound-http-proxy-listen=localhost:{HTTP_PORT}",
    ]
    
    log("Starting tailscaled...", "blue")
    with open(LOG_FILE, "w") as f:
        subprocess.Popen(tsd_cmd, stdout=f, stderr=f, env=env)
    
    # Wait for socket to appear
    log("Waiting for tailscaled socket...", "blue")
    for _ in range(15):
        if os.path.exists(TAILSCALED_SOCKET):
            time.sleep(2) # Give it a moment to actually start listening
            break
        time.sleep(1)
    else:
        log("❌ tailscaled socket never appeared. Check logs below:", "red")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: print(f.read())
        sys.exit(1)

    log("Connecting to Tailscale...", "blue")
    up_cmd = [
        ts_path, f"--socket={TAILSCALED_SOCKET}", "up",
        f"--authkey={TAILSCALE_AUTH_KEY}",
        "--advertise-exit-node", "--accept-dns=false",
        "--hostname=exit-node-server", "--snat-subnet-routes=true"
    ]
    
    if run_command(up_cmd, env=env):
        log("\n✅ SUCCESS: Exit Node is active!", "green")
        log(f"📍 SOCKS5 Proxy : 127.0.0.1:{SOCKS_PORT}", "cyan")
        log("🚀 Exit Node is now ready for use!", "green")
        try:
            while True:
                time.sleep(60)
                if subprocess.run([ts_path, f"--socket={TAILSCALED_SOCKET}", "status"], capture_output=True).returncode != 0:
                    log("⚠️ tailscaled connection lost.", "red")
                    break
        except KeyboardInterrupt: pass
    else:
        log("❌ Connection failed. Last logs:", "red")
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f: print("\n".join(f.readlines()[-20:]))

if __name__ == "__main__":
    main()