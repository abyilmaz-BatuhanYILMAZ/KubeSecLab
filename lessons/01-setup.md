# Ders 01 — Yerel Kubernetes Güvenlik Laboratuvarı Kurulumu

## Hedef

Kubernetes'in node, cluster, namespace ve context kavramlarını anlayıp izole `kind` cluster'ını oluşturmak. Bir production cluster yerine tamamen silinebilir yerel ortam kullanmak.

## 1. Ön kontrol

Docker çalışıyor mu?

```bash
docker info
```

Kubernetes istemcisi ve kind kurulu mu?

```bash
kubectl version --client
kind version
```

Kurulum araçları eksikse resmî sayfalardan yükle: [kind](https://kind.sigs.k8s.io/docs/user/quick-start/) · [kubectl](https://kubernetes.io/docs/tasks/tools/).

## 2. Cluster oluştur

```bash
kind create cluster --name kubesec-training --wait 90s
kubectl config get-contexts
kubectl --context kind-kubesec-training get nodes
```

**Beklenen:** Listede `kind-kubesec-training` context'i ve en az bir `Ready` node görünür. İlk imaj indirme süresi değişir.

## 3. Pod Security Admission namespace oluştur

```bash
kubectl --context kind-kubesec-training apply -f manifests/safe/namespace.yaml
kubectl --context kind-kubesec-training get namespace kubesec-training --show-labels
```

`pod-security.kubernetes.io/enforce=restricted`, Pod Security Admission politikasının bu namespace'teki Pod isteklerine uygulanmasını ister. `warn` ve `audit` etiketleri ise ayrı raporlama modlarıdır. Etiket yazmak tek başına cluster genelinde tüm güvenlik kontrollerinin kusursuz olduğu anlamına gelmez.

## 4. Güvenli örneği uygula

```bash
kubectl --context kind-kubesec-training apply -f manifests/safe/pod.yaml
kubectl --context kind-kubesec-training get pods -n kubesec-training
kubectl --context kind-kubesec-training describe pod secure-pod -n kubesec-training
```

**Beklenen:** Pod kabul edilir. İmaj çekimi ağ durumuna bağlı olarak zaman alabilir; `ImagePullBackOff` veya `Pending` görülürse olayları incele.

## 5. Sorular

- Bir `kubectl context` neden yanlış cluster üzerinde işlem yapılmasını önlemek için önemlidir?
- `namespace` bir güvenlik sınırı mıdır, yoksa ek yetkilendirme de gerekli midir?
- Neden `privileged` namespace yerine `restricted` seçtik?

## Kapatma

```bash
kind delete cluster --name kubesec-training
```

Sonraki: [Ders 02 — Pod Security](02-pod-security.md).
