"""
Step Implementer for the deploy step for ArgoCD.
"""
import sh
from tssc import TSSCFactory
from tssc import StepImplementer
from tssc import DefaultSteps

DEFAULT_ARGS = {
    'values_yaml_template': './values.yaml.j2',
    'helm-config-repo-branch': 'master',
    'argocd-deployment-check-timeout-seconds': 60
}

REQUIRED_ARGS = {
    'argocd-username': None,
    'argocd-password': None,
    'argocd-api': None,
    'argocd-destination-namespace': None,
    'helm-config-repo': None
}

OPTIONAL_ARGS = {
    'helm-config-repo-branch': None,
}

GIT_OPTIONAL_ARGS = {
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

    def __init__(self, config, results_dir, results_file_name):
        super().__init__(config, results_dir, results_file_name, DEFAULT_ARGS)

    @classmethod
    def step_name(cls):
        return DefaultSteps.DEPLOY

    def _validate_step_config(self, step_config):
        """
        Function for implementers to override to do custom step config validation.

        Parameters
        ----------
        step_config : dict
            Step configuration to validate.
        """
        print(step_config)
        
        for config_name in DEFAULT_ARGS:
            if config_name not in step_config or not step_config[config_name]:
                raise ValueError('Key (' + config_name + ') must have non-empty value in the step '
                                 'configuration')

        for config_name in REQUIRED_ARGS:
            if config_name not in step_config or not step_config[config_name]:
                raise ValueError('Key (' + config_name + ') is required and must have a '
                                  'non-empty value in the step configuration')        

    @staticmethod
    def _validate_runtime_step_config(runtime_step_config):
        if not all(element in runtime_step_config for element in GIT_OPTIONAL_ARGS) \
          and any(element in runtime_step_config for element in GIT_OPTIONAL_ARGS):
            raise ValueError('Either username or password is not set. Neither ' \
              'or both must be set.')

    def _get_tag(self):
        tag = 'latest'
        if(self.get_step_results('generate-metadata') \
          and self.get_step_results('generate-metadata').get('image-tag')):
            tag = self.get_step_results('generate-metadata').get('image-tag')
        else:
            print('No version found in metadata. Using latest')
        return tag

    #TODO: MAKE SURE SKOPEO IS UPDATED TO RETURN 'image-url' AND 'image-version'

    def _get_image_url(self, runtime_step_config):
        image_url = None

        if runtime_step_config.get('image-url'):
            image_url = runtime_step_config.get('image-url')
        else:
            if(self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE) \
            and self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).get('image-url')):
                image_url = self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).get('image-url')
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
                image_version = self.get_step_results(DefaultSteps.PUSH_CONTAINER_IMAGE).get('image-version')
            else:
                print('No image version found in metadata, using \"latest\"')
        return image_version        

    def _run_step(self, runtime_step_config):
        results = {}


        # Create the argocd project (via argocli) if it doesn't already exist

        # Retrieve image-version and image-url from the previous output

        # Create a flat dictionary of all config parameters from previous steps and the current step config

        # Use jinja to create values.yaml from values.yaml.j2 using the dictionary above

        # Clone the config repo
        
        # Checkout the correct branch

        # Copy the generated values.yaml over 

        # Commit the change, tag the branch, push the repo

        # User argo cli to verify deployment has started (timeout value)

        # Set the results:
        # results = {
        #     'config_repo_git_tag' : tag
        # } 

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
    def _git_tag(git_tag_value): # pragma: no cover
        try:
            # NOTE:
            # this force is only needed locally in case of a re-reun of the same pipeline
            # without a fresh check out. You will notice there is no force on the push
            # making this an acceptable work around to the issue since on the off chance
            # actually orverwriting a tag with a different comment, the push will fail
            # because the tag will be attached to a different git hash.
            sh.git.tag(git_tag_value, '-f')
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

# register step implementer
TSSCFactory.register_step_implementer(Git, True)
