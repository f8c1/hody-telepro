# Hody-Telepro — دليل النشر على PyPI

> هذا الدليل يشرح خطوة بخطوة كيفية نشر مكتبة Hody-Telepro على PyPI ليتمكن أي شخص من تثبيتها عبر `pip install hody-telepro`

---

## المتطلبات المسبقة

| المتطلب | الأمر |
|---------|-------|
| Python 3.9+ | `python3 --version` |
| حساب PyPI | [https://pypi.org/account/register/](https://pypi.org/account/register/) |
| حساب TestPyPI (للتجربة) | [https://test.pypi.org/account/register/](https://test.pypi.org/account/register/) |

---

## الخطوة 1: إنشاء حساب على PyPI

1. اذهب إلى [https://pypi.org/account/register/](https://pypi.org/account/register/)
2. سجل حساب جديد
3. فعّل التوثيق الثنائي (2FA) — **مطلوب للنشر**
4. احصل على **API Token** من: [https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)

---

## الخطوة 2: حفظ بيانات الاعتماد (Token)

### الطريقة أ: ملف ~/.pypirc (موصى به)

```bash
cat > ~/.pypirc << 'EOF'
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmcCJGY0Y...  # ضع التوكن هنا
EOF

chmod 600 ~/.pypirc
```

### الطريقة ب: تمرير التوكن مباشرة

```bash
twine upload dist/* -u __token__ -p pypi-AgEIcHlwaS5vcmcCJGY0Y...
```

### الطريقة ج: استخدام متغيرات البيئة

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcHlwaS5vcmcCJGY0Y...
```

---

## الخطوة 3: تثبيت أدوات النشر

```bash
# تثبيت الأدوات المطلوبة
pip install --upgrade build setuptools wheel twine

# أو عبر uv (أسرع)
# uv pip install build setuptools wheel twine
```

---

## الخطوة 4: بناء الحزمة

```bash
cd hody-telepro

# تنظيف الملفات القديمة
rm -rf build/ dist/ src/hody_telepro.egg-info/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# بناء الحزمة (ينتج .whl و .tar.gz)
python3 -m build
```

**المخرجات:**
```
dist/
├── hody_telepro-1.0.0-py3-none-any.whl   ← Wheel package
└── hody_telepro-1.0.0.tar.gz              ← Source distribution
```

---

## الخطوة 5: اختبار الحزمة (موصى به)

### نشر على TestPyPI أولاً:

```bash
# بناء
python3 -m build

# رفع على TestPyPI
twine upload --repository testpypi dist/*

# تثبيت من TestPyPI للتأكد
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ hody-telepro

# اختبار الاستيراد
python3 -c "from hody_telepro import HodyClient; print('✅ Works!')"
```

---

## الخطوة 6: النشر على PyPI الحقيقي

```bash
# رفع على PyPI
twine upload dist/*

# أو عبر سكربت النشر الآلي
./publish.sh

# أو للتجربة أولاً
./publish.sh test
```

---

## الخطوة 7: التحقق من النشر

```bash
# انتظار 5-10 دقائق ثم التحقق
pip search hody-telepro  # (deprecated)

# بدلاً من ذلك، افتح:
# https://pypi.org/project/hody-telepro/

# أو ثبّت وتحقق:
pip install hody-telepro
python3 -c "import hody_telepro; print(hody_telepro.__version__)"
```

---

## سكربت النشر الآلي

الملف `publish.sh` المرفق ينفذ كل الخطوات تلقائياً:

```bash
# النشر الكامل
./publish.sh

# التجربة على TestPyPI فقط
./publish.sh test

# بناء فقط بدون رفع
./publish.sh build-only
```

---

## إدارة الإصدارات

عند إصدار نسخة جديدة:

### 1. تحديث الإصدار في `pyproject.toml`:
```toml
version = "1.1.0"  # بدل "1.0.0"
```

### 2. تحديث ملف `CHANGELOG.md` (اختياري)

### 3. إعادة البناء والنشر:
```bash
rm -rf dist/ build/ src/hody_telepro.egg-info/
python3 -m build
twine upload dist/*
```

---

## جدول الإصدارات المقترح (Semantic Versioning)

| النوع | النمط | مثال | متى نستخدم |
|-------|-------|------|-----------|
| Major | `X.0.0` | `2.0.0` | تغييرات غير متوافقة مع الإصدارات السابقة |
| Minor | `X.Y.0` | `1.1.0` | إضافة ميزات جديدة |
| Patch | `X.Y.Z` | `1.0.1` | إصلاح أخطاء |

---

## حل المشاكل الشائعة

### ❌ خطأ: "File already exists"
```bash
# الحزمة بهذا الاسم والإصدار موجودة، زد الإصدار
# pyproject.toml → version = "1.0.1"
```

### ❌ خطأ: "HTTPError: 403 Forbidden"
```bash
# تأكد من:
# 1. التوكن صحيح
# 2. حسابك مفعل (2FA)
# 3. اسم الحزمة hody-telepro غير محجوز
```

### ❌ خطأ: "tgcrypto build failed"
```bash
# على Linux/Mac:
sudo apt install python3-dev gcc  # Linux
# على Windows: تثبيت Visual Studio Build Tools

# أو بدون tgcrypto (أبطأ لكن يعمل):
pip install hody-telepro --no-deps
pip install pyrogram
```

---

## ما يحدث بعد النشر

```
المستخدم يكتب:
  pip install hody-telepro

         ↓

PyPI يرسل الحزمة:
  dist/hody_telepro-1.0.0-py3-none-any.whl

         ↓

pip يثبّت المكتبة:
  /usr/local/lib/python3.x/site-packages/hody_telepro/

         ↓

المستخدم يستخدمها:
  from hody_telepro import HodyClient
  async with HodyClient("session", api_id=..., api_hash="...") as client:
      result = await client.inspect("@telegram")
      print(result.entity.full_name)
```

---

## روابط مفيدة

| الرابط | الوصف |
|--------|-------|
| [PyPI](https://pypi.org/project/hody-telepro/) | صفحة الحزمة على PyPI |
| [TestPyPI](https://test.pypi.org/project/hody-telepro/) | صفحة الاختبار |
| [Twine Documentation](https://twine.readthedocs.io/) | دليل Twine |
| [Packaging Guide](https://packaging.python.org/) | دليل حزم Python الرسمي |
| [PEP 621](https://peps.python.org/pep-0621/) | معيار pyproject.toml |

---

<div align="center">

**Hody-Telepro v1.0.0** — Ready to publish! 🚀

</div>
