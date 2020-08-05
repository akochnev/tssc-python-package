"""
Step Implementer for the deploy step for ArgoCD.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key         | Required?          | Default              | Description
|---------------------------|--------------------|----------------------|---------------------------
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
| `argocd-sync-timeout-     | False              | 60                   | Number of seconds to wait
   seconds`                                                               for argocd to sync updates



Expected Previous Step Results
------------------------------

Results expected from previous steps that this step may require. If not found, it
will attempt to tag the source with `latest`

| Step Name           | Result Key | Description
|---------------------|------------|------------
| `generate-metadata` | ``         |

Results
-------

Results output by this step.

| Result Key | Description
|------------|------------
| ``         |


**Example**

    'tssc-results': {
        'deploy': {
            'key': 'value'
        }
    }
"""
import sys
import sh
from jinja2 import Environment, FileSystemLoader
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_CONFIG = {
    'values-yaml-directory': '../cicd/Deployment', #changed for testing
    'values-yaml-template': 'values.yaml.j2',
    'helm-config-repo-branch': 'master',
    'argocd-sync-timeout-seconds': 60,
    'kube-api-uri': 'https://kubernetes.default.svc',
    'argocd-helm-chart-path': './'
}

REQUIRED_CONFIG_KEYS = [
    'argocd-username',
    'argocd-password',
    'argocd-api',
    'argocd-destination-namespace',
    'helm-config-repo'
]

GIT_AUTHENTICATION_CONFIG = {
    'git-username': None,
    'git-password': None
}

