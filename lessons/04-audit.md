# Ders 04 — KubeGuard ile YAML Güvenlik Denetimi

## Hedef

Kubernetes cluster'a bağlanmadan manifest dosyalarını incelemek, bulguları önem sırasına koymak, düzeltmek ve tekrar taramak.

## 1. Aracı yükle

KubeGuard'ın bağımsız paketini KubeSecLab ile yan yana çıkardıysan:

```bash
cd ../KubeGuard
python -m pip install -e .
python -m unittest discover -s tests -v
```

## 2. Güvenli manifestleri tara

```bash
python -m kubeguard scan ../KubeSecLab/manifests/safe/
```

**Beklenen:** Mevcut 14 KubeGuard kuralı için bulgu yok; ancak bu bir bütüncül güvenlik sertifikası değildir.

## 3. Güvensiz manifestleri tara

```bash
python -m kubeguard scan ../KubeSecLab/manifests/vulnerable/ \
  --format human
```

**Beklenen:** `KG001`, `KG010`, `KG012`, `KG013` gibi yüksek/kritik bulgular; varsayılan eşik nedeniyle exit code 1.

## 4. Makine-okunabilir rapor hazırla

```bash
python -m kubeguard scan ../KubeSecLab/manifests/vulnerable/ \
  --format json --fail-on NONE > kubeguard-results.json
python -m kubeguard scan ../KubeSecLab/manifests/vulnerable/ \
  --format sarif --fail-on NONE > kubeguard-results.sarif
```

- `--fail-on NONE` yalnızca komutun çıkış kodunu değiştirir; riskleri ortadan kaldırmaz.
- SARIF dosyası otomasyon ve code-scanning ekosistemine uyumlu biçimdedir. Dosya satır numarası ilk sürümde yaklaşık gösterilir.
- Bir araç raporu, Kubernetes API ve runtime politika denetiminin yerini almaz.

## 5. Mini proje

İnsecure Pod'un kopyasını ayrı dosyaya al. Bulguların her biri için güvenli seçenek öner, YAML üzerinde düzelt ve tekrar tara. Hangi risklerin Pod Security Admission tarafından, hangilerinin sadece statik denetleyici tarafından yakalandığını karşılaştır.

## 6. Ölçüm / bitirme kriteri

- [ ] Riskli `privileged`, `hostPath`, wildcard RBAC ve `cluster-admin` davranışlarını açıklayabiliyorum.
- [ ] `kubectl auth can-i` ile gerçek yetkiyi kontrol ettim.
- [ ] `restricted` namespace içinde güvenli Pod kabul ve güvensiz Pod ret farkını gözlemledim.
- [ ] KubeGuard bulgularını JSON/SARIF biçiminde dışa aktardım.
- [ ] Yerel `kind` cluster'ını sildim.

Kapatma: `bash scripts/cleanup.sh` (KubeSecLab dizininden).
