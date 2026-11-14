# KubeSecLab — Kubernetes Security, Step by Step

**Practical Kubernetes security exercises in an isolated local `kind` cluster.** Each lesson teaches a control, demonstrates a deliberately unsafe configuration, fixes it, and verifies the outcome. The learning materials are in Turkish with English terminology so that the labs can be used for both technical training and a public portfolio.

> **Safety:** The insecure manifests are for analysis and **server-side dry-run only**. Do not apply the `manifests/vulnerable/broad-rbac.yaml` file: it grants cluster-wide power. The training cluster is disposable; never use a production kubeconfig/context.

## Öğrenme rotası

| Sıra | Ders | Öğreneceğin şey | Beklenen kanıt |
| --- | --- | --- | --- |
| 01 | [Ortam kurulumu](lessons/01-setup.md) | Docker, kind, kubectl, güvenli namespace | Yerel cluster ve `restricted` etiketleri |
| 02 | [Pod Security](lessons/02-pod-security.md) | `privileged`, seccomp, capability, non-root | Insecure Pod reddedildi / secure Pod kabul edildi |
| 03 | [RBAC ve ServiceAccount](lessons/03-rbac.md) | `Role`, `RoleBinding`, en az yetki ilkesi | Reader get/list yapıyor, delete yapamıyor |
| 04 | [KubeGuard ile denetim](lessons/04-audit.md) | Offline YAML taraması, düzeltme önerisi, JSON/SARIF | Güvensiz YAML bulguları, güvenli YAML temiz |

## Gereksinimler

- Linux, macOS veya Windows + WSL2 üzerinde Docker Engine/Desktop çalışır olmalı.
- [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) ve [kubectl](https://kubernetes.io/docs/tasks/tools/) kurulu olmalı.
- Yerel cluster için yeterli RAM/CPU/disk ve internet bağlantısı (ilk imaj çekimleri için) bulunmalı.
- KubeGuard denetimlerini çalıştırmak için Python 3.11+ ve PyYAML 6 gereklidir.

Bu repo Kubernetes'i veya Docker'ı bilgisayarına otomatik yüklemez. Kurulum seçenekleri işletim sistemine göre değişir.

## Hızlı başlangıç (yerel ve izole)

```bash
# Proje kökünden:
bash scripts/setup.sh
kubectl --context kind-kubesec-training get pods -n kubesec-training
bash scripts/verify.sh
```

`setup.sh` adlı `kubesec-training` kind cluster'ını oluşturur, restricted namespace'i ve yalnızca güvenli manifestleri uygular. `verify.sh`, RBAC izinlerini ve insecure Pod'un **server-side dry-run ile** reddedilmesini sınar. Bu betikler bu ortamda gerçek bir kind cluster üzerinde henüz çalıştırılmadı; komutları kendi yerel ortamında doğrula.

### Beklenen ayrım

```bash
# Secure example — should be admitted in the restricted namespace
kubectl --context kind-kubesec-training apply --dry-run=server -f manifests/safe/pod.yaml

# Deliberately insecure example — expected to be rejected by Pod Security Admission
kubectl --context kind-kubesec-training apply --dry-run=server -f manifests/vulnerable/privileged-pod.yaml
```

İkinci komutun başarısız olması **beklenen güvenlik davranışıdır**. Yalnızca bu ayrım test için yeterli değildir: özellikle RBAC ve yapılandırma eksiklerini offline denetle.

## KubeGuard ile denetim

**KubeGuard** ayrı bir offline Python projesidir. Onun paketini `KubeSecLab` ile yan yana bir dizine çıkardıysan:

```bash
cd ../KubeGuard
python -m pip install -e .
python -m kubeguard scan ../KubeSecLab/manifests/safe/
python -m kubeguard scan ../KubeSecLab/manifests/vulnerable/ --format json --fail-on NONE
```

Ekrandaki bulguların özellikle `KG001`, `KG010`, `KG012`, `KG013` kodlarına nasıl eşleştiğini [4. derste](lessons/04-audit.md) inceleyebilirsin.

## Temizleme

```bash
bash scripts/cleanup.sh
```

Bu komut yalnızca `kubesec-training` adlı **yerel kind cluster'ını** siler. Başka bir cluster'a karşı cleanup çalıştırmaz.

## Kapsam ve sınırlamalar

- Bu bir **eğitim laboratuvarıdır**, gerçek bir Kubernetes cluster'ını otomatik zafiyet taramasından geçirme aracı değildir.
- Varsayılan örnekler yerel Kind cluster kullanır; laboratuvarı bulut veya kurum ağına taşımayın.
- `kind`/Docker/kubectl ikililerinin çalışması ve imaj erişimi makinede ayrıca doğrulanmalıdır.
- `KubeGuard`, YAML üzerinde offline kurallar uygular; actual admission behavior Kubernetes sürümüne ve cluster ayarlarına bağlıdır.
- İkinci projede henüz Helm, Argo CD, NetworkPolicy CNI testi, Falco/eBPF veya gerçek cluster güvenlik kontrolleri bulunmuyor. Bunlar ileride ayrı modüller olabilir.

## Referanslar

- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes Pod Security Admission Tutorial](https://kubernetes.io/docs/tutorials/security/ns-level-pss/)
- [RBAC Good Practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)

**License:** MIT. A teaching resource with intentional vulnerabilities for analysis; not a production deployment template.


## İleri düzey laboratuvarlar

| Ders | Konu | Canlı test kanıtı |
| --- | --- | --- |
| [05 — NetworkPolicy ve Calico](lessons/05-networkpolicy.md) | Default deny, podSelector ile allow, gerçek HTTP erişim testi | [Canlı NetworkPolicy workflow](.github/workflows/networkpolicy-integration.yml) |
| [06 — Gelişmiş RBAC](lessons/06-advanced-rbac.md) | resourceNames, escalate/bind/impersonate, tehlikeli ClusterRoleBinding | [Canlı kind/RBAC workflow](.github/workflows/kind-integration.yml) |

Kubernetes kaynaklarının yalnızca kabul edilmesi, ağ politikalarının gerçekten **uygulandığını** göstermez. NetworkPolicy dersi Calico CNI ile ayrı bir disposable cluster açar ve onaylı/onaysız istemcilerin **gerçek trafik sonucunu** sınar.

```bash
bash scripts/setup-networkpolicy.sh
bash scripts/verify-networkpolicy.sh
kind delete cluster --name kubesec-net
```

Hatalı `manifests/vulnerable/` örnekleri **offline-only** kalmalıdır. Live CI yalnızca `manifests/safe/` ve ağ dersinin açıkça güvenli çalışma manifestlerini uygular.
