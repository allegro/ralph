# DCIM

## Introduction

TODO

## Configuration path

You could optionally specify configuration path for you Data Center objects, like
`Data Center Asset`, `Virtual Server` or `Cloud Host`. This path could be later used as an input to the configuration management tool, like [Puppet](https://puppet.com/) or [Ansible](https://www.ansible.com/).

First, you should define (hierarchy of) configuration modules (`http://<YOU_RALPH_URL>/assets/configurationmodule/`). You could store configuration modules in tree (using `parent` relation) to group multiple configurations. The tree structure could be used to reflect directories structure where you're storing your configuration files.

> If you're using Puppet, configuration module could be directly mapped to [Puppet module](https://docs.puppet.com/puppet/latest/reference/modules_fundamentals.html).

> If you're using Ansible, use configuration module to group multiple configs.

Then you could add configuration classes (`http://<YOUR_RALPH_URL>/assets/configurationclass/`). This class will be later used to mark host that it's holding this configuration.

> In case of Puppet, this maps directly to [Puppet class](https://docs.puppet.com/puppet/latest/reference/lang_classes.html).

> For Ansible, this could be mapped to [Playbook](http://docs.ansible.com/ansible/playbooks.html).

Finally, you could attach configuration to your host (`Data Center Asset`, `Virtual Server` etc.) using `configuration path` field. This could be used for administrators information only, but you could use this to automate you configuration management tool as well! Simply fetch `configuration_path` for host from Ralph's API and apply it in your tool.

You could use custom fields to set some variables passed to your configuration management tool. To show custom field under `configuration_variables` field in REST API, select `use as configuration variable` in its settings. See [Custom fields](/user/custom_fields) section for more infromation.
