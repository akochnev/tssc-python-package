"""
Step Implementer for the deploy step for ArgoCD.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key         | Required?          | Default              | Description
|---------------------------|--------------------|----------------------|---------------------------
| `argocd-username`         | True               |                      | Username for accessing the
                                                                          ArgoCD API
| `argocd-password`         | True               |                      | Password for accessing the
                                                                          ArgoCD API
| `argocd-api`              | True               |                      | The ArgoCD API endpoint
| `deployment-namespace`    | True               |                      | The k8s namespace to
                                                                          deploy the app into
| `helm-config-repo`        | True               |                      | The repo containing the
                                                                          helm chart definiton
| `values-yaml-directory`   | False              | ./cicd/Deployment/   | Directory containing jinja
                                                                          templates
| `value-yaml-template`     | False              | values.yaml.j2       | Name of the values yaml
                                                                          jinja file
| `helm-config-repo-branch` | False              | master               | The branch to modify
                                                                          within the helm config
                                                                          git repo. This is also the
                                                                          branch argocd will listen
                                                                          on when the project is
                                                                          configured.
| `argocd-sync-timeout-`    | False              | 60                   | Number of seconds to wait
  `seconds`                                                               for argocd to sync updates
| `kube-api-url`            | False              | https://kubernetes.  | k8s API endpoint
                                                   default.svc
| `argocd-helm-chart-path`  | False              | ./                   | Directory containing the
                                                                          helm chart definition
| `git-username`            | False              |                      | If the helm config repo
                                                                          is accessed via http(s)
                                                                          this must be supplied
| `git-password`            | False              |                      | If the helm config repo
                                                                          is accessed via http(s)
                                                                          this must be supplied
| `git-url`                 | False              |                      | Optional explicit
                                                                          specification of git url
| `git-email`               | False              |                      | Git email for commit
| `git-friendly-name`       | False              |                      | Git name for commit


Expected Previous Step Results
------------------------------

Results expected from previous steps that this step may require.

| Step Name              | Result Key      | Description
|------------------------|-----------------|------------
| `tag-source`           | `tag`           | The git tag to apply to the config repo
| `push-container-image` | `image-url`     | The image url to use in the deployment
| `push-container-image` | `image-version` | The image version use in the deployment

Results
-------

Results output by this step.

| Result Key            | Description
|-----------------------|------------
| `argocd-app-name`     | The argocd app name that was created or updated
| `config-repo-git-tag` | The git tag applied to the configuration repo for deployment


**Example**

    'tssc-results': {
        'deploy': {
            'argocd-app-name': 'acme-myapp-frontend',
            'config-repo-git-tag': 'value'
        }
    }
"""
import sys
import tempfile
import sh
from jinja2 import Environment, FileSystemLoader
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_CONFIG = {
    'values-yaml-directory': './cicd/Deployment',
    'values-yaml-template': 'values.yaml.j2',
    'helm-config-repo-branch': 'master',
    'argocd-sync-timeout-seconds': 60,
    'kube-api-uri': 'https://kubernetes.default.svc',
    'argocd-helm-chart-path': './',
    'git-email': 'napsspo+tssc@redhat.com',
    'git-friendly-name': 'TSSC'
}

REQUIRED_CONFIG_KEYS = [
    'argocd-username',
    'argocd-password',
    'argocd-api',
    'deployment-namespace',
    'helm-config-repo'
]

GIT_AUTHENTICATION_CONFIG = {
    'git-username': None,
    'git-password': None
}

