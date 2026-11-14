# Ders 03 — RBAC ve ServiceAccount: En Az Yetki

## Hedef

Bir ServiceAccount için yalnızca gereken kaynak ve eylemlere izin vermek. Kapsamı geniş bir ClusterRoleBinding ile dar kapsamlı RoleBinding arasındaki farkı anlamak.

## 1. Meşru Role ve RoleBinding'i oluştur

```bash
kubectl --context kind-kubesec-training apply -f manifests/safe/role.yaml
kubectl --context kind-kubesec-training get role,rolebinding,serviceaccount -n kubesec-training
```

`pod-reader` rolü yalnızca `pods` kaynağında `get` ve `list` eylemlerine izin verir. `demo-reader` ServiceAccount'u bu role bağlanır.

## 2. Etkin izni kontrol et

```bash
kubectl --context kind-kubesec-training auth can-i get pods \
  --as=system:serviceaccount:kubesec-training:demo-reader -n kubesec-training

kubectl --context kind-kubesec-training auth can-i delete pods \
  --as=system:serviceaccount:kubesec-training:demo-reader -n kubesec-training
```

**Beklenen:** İlk sonuç `yes`, ikinci sonuç `no`. Bu komutların kullanıldığı kimliğin impersonation yetkisi olması gerekir; kind'ın varsayılan yönetici context'inde mümkündür.

## 3. Hatalı RBAC'yi sadece offline incele

`manifests/vulnerable/broad-rbac.yaml` içinde tüm API gruplarına, tüm kaynaklara ve tüm eylemlere joker karakterle izin veren ClusterRole ve `cluster-admin` binding örneği var.

**Bu dosyayı cluster'a uygulama.** KubeGuard ile tara:

```bash
python -m kubeguard scan manifests/vulnerable/broad-rbac.yaml --format human
```

**Beklenen bulgular:** `KG012` (wildcard RBAC), `KG013` (cluster-admin binding).

## 4. Güvenli yaklaşım

- Erişimi mümkün olduğunda **namespace** içinde tut.
- `resources`, `verbs` ve `apiGroups` için gerekli değerleri tek tek belirt.
- ServiceAccount token'ının otomatik mount edilmesini iş yükünde gerekmedikçe kapat.
- `cluster-admin` iznini eğitimde bile örnek amaçlı kullanmak yerine, neden tehlikeli olduğunu açıkla.

## 5. Soru

Bir servis yalnızca Pod listesini okumalıysa neden `ClusterRoleBinding` değil `RoleBinding` daha uygun olabilir?

Sonraki: [Ders 04 — Audit](04-audit.md).
