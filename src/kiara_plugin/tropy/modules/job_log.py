# -*- coding: utf-8 -*-
from kiara.api import KiaraModule, ValueMapSchema
from kiara.models.values.value import ValueMap
from kiara.interfaces.python_api.base_api import BaseAPI

KIARA_METADATA = {
    "authors": [
        {"name": "Caitlin Burge", "email": "caitlinburge@hotmail.co.uk"},
    ],
    "description": "Kiara modules for: job_log",
}

class JobLog(KiaraModule):
    """Returns a log of all the jobs run in the current kiara context.

    Information for each job includes:
    - module name
    - date and time the job was submitted
    - job run time
    - comments associated with each job
    - inputs
    - outputs

    Where aliases have been assigned to the inputs / outputs, you can choose to display the alias or render the full information. If this is a particularly large input or output (e.g. a table or file), you can also choose to set a max character limit for all renderings.

    The job log can also be optionally exported as a txt or csv file.
    """

    _module_type_name = "create.job_log"

    def create_inputs_schema(self):
        return {
            "aliases": {
                "type": "boolean",
                "doc": "Whether to display aliases or not (if available).",
                "optional": True
            },
            "max_characters": {
                 "type": "integer",
                 "doc": "Maximum length of any displayed input or output. If not set, will return the entire object.",
                 "optional": True
            },
            "export_type": {
                 "type": "string",
                 "doc": "Whether to export the job log as a txt or csv file. This is an optional extra, as the job log will always be returned as the output.",
                 "optional": True
            }
        }

    def create_outputs_schema(self):
        return {
            "job_log": {
                "type": "string",
                "doc": "Job log for all jobs run in the current kiara context.",
            },
        }

    def process(self, inputs: ValueMap, outputs: ValueMap):
        kiara = self

        jobs = kiara.list_all_job_records()
        alias_dict = {}
        for values, schema in kiara.list_aliases().items():
            alias_dict[str(kiara.get_value(schema).value_id)] = values

        JOB_LOG = []
        for job_id, job in jobs.items():
            if job.is_internal == False:
                JOB_LOG.append(f"\nJob '{job.module_type}', submitted: {job.job_submitted}")
                JOB_LOG.append(f"'Comments:' {kiara.get_job_comment(job_id)}")
                JOB_LOG.append(f"Runtime: {job.runtime_details.runtime} seconds")
                JOB_LOG.append("INPUTS")
                for name, id in job.inputs.items():
                    if kiara.get_value(id).value_status.value != 'none':
                        if len(kiara._api.render_value(value=id, target_format="string").rendered) < 10:
                                JOB_LOG.append(f"{name}: \n {kiara._api.render_value(value=id, target_format="string").rendered[:1000]}")     
                        else:       
                            str_id = str(id)
                            if str_id in alias_dict.keys():
                                JOB_LOG.append(f"{name}: \n {alias_dict[str_id]}")                  
                            else:
                                JOB_LOG.append(f"{name}: \n {kiara._api.render_value(value=id, target_format="string").rendered[:1000]}")
                    else:
                        JOB_LOG.append(f"{name}: {kiara.get_value(id).value_status.value}")
                JOB_LOG.append("OUTPUTS")
                for name, id in job.outputs.items():
                    if len(kiara._api.render_value(value=id, target_format="string").rendered) < 500:
                                JOB_LOG.append(f"{name}: \n {kiara._api.render_value(value=id, target_format="string").rendered[:1000]}")   
                    else:
                        str_id = str(id)
                        if str_id in alias_dict.keys():
                            JOB_LOG.append(f"{name}: \n {alias_dict[str_id]}")
                        else:
                            JOB_LOG.append(f"{name}: \n {kiara._api.render_value(value=id, target_format="string").rendered[:1000]}")

        outputs.set_values(job_log=JOB_LOG)
