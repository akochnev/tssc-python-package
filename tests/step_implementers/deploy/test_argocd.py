import sys
from testfixtures import TempDirectory
import unittest
from unittest.mock import patch

from test_utils import *
from tssc.step_implementers.tag_source import Git

class TestStepImplementerDeployArgoCD(unittest.TestCase):

    def test_deploy_git_username_missing(self):

        # TODO Prune the code down for this test case
        application_name = 'application-name'
        service_name = 'service-name'
        organization_name = 'organization-name'
        git_tag = 'v1.2.3'

        with TempDirectory() as temp_dir:
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : 'admin',
                            'argocd-password' : 'password',
                            'argocd-api' : 'http://argocd.example.com',
                            'deployment-namespace' : 'dev',
                            'helm-config-repo' : 'http://gitrepo.com/helm-confg-repo.git',
                            'helm-config-repo-branch' : 'master',
                            'argocd-sync-timeout-seconds' : '60',
                            'kube-app-domain' : 'apps.tssc.rht-set.com',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                        }
                    }
                }
            }

            expected_step_results = {
                'tssc-results': {
                    'deploy': {
                        'argocd-app-name': '{org}-{service}-{app}'.format(org=organization_name, service=service_name, app=application_name),
                        'config-repo-git-tag': git_tag
                    }
                }
            }

            runtime_args = {
                #'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            with self.assertRaisesRegex(
                AssertionError,
                r"Either username or password is not set. Neither or both must be set."):
                run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args)

    @patch('sh.cp', create=True)
    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_image_url_missing(self, argocd_mock, git_mock, cp_mock):

        application_name = 'application-name'
        service_name = 'service-name'
        organization_name = 'organization-name'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    image-tag: {image_tag}
                  tag-source:
                    tag: {git_tag}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'deployment-namespace' : 'dev',
                            'helm-config-repo' : helm_config_repo,
                            'helm-config-repo-branch' : 'master',
                            'argocd-sync-timeout-seconds' : '60',
                            'kube-app-domain' : 'apps.tssc.rht-set.com',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'image-tag' : image_tag
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'argocd-app-name' : '{org}-{app}-{service}'.format(org=organization_name, service=service_name, app=application_name),
                        'config-repo-git-tag' : git_tag
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            with self.assertRaisesRegex(
                ValueError,
                r"No image url was specified"):
                run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=sys.stdout
            )

    @patch('sh.cp', create=True)
    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_runtime_image_url_and_version(self, argocd_mock, git_mock, cp_mock):

        application_name = 'application-name'
        service_name = 'service-name'
        organization_name = 'organization-name'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    image-tag: {image_tag}
                  tag-source:
                    tag: {git_tag}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'deployment-namespace' : 'dev',
                            'helm-config-repo' : helm_config_repo,
                            'helm-config-repo-branch' : 'master',
                            'argocd-sync-timeout-seconds' : '60',
                            'kube-app-domain' : 'apps.tssc.rht-set.com',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'image-tag' : image_tag
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'argocd-app-name' : '{org}-{app}-{service}'.format(org=organization_name, service=service_name, app=application_name),
                        'config-repo-git-tag' : git_tag
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password',
                'image-url': image_url,
                'image-version': image_tag
            }

            run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=sys.stdout
            )

    @patch('sh.cp', create=True)
    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_app_missing(self, argocd_mock, git_mock, cp_mock):

        application_name = 'application-name'
        service_name = 'service-name'
        organization_name = 'organization-name'
        git_tag = 'v1.2.3'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    image-tag: {image_tag}
                  tag-source:
                    tag: {git_tag}
                  push-container-image:
                    image-url: {image_url}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'deployment-namespace' : 'dev',
                            'helm-config-repo' : helm_config_repo,
                            'helm-config-repo-branch' : 'master',
                            'argocd-sync-timeout-seconds' : '60',
                            'kube-app-domain' : 'apps.tssc.rht-set.com',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'image-tag' : image_tag
                    },
                    'push-container-image' : {
                        'image-url' : image_url
                    },
                    'tag-source' : {
                        'tag' : git_tag
                    },
                    'deploy': {
                        'argocd-app-name' : '{org}-{app}-{service}'.format(org=organization_name, service=service_name, app=application_name),
                        'config-repo-git-tag' : git_tag
                    }
                }
            }

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password'
            }

            run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=sys.stdout
            )

            cp_mock.assert_called_once()
            git_mock.clone.assert_called_once()

    @patch('sh.cp', create=True)
    @patch('sh.git', create=True)
    @patch('sh.argocd', create=True)
    def test_deploy_argo_git_url_no_tag(self, argocd_mock, git_mock, cp_mock):

        application_name = 'application-name'
        service_name = 'service-name'
        organization_name = 'organization-name'
        git_tag = 'latest'
        argocd_username = 'username'
        argocd_password = 'password'
        image_tag = 'not_latest'
        image_url = 'quay.io/tssc/myimage'
        helm_config_repo = 'http://gitrepo.com/helm-confg-repo.git'
        argocd_api = 'http://argocd.example.com'

        with TempDirectory() as temp_dir:
            temp_dir.makedir('tssc-results')

            temp_dir.write(
                'tssc-results/tssc-results.yml',
                bytes(
                    '''tssc-results:
                  generate-metadata:
                    image-tag: {image_tag}
                  push-container-image:
                    image-url: {image_url}
                    image-version: {image_tag}
                '''.format(image_tag=image_tag, image_url=image_url, git_tag=git_tag),
                    'utf-8')
                )
            temp_dir.write(
                'values.yaml.j2',
                bytes(
                   '''
                   {{ num_replicas }}
                   ''', 'utf-8'
                )
            )
            config = {
                'tssc-config': {
                    'global-defaults' : {
                        'service-name' : service_name,
                        'application-name' : application_name,
                        'organization' : organization_name
                    },
                    'deploy' : {
                        'implementer': 'ArgoCD',
                        'config': {
                            'argocd-username' : argocd_username,
                            'argocd-password' : argocd_password,
                            'argocd-api' : argocd_api,
                            'deployment-namespace' : 'dev',
                            'helm-config-repo' : helm_config_repo,
                            'helm-config-repo-branch' : 'master',
                            'argocd-sync-timeout-seconds' : '60',
                            'kube-app-domain' : 'apps.tssc.rht-set.com',
                            'num-replicas' : '3',
                            'ingress-enabled' : 'true',
                            'readiness-probe-path' : '/ready',
                            'liveness-probe-path' : '/live',
                            'values-yaml-directory': temp_dir.path
                        }
                    }
                }
            }

            expected_step_results = {
                'tssc-results': {
                    'generate-metadata' : {
                        'image-tag' : image_tag
                    },
                    'push-container-image' : {
                        'image-url' : image_url,
                        'image-version' : image_tag
                    },
                    'deploy': {
                        'argocd-app-name' : '{org}-{app}-{service}'.format(org=organization_name, service=service_name, app=application_name),
                        'config-repo-git-tag' : git_tag
                    }
                }
            }

            print("EXPECTED RESULTS\n" + str(expected_step_results))

            runtime_args = {
                'git-username': 'unit_test_username',
                'git-password': 'unit_test_password',
                'git-url': 'http://git.repo.com/repo.git'
            }

            run_step_test_with_result_validation(temp_dir, 'deploy', config, expected_step_results, runtime_args)

            argocd_mock.login.assert_called_once_with(
                argocd_api,
                '--username=' + argocd_username,
                '--password=' + argocd_password,
                '--insecure',
                _out=sys.stdout
            )

            cp_mock.assert_called_once()
            git_mock.clone.assert_called_once()