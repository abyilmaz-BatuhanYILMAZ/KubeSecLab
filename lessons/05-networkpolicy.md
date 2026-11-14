# Ders 05 — NetworkPolicy: default deny + yalnızca izinli istemci

## Amaç ve önkoşullar

Bir ağ politikasının YAML'da bulunması ile **gerçekten uygulanması** arasındaki farkı göstermek. Bu ders, yalnızca bir Pod'un API tarafından kabul edilmesini değil, **gerçek Pod-to-Pod HTTP trafiğini** ölçer.

**Önemli:** Standart `kindnet` NetworkPolicy kurallarını uygulamaz. Bu ders için **Calico CNI** ile ayrı bir disposable cluster gerekir. Resmî [Kubernetes NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/) ve [Calico kind kurulumu](https://docs.tigera.io/calico/latest/getting-started/kubernetes/kind) başvurularına bak.

## 1. Cluster'ı kur

Docker, `kind`, `kubectl` ve `curl` gerekir. Sadece `kubesec-net` isimli yeni cluster kurulur. Kurulum mevcut aynı isimli cluster'ı değiştirmeyi reddeder.

```bash
bash scripts/setup-networkpolicy.sh
kubectl --context kind-kubesec-net get nodes
kubectl --context kind-kubesec-net get pods -A
```

Kurulum, `config/kind-calico.yaml` üzerinden kind'in varsayılan CNI'sini kapatır, sürümü sabitlenmiş **Calico v3.33.0** manifestini kurar ve node'ların `Ready` durumunu bekler. Bileşenler ilk defa indirilirken internet gerekir. Bu kurulum dış kaynaktan çalıştırılan Kubernetes manifestlerini içerdiğinden kullanılmadan önce incelenmelidir.

## 2. Politika öncesi bağlantı testi

`manifests/networkpolicy/workloads.yaml` şu üç Pod'u ve bir Service'i kurar:

- `web`: HTTP sunucusu, `web:8080`
- `client-approved`: `access=approved` etiketli istemci
- `client-other`: `access=other` etiketli istemci

Başlangıçta ağ kısıtlaması yoktur; ikisi de aynı servise erişmelidir:

```bash
kubectl --context kind-kubesec-net -n kubesec-net exec client-approved -- wget -qO- -T 3 http://web:8080
kubectl --context kind-kubesec-net -n kubesec-net exec client-other -- wget -qO- -T 3 http://web:8080
```

**Beklenen:** Her ikisi de `hello-kubesec` döndürür.

## 3. Default-deny ve dar kapsamlı allow ekle

```bash
kubectl --context kind-kubesec-net apply -f manifests/networkpolicy/default-deny-ingress.yaml
kubectl --context kind-kubesec-net apply -f manifests/networkpolicy/allow-approved-to-web.yaml
kubectl --context kind-kubesec-net -n kubesec-net describe networkpolicy
```

İlk politika tüm Pod'lar için inbound bağlantıyı varsayılan olarak reddeder. İkinci politika, yalnızca aynı namespace'te `access=approved` etiketli Pod'lardan `app=web` Pod'una TCP/8080 girişine izin verir. NetworkPolicy kuralları seçilen Pod'a göre **toplanarak** izin verir; sırayla birbirini geçersiz kılmaz.

## 4. Gerçek davranışı doğrula

```bash
bash scripts/verify-networkpolicy.sh
```

**Beklenen:** Politika öncesi her iki istemci bağlanır; politika sonrası `client-approved` bağlanır, `client-other` bağlantısı başarısız olur. Betik, Calico kuralının uygulanmasına zaman tanıyarak her iki durumu ayrı test eder.

**Hata analizi:** İki istemci de erişebiliyorsa CNI'nın gerçekten politika uyguladığını doğrula. İkisi de erişemiyorsa etiketleri, `policyTypes`, portu ve sunucu sağlığını kontrol et. DNS ve egress ayrıca ele alınmalıdır; bu ders **ingress** politikasına odaklanır.

## 5. Güvensiz karşılaştırma

`manifests/vulnerable/allow-all-networkpolicy.yaml` hem ingress hem egress için açık kural içerir ve yalnızca offline KubeGuard taraması için vardır. Uygulama:

```bash
# KubeGuard kardeş proje dizininde kuruluysa:
python -m kubeguard scan manifests/vulnerable/allow-all-networkpolicy.yaml --fail-on NONE
```

**Güvensiz manifesti apply etme.** Bu dosya yalnızca kuralın neden tehlikeli olduğunu anlamak için.

## 6. Temizleme

```bash
kind delete cluster --name kubesec-net
```

Test ve değişiklikler yalnızca `kind-kubesec-net` context'inde gerçekleştirilir. Ağ egress politikalarını ekleyeceğin ileriki derslerde DNS erişimi için ayrı izinleri düşün.

**Kanıt:** [GitHub Actions canlı Calico testi](../.github/workflows/networkpolicy-integration.yml).
