from python_terraform import Terraform
import subprocess
import os
import time


def create(pathToPlatform):

    # Initalize a terraform object
    # Make the working directory the openstack directory
    terra = Terraform(pathToPlatform)

    # Apply the IAC in the openstack directory and skip the planning Stage
    return_code, stdout, stderr = terra.apply(skip_plan=True)

    # Get the outputs from the apply
    outputs = terra.output()

    # Return the outputs
    return outputs, return_code
