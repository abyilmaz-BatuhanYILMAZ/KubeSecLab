# Ders 06 — Gelişmiş RBAC: resourceNames ve ayrıcalık devri

## Hedef

Bir ServiceAccount'a bütün ConfigMap'leri değil, yalnızca tek bir adlandırılmış ConfigMap'i okumak için yetki vermek; `escalate`, `bind`, `impersonate` haklarının neden yüksek risk taşıdığını açıklamak.

## 1. Meşru rol ve bağlamı oluştur

Mevcut `kubesec-training` disposable cluster'ı ve `kubesec-training` namespace'i içinde:

```bash
bash scripts/setup.sh
kubectl --context kind-kubesec-training apply -f manifests/safe/resource-names-rbac.yaml
```

Bu manifestte `audit-reader` ServiceAccount'u, `specific-config-reader` Role ve RoleBinding bulunur. `resourceNames: [approved-config]` ile `verbs: [get]` sınırlandırılmıştır.

## 2. Yetkiyi sunucu tarafında doğrula

```bash
ctx=kind-kubesec-training
sa=system:serviceaccount:kubesec-training:audit-reader
kubectl --context "$ctx" auth can-i get configmaps --resource-name=approved-config --as="$sa" -n kubesec-training
kubectl --context "$ctx" auth can-i get configmaps --resource-name=other-config --as="$sa" -n kubesec-training
kubectl --context "$ctx" auth can-i list configmaps --as="$sa" -n kubesec-training
kubectl --context "$ctx" auth can-i get secrets --as="$sa" -n kubesec-training
```

**Beklenen:** `yes / no / no / no`. `resourceNames`, listeleme gibi koleksiyon operasyonlarında özel dikkat gerektirir; yalnızca hedefteki **get** kullanımını göstermek için uygulanmıştır.

`kubectl auth can-i --as` ile impersonation yapmayı sağlayan yönetici yetkisi gerekir; bu nedenle komutları yalnızca disposable kind yönetici context'inde kullan.

## 3. Özellikle verilmemesi gereken haklar

- **escalate:** Belirli RBAC nesneleri üzerinde, normalde sahip olunmayan yetkileri de içeren kural değişikliklerine kapı açabilir.
- **bind:** Kullanıcının kendi izni dışında geniş yetkiler içeren rolü bağlamasına olanak tanıyabilir.
- **impersonate:** Yetkili kimliklerin yerine işlem yapmaya imkân sağlayabilir.

Ayrıcalıklar kendiliğinden her zaman zafiyet değildir; ancak kurumda olağan ServiceAccount rollerine verilmemelidir. Özellikle `system:authenticated` gibi geniş gruplara yapılan bağlamalar gözden geçirilmelidir.

## 4. Hatalı manifesti çevrimdışı incele

`manifests/vulnerable/escalation-rbac.yaml` kasıtlı olarak tehlikeli bir ClusterRole ve geniş grup binding'i içerir.

```bash
python -m kubeguard scan manifests/vulnerable/escalation-rbac.yaml --fail-on NONE
```

**Beklenen:** KubeGuard `KG015` (escalate/bind/impersonate), `KG016` (Secrets read), `KG020` (geniş grup binding) gibi kontrolleri raporlar.

**Bu dosyayı hiçbir gerçek cluster'a veya eğitim cluster'ına uygulama.**

## 5. Doğrulama ve temizleme

```bash
bash scripts/verify.sh
bash scripts/cleanup.sh
```

## Not

`kubectl auth can-i` gerçek cluster API'sinde yetki kararı verir; KubeGuard'ın statik kuralları ise RBAC yetki grafiğini tam olarak çözümlemez. Aggregated ClusterRole, webhook authorizer, admission politikaları ve rol bağlamaları ayrıca değerlendirilmelidir.
