# Hody-Telepro — دليل Termux الشامل

> دليل كامل للنشر على PyPI والاستخدام الذكي عبر Termux على هاتفك

---

## 📱 الجزء الأول: إعداد Termux

### 1. تثبيت Termux من F-Droid (ليس Google Play)

```
https://f-droid.org/packages/com.termux/
```

### 2. تحديث الحزم

```bash
pkg update && pkg upgrade -y
```

### 3. تثبيت الحزم الأساسية

```bash
pkg install -y python python-pip clang make openssl libffi
```

### 4. إعداد Python

```bash
# تثبيت pip
pip install --upgrade pip setuptools wheel

# تثبيت الحزم المطلوبة للبناء
pip install build twine tgcrypto
```

---

## 🚀 الجزء الثاني: النشر على PyPI

### الطريقة 1: عبر Termux مباشرة

```bash
# 1. نقل ملفات المشروع إلى الهاتف
#    يمكنك استخدام rsync أو scp أو تحميل ZIP

# 2. فك الضغط
unzip hody-telepro-complete.zip
cd hody-telepro

# 3. تثبيت أدوات البناء
pip install build twine

# 4. بناء الحزمة
python3 -m build

# 5. النشر على PyPI (سيطلب التوكن)
twine upload dist/*
```

### إدخال التوكن:
عندما يطلب `twine` بيانات الدخول:
```
Enter your username: __token__
Enter your password: pypi-AgEIcHlwaS5vcmcCJGY0Y...
```

---

## 📥 الجزء الثالث: تثبيت المكتبة من PyPI

بعد النشر بنجاح:

```bash
# تثبيت المكتبة من PyPI
pip install hody-telepro
```

---

## 🧠 الجزء الرابع: الاستخدام الذكي عبر Termux

### سكربت الاستخدام السريع

```bash
cat > ~/hody_inspect.py << 'PYEOF'
import asyncio
import sys
from hody_telepro import HodyClient
from hody_telepro.algorithms import AccountCreationEstimator
from hody_telepro.exporters import JSONExporter, HTMLReporter

async def main():
    if len(sys.argv) < 3:
        print("Usage: python hody_inspect.py <api_id> <api_hash> <target>")
        sys.exit(1)

    api_id = int(sys.argv[1])
    api_hash = sys.argv[2]
    target = sys.argv[3]

    async with HodyClient("termux_session", api_id=api_id, api_hash=api_hash) as client:
        result = await client.inspect(target)
        
        print("=" * 50)
        print(f"📊 Result for: {target}")
        print("=" * 50)
        print(f"  Name:       {result.entity.full_name}")
        print(f"  Type:       {result.entity.entity_type.value}")
        print(f"  Username:   {result.entity.username or 'N/A'}")
        print(f"  ID:         {result.entity.user_id}")
        print(f"  Verified:   {'Yes' if result.entity.is_verified else 'No'}")
        print(f"  Premium:    {'Yes' if result.entity.is_premium else 'No'}")
        print(f"  Bot:        {'Yes' if result.entity.is_bot else 'No'}")
        print(f"  Time:       {result.inspection_time_ms:.2f}ms")
        
        if result.entity.account_estimate:
            est = result.entity.account_estimate
            print(f"  Est. Date:  {est.estimated_month} {est.estimated_year}")
            print(f"  Confidence: {est.confidence:.0%}")
        
        print("=" * 50)
        
        # Save to JSON
        json_str = JSONExporter().export_single(result)
        with open(f"{target.lstrip('@')}_result.json", "w") as f:
            f.write(json_str)
        print(f"📁 Saved: {target.lstrip('@')}_result.json")

asyncio.run(main())
PYEOF
```

### استخدام السكربت:

```bash
python3 hody_inspect.py 12345 "your_hash" @telegram
```

---

## 🔧 الجزء الخامس: سكربت CLI ذكي