class ArgoCD(StepImplementer):
    """ StepImplementer for the deploy step for ArgoCD.

    This makes extensive use of the python sh library. This was a deliberate choice,
    as the gitpython library doesn't appear to easily support username/password auth
    for http and https git repos, and that is a desired use case.

Step Configuration
------------------

Step configuration expected as input to this step.
Could come from either configuration file or
from runtime configuration.

| Configuration Key | Required? | Default | Description
|-------------------|-----------|---------|-----------
| `TODO`            | True      |         |

Expected Previous Step Results
------------------------------
Results expected from previous steps that this step requires.
| Step Name | Result Key | Description
|-----------|------------|------------
| `TODO`    | `TODO`     | TODO

Results
-------

Results output by this step.

| Result Key | Description
|------------|------------
| `TODO`     | TODO

**Example**
    'tssc-results': {
        'TODO': {
            'TODO': ''
        }
    }

    Raises
    ------
    ValueError
        If a required parameter is unspecified
    RuntimeError
        If git commands fail for any reason
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

        ## Checks for git username and password
        self._validate_runtime_step_config(runtime_step_config)

        # Create the argocd project (via argocli) if it doesn't already exist
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
            print(sh.argocd.app.get(argocd_app_name), _out=sys.stdout) # pylint: disable=no-member
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable # pragma: no cover
            print('No app found, creating a new app...')
            print(
                sh.argocd.app.create( # pylint: disable=no-member
                    argocd_app_name,
                    '--repo=' + runtime_step_config['helm-config-repo'],
                    '--revision=' + runtime_step_config['helm-config-repo-branch'],
                    '--path=' + runtime_step_config['argocd-helm-chart-path'],
                    '--dest-server=' + runtime_step_config['kube-api-uri'],
                    '--dest-namespace=' + runtime_step_config['argocd-destination-namespace']
                )
            )
        ## argocd app get <APP_NAME> ! exist (argocd app create <APP_NAME> --repo <REPO_URL> \
         #--revision <BRANCH> --path <PATH> --dest-server https://kubernetes.default.svc \
         # --dest-namespace <NAMESPACE>)

        # Clone the config repo
        git_url = self._git_url(runtime_step_config)

        # TODO Possibly use a temporary directory and remove it afterwards
        repo_directory = "./cloned-repo"
        sh.git.clone('http://gitea.tssc.rht-set.com/tssc-references/tssc-reference-app-quarkus-rest-json-config.git', repo_directory) #changed for testing

        # Checkout the correct branch
        sh.cd(repo_directory) #added for testing
        sh.git.checkout(runtime_step_config['helm-config-repo-branch'])

        self._update_values_yaml(repo_directory, runtime_step_config)

        # Commit the change, tag the branch, push the repo

        tag = self._get_tag()
        git_commit_msg = "Configuration Change from TSSC Pipeline. Repository: {repo} Tag: {tag}".\
                          format(repo=git_url, tag=tag)

        sh.git.add('values.yaml')
        sh.git.commit('-am', git_commit_msg)

        self._git_tag(tag, git_commit_msg)

        # TODO See the code in tag_source/git.py for retrieving username/password and handling ssh
        git_username = None
        git_password = None

        self._git_push("http://{username}:{password}@{url}".format(username=git_username,
                                                                   password=git_password,
                                                                   url=git_url[7:]))

        # User argo cli to verify deployment has started (timeout value)
        print(
            sh.argocd.app.sync('--timeout', runtime_step_config['argocd-sync-timeout-seconds'], # pylint: disable=no-member
                               _out=sys.stdout)
        )

        results = {
            'argocd_app_name': argocd_app_name,
            'config_repo_git_tag' : tag
        }

        # username = None
        # password = None

        # self._validate_runtime_step_config(runtime_step_config)

        # if any(element in runtime_step_config for element in OPTIONAL_ARGS):
        #     if(runtime_step_config.get('username') \
        #       and runtime_step_config.get('password')):
        #         username = runtime_step_config.get('username')
        #         password = runtime_step_config.get('password')
        #     else:
        #         raise ValueError('Both username and password must have ' \
        #           'non-empty value in the runtime step configuration')
        # else:
        #     print('No username/password found, assuming ssh')

        # tag = self._get_tag()
        # self._git_tag(tag)

        # image_url = self._get_image_url(runtime_step_config)
        # image_version = self._get_image_url(runtime_step_config)

        # values_yaml = __main__.parse_yaml_or_json_file(runtime_step_config['values_yaml_file'])

        # git_url = self._git_url(runtime_step_config)
        # if git_url.startswith('http://'):
        #     if username and password:
        #         self._git_push('http://' + username + ':' + password + '@' + git_url[7:])
        #     else:
        #         raise ValueError('For a http:// git url, you need to also provide ' \
        #           'username/password pair')
        # elif git_url.startswith('https://'):
        #     if username and password:
        #         self._git_push('https://' + username + ':' + password + '@' + git_url[8:])
        #     else:
        #         raise ValueError('For a https:// git url, you need to also provide ' \
        #           'username/password pair')
        # else:
        #     self._git_push(None)
        # results = {
        #     'git_tag' : tag
        # }
        return results

    @staticmethod
    def _git_url(runtime_step_config):
        return_val = None
        if runtime_step_config.get('git_url'):
            return_val = runtime_step_config.get('git_url')
        else:
            try:
                return_val = sh.git.config(
                    '--get',
                    'remote.origin.url').stdout.decode("utf-8").rstrip()
            except sh.ErrorReturnCode:  # pylint: disable=undefined-variable # pragma: no cover
                raise RuntimeError('Error invoking git config --get remote.origin.url')
        return return_val

    @staticmethod
    def _git_tag(git_tag_value, git_tag_comment): # pragma: no cover
        try:
            # NOTE:
            # this force is only needed locally in case of a re-reun of the same pipeline
            # without a fresh check out. You will notice there is no force on the push
            # making this an acceptable work around to the issue since on the off chance
            # actually orverwriting a tag with a different comment, the push will fail
            # because the tag will be attached to a different git hash.
            sh.git.tag('-a', git_tag_value, ' -f -m ', git_tag_comment)
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git tag ' + git_tag_value)

    @staticmethod
    def _git_push(url=None): # pragma: no cover
        try:
            if url:
                sh.git.push(url, '--tag')
            else:
                sh.git.push('--tag')
        except sh.ErrorReturnCode:  # pylint: disable=undefined-variable
            raise RuntimeError('Error invoking git push')

    def _get_tag(self):
        tag = 'latest'
        if(self.get_step_results(DefaultSteps.GENERATE_METADATA) \
          and self.get_step_results(DefaultSteps.GENERATE_METADATA).get('image-tag')):
            tag = self.get_step_results(DefaultSteps.GENERATE_METADATA).get('image-tag')
        else:
            print('No image-tag found in metadata. Using latest')
        return tag

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
                image_url = 'quay.io/repository/tssc/tssc-tool-argocd'
                #raise ValueError('No image url was specified')
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

        #sh.cp('-f', 'values.yaml', repo_directory + '/values.yaml') # pylint: disable=no-member

# register step implementer
TSSCFactory.register_step_implementer(ArgoCD, True)
