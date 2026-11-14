import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]


def read_yaml(relative):
    return list(yaml.safe_load_all((ROOT / relative).read_text(encoding='utf-8')))


class TrainingFixtures(unittest.TestCase):
    def test_security_namespace_is_restricted(self):
        obj = read_yaml('manifests/safe/namespace.yaml')[0]
        self.assertEqual(obj['metadata']['labels']['pod-security.kubernetes.io/enforce'], 'restricted')

    def test_secure_pod_hardening(self):
        obj = read_yaml('manifests/safe/pod.yaml')[0]
        pod = obj['spec']
        self.assertFalse(pod['automountServiceAccountToken'])
        self.assertTrue(pod['securityContext']['runAsNonRoot'])
        self.assertEqual(pod['securityContext']['seccompProfile']['type'], 'RuntimeDefault')
        for container in pod['containers']:
            sc = container['securityContext']
            self.assertFalse(sc['allowPrivilegeEscalation'])
            self.assertTrue(sc['readOnlyRootFilesystem'])
            self.assertIn('ALL', sc['capabilities']['drop'])

    def test_vulnerable_pod_is_explicitly_unsafe(self):
        obj = read_yaml('manifests/vulnerable/privileged-pod.yaml')[0]
        self.assertTrue(obj['spec']['hostPID'])
        self.assertTrue(obj['spec']['containers'][0]['securityContext']['privileged'])
        self.assertTrue(any('hostPath' in item for item in obj['spec']['volumes']))

    def test_reader_role_is_namespace_scoped(self):
        objs = read_yaml('manifests/safe/role.yaml')
        role = next(obj for obj in objs if obj['kind'] == 'Role')
        self.assertEqual(role['rules'][0]['resources'], ['pods'])
        self.assertEqual(role['rules'][0]['verbs'], ['get', 'list'])
        self.assertTrue(any(obj['kind'] == 'RoleBinding' for obj in objs))

    def test_no_vulnerable_manifests_are_run_by_setup_script(self):
        for path in ('scripts/setup.sh', 'scripts/verify.sh', 'scripts/cleanup.sh'):
            text = (ROOT / path).read_text()
            if path == 'scripts/setup.sh':
                self.assertNotIn('manifests/vulnerable/', text)
            if path == 'scripts/verify.sh':
                self.assertIn('--dry-run=server', text)


    def test_networkpolicy_scoped_and_denied_manifest(self):
        deny = read_yaml('manifests/networkpolicy/default-deny-ingress.yaml')[0]
        allow = read_yaml('manifests/networkpolicy/allow-approved-to-web.yaml')[0]
        self.assertEqual(deny['spec']['policyTypes'], ['Ingress'])
        self.assertEqual(deny['spec']['podSelector'], {})
        self.assertNotIn('ingress', deny['spec'])
        rule = allow['spec']['ingress'][0]
        self.assertEqual(rule['from'][0]['podSelector']['matchLabels']['access'], 'approved')
        self.assertEqual(rule['ports'][0]['port'], 8080)

    def test_calico_configuration_disables_kindnet(self):
        config = read_yaml('config/kind-calico.yaml')[0]
        self.assertTrue(config['networking']['disableDefaultCNI'])
        self.assertEqual(config['networking']['podSubnet'], '192.168.0.0/16')

    def test_advanced_rbac_is_name_scoped_and_does_not_list(self):
        objs = read_yaml('manifests/safe/resource-names-rbac.yaml')
        role = next(obj for obj in objs if obj['kind'] == 'Role')
        rule = role['rules'][0]
        self.assertEqual(rule['resourceNames'], ['approved-config'])
        self.assertEqual(rule['resources'], ['configmaps'])
        self.assertEqual(rule['verbs'], ['get'])
        self.assertTrue(any(obj['kind'] == 'RoleBinding' for obj in objs))

    def test_unsafe_advanced_rbac_is_offline_only(self):
        objs = read_yaml('manifests/vulnerable/escalation-rbac.yaml')
        role = next(obj for obj in objs if obj['kind'] == 'ClusterRole')
        verbs = {verb for rule in role['rules'] for verb in rule['verbs']}
        self.assertTrue({'escalate', 'bind', 'impersonate'}.issubset(verbs))
        for script in ('scripts/setup.sh', 'scripts/verify.sh', 'scripts/setup-networkpolicy.sh', 'scripts/verify-networkpolicy.sh'):
            contents = (ROOT / script).read_text()
            self.assertNotIn('escalation-rbac.yaml', contents)
            self.assertNotIn('allow-all-networkpolicy.yaml', contents)
            # The existing insecure Pod is deliberately sent to Pod Security
            # Admission with --dry-run=server; no unsafe role is applied.
            if 'manifests/vulnerable/privileged-pod.yaml' in contents:
                self.assertIn('--dry-run=server', contents)


if __name__ == '__main__':
    unittest.main()