```bash
cat > ~/hody_tool.sh << 'SHEOF'
#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# Hody-Telepro CLI Tool for Termux
# ============================================================

API_ID=""
API_HASH=""

# Load credentials from config
if [ -f ~/.hody_config ]; then
    source ~/.hody_config
fi

usage() {
    echo "Usage: hody_tool.sh <command> [options]"
    echo ""
    echo "Commands:"
    echo "  config    Set API credentials"
    echo "  inspect   Inspect an entity"
    echo "  phone     Lookup by phone number"
    echo "  estimate  Estimate account creation date"
    echo "  batch     Batch inspection"
    echo ""
    echo "Examples:"
    echo "  hody_tool.sh config 12345 your_hash"
    echo "  hody_tool.sh inspect @telegram"
    echo "  hody_tool.sh phone +1234567890"
    echo "  hody_tool.sh estimate 12345"
    echo "  hody_tool.sh batch @telegram @durov @BotFather"
}

cmd_config() {
    echo "API_ID=$1" > ~/.hody_config
    echo "API_HASH=$2" >> ~/.hody_config
    chmod 600 ~/.hody_config
    echo "✅ Credentials saved to ~/.hody_config"
}

cmd_inspect() {
    if [ -z "$API_ID" ]; then
        echo "❌ Run 'hody_tool.sh config <api_id> <api_hash>' first"
        exit 1
    fi
    
    python3 -c "
import asyncio, sys
from hody_telepro import HodyClient

async def main():
    async with HodyClient('termux', api_id=$API_ID, api_hash='$API_HASH') as client:
        result = await client.inspect('$1')
        e = result.entity
        print(f'👤 {e.full_name}')
        print(f'   Type: {e.entity_type.value}')
        print(f'   ID: {e.user_id}')
        print(f'   Username: @{e.username or \"N/A\"}')
        print(f'   Verified: {\"✓\" if e.is_verified else \"✗\"}')
        print(f'   Premium: {\"✓\" if e.is_premium else \"✗\"}')
        print(f'   Time: {result.inspection_time_ms:.0f}ms')
        if e.account_estimate:
            print(f'   Created: {e.account_estimate.estimated_month} {e.account_estimate.estimated_year}')

asyncio.run(main())
"
}

cmd_phone() {
    python3 -c "
import asyncio
from hody_telepro import HodyClient

async def main():
    async with HodyClient('termux', api_id=$API_ID, api_hash='$API_HASH') as client:
        result = await client.lookup_phone('$1')
        print(f'📱 Phone: {result.phone_number}')
        print(f'   User ID: {result.user_id}')
        print(f'   Name: {result.full_name}')

asyncio.run(main())
"
}

cmd_estimate() {
    python3 -c "
from hody_telepro.algorithms import AccountCreationEstimator
estimator = AccountCreationEstimator()
result = estimator.estimate($1)
print(f'📅 Account ID: $1')
print(f'   Estimated: {result.estimated_month} {result.estimated_year}')
print(f'   Confidence: {result.confidence:.0%}')
"
}

cmd_batch() {
    shift
    targets="$@"
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
            print(f'✓ {e.full_name} ({e.entity_type.value})')
        JSONExporter().export_batch(results, 'batch_results.json')
        print(f'\n📁 Saved batch_results.json')

asyncio.run(main())
" $targets
}

case "$1" in
    config)   cmd_config "$2" "$3" ;;
    inspect)  cmd_inspect "$2" ;;
    phone)    cmd_phone "$2" ;;
    estimate) cmd_estimate "$2" ;;
    batch)    cmd_batch "${@:2}" ;;
    *)        usage ;;
esac
SHEOF

chmod +x ~/hody_tool.sh
echo "✅ hody_tool.sh installed to ~/hody_tool.sh"
```

### استخدام الأداة:

```bash
# حفظ التوكنات
hody_tool.sh config 12345 your_api_hash

# فحص مستخدم
hody_tool.sh inspect @telegram

# البحث عن رقم
hody_tool.sh phone +1234567890

# تقدير تاريخ الحساب
hody_tool.sh estimate 12345

# فحص جماعي
hody_tool.sh batch @telegram @durov @BotFather
```

---

## 🎯 الجزء السادس: سكربت التثبيت الآلي الكامل

```bash
cat > ~/install_hody.sh << 'AUTOEOF'
#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
# Hody-Telepro — Auto Install Script for Termux
# Run: bash install_hody.sh
# ============================================================

echo "🔧 Setting up Hody-Telepro on Termux..."
echo ""

# Update packages
echo "[1/5] Updating packages..."
pkg update -y > /dev/null 2>&1
pkg upgrade -y > /dev/null 2>&1

# Install dependencies
echo "[2/5] Installing dependencies..."
pkg install -y python clang make openssl libffi > /dev/null 2>&1

# Upgrade pip
echo "[3/5] Upgrading pip..."
pip install --upgrade pip setuptools wheel > /dev/null 2>&1

# Install hody-telepro
echo "[4/5] Installing hody-telepro..."
pip install hody-telepro > /dev/null 2>&1

# Test installation
echo "[5/5] Testing installation..."
python3 -c "import hody_telepro; print(f'✅ hody-telepro v{hody_telepro.__version__} installed!')"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "Usage:"
echo "  from hody_telepro import HodyClient"
echo "  # See PUBLISHING_GUIDE.md for full documentation"
AUTOEOF

chmod +x ~/install_hody.sh
```

