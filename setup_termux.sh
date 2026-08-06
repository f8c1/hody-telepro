#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# Hody-Telepro — Termux Full Setup Script
# Run: bash setup_termux.sh
# ============================================================

set -e

echo "╔══════════════════════════════════════════╗"
echo "║   Hody-Telepro — Termux Setup            ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ─── Step 1: Update Termux ─────────────────────────────────
echo "🔄 [1/6] Updating Termux..."
pkg update -y 2>/dev/null
pkg upgrade -y 2>/dev/null

# ─── Step 2: Install system dependencies ───────────────────
echo "📦 [2/6] Installing system packages..."
pkg install -y python python-pip clang make openssl libffi 2>/dev/null

# ─── Step 3: Upgrade pip ───────────────────────────────────
echo "📈 [3/6] Upgrading pip..."
pip install --upgrade pip setuptools wheel 2>/dev/null

# ─── Step 4: Install build tools ───────────────────────────
echo "🔨 [4/6] Installing build tools..."
pip install build twine 2>/dev/null

# ─── Step 5: Install hody-telepro ──────────────────────────
echo "📥 [5/6] Installing hody-telepro..."
pip install hody-telepro 2>/dev/null || echo "   ⚠️  Will be available after PyPI publish"

# ─── Step 6: Install CLI tool ──────────────────────────────
echo "🛠️  [6/6] Installing CLI tool..."

cat > ~/hody_tool.sh << 'TOOLEOF'
#!/data/data/com.termux/files/usr/bin/bash
# Hody-Telepro CLI Tool
API_ID=""
API_HASH=""

if [ -f ~/.hody_config ]; then
    source ~/.hody_config
fi

usage() {
    echo "Usage: hody_tool.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  config <api_id> <api_hash>  Set credentials"
    echo "  inspect <@username>         Inspect entity"
    echo "  phone <number>              Phone lookup"
    echo "  estimate <id>               Estimate creation date"
    echo "  batch <@user1> <@user2>...  Batch inspection"
}

cmd_config() {
    echo "API_ID=$1" > ~/.hody_config
    echo "API_HASH=$2" >> ~/.hody_config
    chmod 600 ~/.hody_config
    echo "✅ Credentials saved"
}

cmd_inspect() {
    [ -z "$API_ID" ] && { echo "❌ Run 'hody_tool.sh config' first"; exit 1; }
    python3 -c "
import asyncio, sys
from hody_telepro import HodyClient

async def main():
    async with HodyClient('termux', api_id=$API_ID, api_hash='$API_HASH') as client:
        r = await client.inspect('$1')
        e = r.entity
        print(f'👤 {e.full_name}')
        print(f'   Type: {e.entity_type.value}')
        print(f'   ID: {e.user_id}')
        print(f'   Username: @{e.username or \"N/A\"}')
        print(f'   Verified: {\"✓\" if e.is_verified else \"✗\"}')
        print(f'   Premium: {\"✓\" if e.is_premium else \"✗\"}')
        print(f'   Time: {r.inspection_time_ms:.0f}ms')
        if e.account_estimate:
            a = e.account_estimate
            print(f'   Created: {a.estimated_month} {a.estimated_year}')
            print(f'   Confidence: {a.confidence:.0%}')

asyncio.run(main())
"
}

cmd_phone() {
    [ -z "$API_ID" ] && { echo "❌ Run 'hody_tool.sh config' first"; exit 1; }
    python3 -c "
import asyncio
from hody_telepro import HodyClient
async def main():
    async with HodyClient('termux', api_id=$API_ID, api_hash='$API_HASH') as client:
        r = await client.lookup_phone('$1')
        print(f'📱 Phone: {r.phone_number}')
        print(f'   ID: {r.user_id}')
        print(f'   Name: {r.full_name}')
        print(f'   Username: @{r.username or \"N/A\"}')
asyncio.run(main())
"
}

cmd_estimate() {
    python3 -c "
from hody_telepro.algorithms import AccountCreationEstimator
r = AccountCreationEstimator().estimate($1)
print(f'📅 ID: $1')
print(f'   Estimated: {r.estimated_month} {r.estimated_year}')
print(f'   Confidence: {r.confidence:.0%}')
"
}

cmd_batch() {
    [ -z "$API_ID" ] && { echo "❌ Run 'hody_tool.sh config' first"; exit 1; }
    TARGETS="$*"
    python3 -c "
import asyncio, sys
from hody_telepro import HodyClient
from hody_telepro.exporters import JSONExporter

async def main():
    targets = sys.argv[1:]
    async with HodyClient('termux', api_id=$API_ID, api_hash='$API_HASH') as client:
        results = await client.inspect_batch(targets)
        for r in results:
            e = r.entity
            print(f'  ✓ {e.full_name} ({e.entity_type.value})')
        JSONExporter().export_batch(results, 'batch_results.json')
        print(f'\n📁 Saved: batch_results.json')

asyncio.run(main())
" $TARGETS
}

case "$1" in
    config)   cmd_config "$2" "$3" ;;
    inspect)  cmd_inspect "$2" ;;
    phone)    cmd_phone "$2" ;;
    estimate) cmd_estimate "$2" ;;
    batch)    cmd_batch "${@:2}" ;;
    *)        usage ;;
esac
TOOLEOF

chmod +x ~/hody_tool.sh

# Add to PATH
if ! grep -q "hody_tool" ~/.bashrc 2>/dev/null; then
    echo "" >> ~/.bashrc
    echo "# Hody-Telepro CLI" >> ~/.bashrc
    echo "export PATH=\$HOME:\$PATH" >> ~/.bashrc
    echo "alias hody=~/hody_tool.sh" >> ~/.bashrc
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   ✅ Setup Complete!                     ║"
echo "╠══════════════════════════════════════════╣"
echo "║                                          ║"
echo "║   Usage:                                 ║"
echo "║     hody config <api_id> <api_hash>     ║"
echo "║     hody inspect @telegram              ║"
echo "║     hody phone +1234567890              ║"
echo "║     hody estimate 12345                 ║"
echo "║     hody batch @telegram @durov         ║"
echo "║                                          ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# Test
python3 -c "
try:
    from hody_telepro import HodyClient
    from hody_telepro.algorithms import AccountCreationEstimator
    print('✅ hody-telepro is ready to use!')
    est = AccountCreationEstimator()
    r = est.estimate(12345)
    print(f'   Test estimate: Account 12345 → {r.estimated_month} {r.estimated_year}')
except ImportError:
    print('⚠️  hody-telepro not yet on PyPI. Install from source:')
    print('   pip install path/to/hody_telepro-1.0.0-py3-none-any.whl')
"
