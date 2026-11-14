# Ders 02 — Pod Security Standards: Privileged vs Restricted

## Hedef

Kubernetes Pod Security Admission'ın riskli Pod ayarlarına neden itiraz ettiğini uygulamayla görmek; aynı işlevi güvenli bir Pod ile sağlamak.

## 1. Önce YAML'ları karşılaştır

`manifests/vulnerable/privileged-pod.yaml` şu sorunları kasıtlı olarak barındırır: `privileged: true`, `hostPID: true`, `hostPath`, token auto-mount, root olmayan kullanıcının zorunlu tutulmaması ve `latest` etiketi.

`manifests/safe/pod.yaml` şu savunmaları içerir: `runAsNonRoot: true`, `seccompProfile.type: RuntimeDefault`, `allowPrivilegeEscalation: false`, `capabilities.drop: [ALL]`, `readOnlyRootFilesystem: true`, tanımlanmış limitler ve ServiceAccount token auto-mount'un kapatılması.

## 2. İnsecure örneğe yalnızca server dry-run uygula

```bash
kubectl --context kind-kubesec-training apply --dry-run=server \
  -f manifests/vulnerable/privileged-pod.yaml
```

**Beklenen:** `restricted` Pod Security standardının ihlal edildiğini belirten bir **Forbidden/violates PodSecurity** hatası. Bu komut kaynak oluşturmaz.

> Bu örneği gerçek cluster'da veya `restricted` olmayan namespace'te normal `kubectl apply` ile çalıştırma.

## 3. Aynı kontrolü güvenli örnekle yap

```bash
kubectl --context kind-kubesec-training apply --dry-run=server \
  -f manifests/safe/pod.yaml
```

**Beklenen:** `pod/secure-pod configured (server dry run)` benzeri bir başarı çıktısı. Mevcut Pod varsa sunucunun durumuna göre ifade değişebilir.

## 4. Neden önemli?

- **Privileged:** Container'ın host çekirdeğine erişim imkânlarını genişletir.
- **hostPath:** Düğüm dosya sisteminden bir yolu Pod'a bağlayabilir.
- **allowPrivilegeEscalation:** Sürecin mevcut ayrıcalıklarının ötesine çıkmasını sınırlayan bir ayardır.
- **Seccomp:** System call yüzeyini azaltır.
- **Capabilities:** Linux kernel yetkilerini daraltır.
- **runAsNonRoot:** Sürecin root kullanıcı olarak başlamamasını hedefler.

## 5. Alıştırma

Güvenli Pod'un `securityContext` bölümünden yalnızca `allowPrivilegeEscalation: false` satırını **ayrı bir kopyada** kaldır, tekrar `--dry-run=server` ile dene. Sonra satırı geri ekleyip ret nedeninin ortadan kalktığını doğrula. Özgün dosyayı bozma.

## 6. İleri kontrol

KubeGuard'da her bulgu için ayrı kod bulunur: `KG001`, `KG002`, `KG003`, `KG004`, `KG005`, `KG010`. Ancak KubeGuard, Kubernetes API'sinin yerini almaz.

Sonraki: [Ders 03 — RBAC](03-rbac.md).