---

## 📋 الجزء السابع: الأوامر الجاهزة (Copy & Paste)

### 🟢 إعداد Termux (مرة واحدة):

```bash
pkg update && pkg upgrade -y
pkg install -y python python-pip clang make openssl libffi
pip install --upgrade pip setuptools wheel build twine
```

### 🟢 بناء ونشر الحزمة:

```bash
cd hody-telepro
python3 -m build
twine upload dist/*
# Username: __token__
# Password: [paste your token here]
```

### 🟢 تثبيت المكتبة:

```bash
pip install hody-telepro
```

### 🟢 اختبار سريع:

```bash
python3 -c "
from hody_telepro.algorithms import AccountCreationEstimator
est = AccountCreationEstimator()
r = est.estimate(12345)
print(f'Account 12345: {r.estimated_month} {r.estimated_year} (confidence: {r.confidence:.0%})')
"
```

### 🟢 سكربت فحص كامل:

```bash
cat > ~/hody_check.py << 'EOF'
import asyncio, sys
from hody_telepro import HodyClient
from hody_telepro.exporters import JSONExporter

async def check(target):
    async with HodyClient("session", api_id=int(sys.argv[2]), api_hash=sys.argv[3]) as client:
        result = await client.inspect(target)
        e = result.entity
        print(f"{'='*40}")
        print(f" Target: {target}")
        print(f" Name:   {e.full_name}")
        print(f" Type:   {e.entity_type.value}")
        print(f" ID:     {e.user_id}")
        print(f" Username: @{e.username or 'N/A'}")
        print(f" Verified: {'Yes' if e.is_verified else 'No'}")
        print(f" Premium:  {'Yes' if e.is_premium else 'No'}")
        print(f" Time:     {result.inspection_time_ms:.1f}ms")
        if e.account_estimate:
            a = e.account_estimate
            print(f" Created:  {a.estimated_month} {a.estimated_year}")
            print(f" Conf:     {a.confidence:.0%}")
        print(f"{'='*40}")
        JSONExporter().export_single(result, f"{target.lstrip('@')}.json")
        print(f" Saved: {target.lstrip('@')}.json")

asyncio.run(check(sys.argv[1]))
EOF
```

### استخدام السكربت:

```bash
python3 ~/hody_check.py @telegram 12345 "your_hash"
```

---

## 🔒 الجزء الثامن: الأمان على Termux

```bash
# حماية بيانات الدخول
chmod 600 ~/.hody_config

# لا تضع التوكنات في السكربت مباشرة
# استخدم متغيرات البيئة:
export API_ID=12345
export API_HASH="your_hash"
```

---

## ⚡ الجزء التاسع: أوامر سريعة جاهزة

```bash
# ─── فحص مستخدم ─────────────────────────────────────────────
python3 -c "
import asyncio
from hody_telepro import HodyClient
async def m():
    async with HodyClient('s', api_id=12345, api_hash='HASH') as c:
        r = await c.inspect('@telegram')
        print(r.entity.full_name, '|', r.entity.entity_type.value)
asyncio.run(m())
"

# ─── تقدير تاريخ حساب ──────────────────────────────────────
python3 -c "
from hody_telepro.algorithms import AccountCreationEstimator
r = AccountCreationEstimator().estimate(100000)
print(f'{r.estimated_month} {r.estimated_year} ({r.confidence:.0%})')
"

# ─── فحص جماعي + تصدير ────────────────────────────────────
python3 -c "
import asyncio
from hody_telepro import HodyClient
from hody_telepro.exporters import JSONExporter
async def m():
    async with HodyClient('s', api_id=12345, api_hash='HASH') as c:
        results = await c.inspect_batch(['@telegram','@durov','@BotFather'])
        JSONExporter().export_batch(results, 'results.json')
        print(f'Exported {len(results)} results')
asyncio.run(m())
"
```

---

## 📌 ملخص سريع

| الخطوة | الأمر |
|--------|-------|
| تحديث Termux | `pkg update && pkg upgrade -y` |
| تثبيت المكتبة | `pip install hody-telepro` |
| فحص مستخدم | `hody_tool.sh inspect @telegram` |
| بحث هاتف | `hody_tool.sh phone +1234567890` |
| تقدير تاريخ | `hody_tool.sh estimate 12345` |
| فحص جماعي | `hody_tool.sh batch @telegram @durov` |
| نشر على PyPI | `twine upload dist/*` |

---

<div align="center">

**Hody-Telepro on Termux** — Full power on your phone! 📱🚀

</div>
