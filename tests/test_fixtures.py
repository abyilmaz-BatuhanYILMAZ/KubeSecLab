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


if __name__ == '__main__':
    unittest.main()