class ArgoCD(StepImplementer):
    """ StepImplementer for the deploy step for ArgoCD.


    """
    @staticmethod
    def step_name():
        """
        Getter for the TSSC Step name implemented by this step.

        Returns
        -------
        str
            TSSC step name implemented by this step.
        """
        return DefaultSteps.DEPLOY

    @staticmethod
    def step_implementer_config_defaults():
        """
        Getter for the StepImplementer's configuration defaults.

        Notes
        -----
        These are the lowest precedence configuration values.

        Returns
        -------
        dict
            Default values to use for step configuration values.
        """
        return DEFAULT_CONFIG

    @staticmethod
    def required_runtime_step_config_keys():
        """
        Getter for step configuration keys that are required before running the step.

        See Also
        --------
        _validate_runtime_step_config

        Returns
        -------
        array_list
            Array of configuration keys that are required before running the step.
        """
        return REQUIRED_CONFIG_KEYS

    def _validate_runtime_step_config(self, runtime_step_config):
        """
        Validates the given `runtime_step_config` against the required step configuration keys.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Raises
        ------
        AssertionError
            If the given `runtime_step_config` is not valid with a message as to why.
        """
        super()._validate_runtime_step_config(runtime_step_config) #pylint: disable=protected-access

        assert ( \
            all(element in runtime_step_config for element in GIT_AUTHENTICATION_CONFIG) or \
            not any(element in runtime_step_config for element in GIT_AUTHENTICATION_CONFIG) \
        ), 'Either username or password is not set. Neither or both must be set.'

    def _run_step(self, runtime_step_config):
        """
        Runs the TSSC step implemented by this StepImplementer.

        Parameters
        ----------
        runtime_step_config : dict
            Step configuration to use when the StepImplementer runs the step with all of the
            various static, runtime, defaults, and environment configuration munged together.

        Returns
        -------
        dict
            Results of running this step.
        """

        self._validate_runtime_step_config(runtime_step_config)

        print(
            sh.argocd.login( # pylint: disable=no-member
                runtime_step_config['argocd-api'],
                '--username=' + runtime_step_config['argocd-username'],
                '--password=' + runtime_step_config['argocd-password'],
                '--insecure', _out=sys.stdout
            )
        )

        argocd_app_name = "{organization}-{application}-{service}".\
                            format(organization=runtime_step_config['organization'],
                                   application=runtime_step_config['application-name'],
                                   service=runtime_step_config['service-name'])

        try:
            print(sh.argocd.app.get(argocd_app_name, _out=sys.stdout)) # pylint: disable=no-member
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            print('No app found, creating a new app...')
            print(
                sh.argocd.app.create( # pylint: disable=no-member
                    argocd_app_name,
                    '--repo=' + runtime_step_config['helm-config-repo'],
                    '--revision=' + runtime_step_config['helm-config-repo-branch'],
                    '--path=' + runtime_step_config['argocd-helm-chart-path'],
                    '--dest-server=' + runtime_step_config['kube-api-uri'],
                    '--dest-namespace=' + runtime_step_config['deployment-namespace'],
                    _out=sys.stdout
                )
            )

        git_url = self._git_url(runtime_step_config)

        with tempfile.TemporaryDirectory() as repo_directory:
            try:
                sh.git.clone(runtime_step_config['helm-config-repo'], repo_directory)
                sh.git.checkout(runtime_step_config['helm-config-repo-branch'],
                                _cwd=repo_directory)

                self._update_values_yaml(repo_directory, runtime_step_config)

                tag = self._get_tag()
                git_commit_msg = 'Configuration Change from TSSC Pipeline. Repository: ' +\
                                 '{repo} Tag: {tag}'.format(repo=git_url, tag=tag)

                print(sh.git.config('--global', 'user.email', runtime_step_config['git-email'],
                                    _out=sys.stdout))

                print(sh.git.config('--global', 'user.name',
                                    runtime_step_config['git-friendly-name'],
                                    _out=sys.stdout))

                print(sh.git.commit('-am', git_commit_msg, _cwd=repo_directory,
                                    _out=sys.stdout))

                print(sh.git.tag('-f', self._get_tag(), _cwd=repo_directory,
                                 _out=sys.stdout))

            except sh.ErrorReturnCode: # pylint: disable=undefined-variable
                raise RuntimeError("Unexpected error executing Git commands")

            self._process_git_push(repo_directory, runtime_step_config)

        print(
            sh.argocd.app.sync('--timeout', runtime_step_config['argocd-sync-timeout-seconds'], # pylint: disable=no-member
                               argocd_app_name,
                               _out=sys.stdout)
        )

        results = {
            'argocd-app-name': argocd_app_name,
            'config-repo-git-tag' : tag
        }

        return results

    def _get_image_url(self, runtime_step_config):
        image_url = None

        if runtime_step_config.get('image-url'):
            image_url = runtime_step_config.get('image-url')
        else:
            if(self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE) \
            and self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).get('image-url')):
                image_url = self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).\
                            get('image-url')
            else:
                print('No image url found in metadata.')
                raise ValueError('No image url was specified')
        return image_url

    def _get_image_version(self, runtime_step_config):
        image_version = 'latest'

        if runtime_step_config.get('image-version'):
            image_version = runtime_step_config.get('image-version')
        else:
            if(self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE) \
            and self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).get('image-version')):
                image_version = self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).\
                                get('image-version')
            else:
                print('No image version found in metadata, using \"latest\"')
        return image_version

    def _update_values_yaml(self, repo_directory, runtime_step_config):
        env = Environment(loader=FileSystemLoader(runtime_step_config['values-yaml-directory']),
                          trim_blocks=True, lstrip_blocks=True)

        version = self._get_image_version(runtime_step_config)
        url = self._get_image_url(runtime_step_config)

        jinja_runtime_step_config = {'image-url' : url, 'image-version' : version}
        for key in runtime_step_config:
            jinja_runtime_step_config[key.replace('-', '_')] = runtime_step_config[key]

        template = env.get_template(runtime_step_config['values-yaml-template'])

        with open("values.yaml", "w") as out_file:
            out_file.writelines(template.render(jinja_runtime_step_config))

        sh.cp('-f', 'values.yaml', repo_directory + '/values.yaml') # pylint: disable=no-member

    def _get_tag(self):
        tag = 'latest'
        if(self.get_step_results(DefaultSteps.TAG_SOURCE) \
          and self.get_step_results(DefaultSteps.TAG_SOURCE).get('tag')):
            tag = self.get_step_results(DefaultSteps.TAG_SOURCE).get('tag')
        else:
            print('No version found in metadata. Using latest')
        return tag

    def _process_git_push(self, repo_directory, runtime_step_config):
        git_url = self._git_url(runtime_step_config)

        username = None
        password = None

        if any(element in runtime_step_config for element in GIT_AUTHENTICATION_CONFIG):
            if(runtime_step_config.get('git-username') \
            and runtime_step_config.get('git-password')):
                username = runtime_step_config.get('git-username')
                password = runtime_step_config.get('git-password')
            else:
                raise ValueError(
                    'Both username and password must have ' \
                    'non-empty value in the runtime step configuration'
                )
        else:
            print('No username/password found, assuming ssh')
        tag = self._get_tag()
        self._git_tag(repo_directory, tag)
        git_url = self._git_url(runtime_step_config)
        if git_url.startswith('http://'):
            if username and password:
                self._git_push(repo_directory, 'http://{username}:{password}@{url}'.format(
                    username=username,
                    password=password,
                    url=git_url[7:]))
            else:
                raise ValueError(
                    'For a http:// git url, you need to also provide ' \
                    'username/password pair'
                )
        elif git_url.startswith('https://'):
            if username and password:
                self._git_push(repo_directory, 'http://{username}:{password}@{url}'.format(
                    username=username,
                    password=password,
                    url=git_url[8:]))

            else:
                raise ValueError(
                    'For a https:// git url, you need to also provide ' \
                    'username/password pair'
                )
        else:
            self._git_push(repo_directory, None)

    @staticmethod
    def _git_push(repo_directory, url=None):

        try:
            if url:
                sh.git.push(
                    url,
                    '--tag',
                    _out=sys.stdout,
                    _cwd=repo_directory
                )
                sh.git.push(
                    url,
                    _out=sys.stdout,
                    _cwd=repo_directory
                )
            else:
                sh.git.push(
                    '--tag',
                    _out=sys.stdout,
                    _cwd=repo_directory
                )
                sh.git.push(
                    url,
                    _out=sys.stdout,
                    _cwd=repo_directory
                )
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git push')

    @staticmethod
    def _git_tag(repo_directory, git_tag_value):  # pragma: no cover
        try:
            # NOTE:
            # this force is only needed locally in case of a re-reun of the same pipeline
            # without a fresh check out. You will notice there is no force on the push
            # making this an acceptable work around to the issue since on the off chance
            # actually orverwriting a tag with a different comment, the push will fail
            # because the tag will be attached to a different git hash.
            sh.git.tag(  # pylint: disable=no-member
                git_tag_value,
                '-f',
                _out=sys.stdout,
                _cwd=repo_directory
            )
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git tag ' + git_tag_value)

    @staticmethod
    def _git_url(runtime_step_config):
        return_val = None
        if runtime_step_config.get('url'):
            return_val = runtime_step_config.get('url')
        else:
            try:
                return_val = sh.git.config(
                    '--get',
                    'remote.origin.url',
                    _out=sys.stdout,
                    _tee=True,
                    _encoding='UTF-8',
                    _decode_errors='ignore'
                    ).rstrip()

            except sh.ErrorReturnCode:  # pylint: disable=undefined-variable # pragma: no cover
                raise RuntimeError('Error invoking git config --get remote.origin.url')
        return return_val

# register step implementer
TSSCFactory.register_step_implementer(ArgoCD, True)
