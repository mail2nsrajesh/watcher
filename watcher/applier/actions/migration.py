# -*- encoding: utf-8 -*-
# Copyright (c) 2015 b<>com
#
# Authors: Jean-Emile DARTOIS <jean-emile.dartois@b-com.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import jsonschema
from oslo_log import log
from watcher._i18n import _
from watcher.applier.actions import base
from watcher.common import exception
from watcher.common import nova_helper

LOG = log.getLogger(__name__)


class Migrate(base.BaseAction):
    """Migrates a server to a destination nova-compute host

    This action will allow you to migrate a server to another compute
    destination host.
    Migration type 'live' can only be used for migrating active VMs.
    Migration type 'cold' can be used for migrating non-active VMs
    as well active VMs, which will be shut down while migrating.

    The action schema is::

        schema = Schema({
         'resource_id': str,  # should be a UUID
         'migration_type': str,  # choices -> "live", "cold"
         'destination_node': str,
         'source_node': str,
        })

    The `resource_id` is the UUID of the server to migrate.
    The `source_node` and `destination_node` parameters are respectively the
    source and the destination compute hostname (list of available compute
    hosts is returned by this command: ``nova service-list --binary
    nova-compute``).
    """

    # input parameters constants
    MIGRATION_TYPE = 'migration_type'
    LIVE_MIGRATION = 'live'
    COLD_MIGRATION = 'cold'
    DESTINATION_NODE = 'destination_node'
    SOURCE_NODE = 'source_node'

    @property
    def schema(self):
        return {
            'type': 'object',
            'properties': {
                'destination_node': {
                    'type': 'string',
                    "minLength": 1
                },
                'migration_type': {
                    'type': 'string',
                    "enum": ["live", "cold"]
                },
                'resource_id': {
                    'type': 'string',
                    "minlength": 1,
                    "pattern": ("^([a-fA-F0-9]){8}-([a-fA-F0-9]){4}-"
                                "([a-fA-F0-9]){4}-([a-fA-F0-9]){4}-"
                                "([a-fA-F0-9]){12}$")
                },
                'source_node': {
                    'type': 'string',
                    "minLength": 1
                    }
            },
            'required': ['destination_node', 'migration_type',
                         'resource_id', 'source_node'],
            'additionalProperties': False,
        }

    def validate_parameters(self):
        try:
            jsonschema.validate(self.input_parameters, self.schema)
            return True
        except jsonschema.ValidationError as e:
            raise e

    @property
    def instance_uuid(self):
        return self.resource_id

    @property
    def migration_type(self):
        return self.input_parameters.get(self.MIGRATION_TYPE)

    @property
    def destination_node(self):
        return self.input_parameters.get(self.DESTINATION_NODE)

    @property
    def source_node(self):
        return self.input_parameters.get(self.SOURCE_NODE)

    def _live_migrate_instance(self, nova, destination):
        result = None
        try:
            result = nova.live_migrate_instance(instance_id=self.instance_uuid,
                                                dest_hostname=destination)
        except nova_helper.nvexceptions.ClientException as e:
            if e.code == 400:
                LOG.debug("Live migration of instance %s failed. "
                          "Trying to live migrate using block migration."
                          % self.instance_uuid)
                result = nova.live_migrate_instance(
                    instance_id=self.instance_uuid,
                    dest_hostname=destination,
                    block_migration=True)
            else:
                LOG.debug("Nova client exception occurred while live "
                          "migrating instance %s.Exception: %s" %
                          (self.instance_uuid, e))
        except Exception:
            LOG.critical("Unexpected error occurred. Migration failed for "
                         "instance %s. Leaving instance on previous "
                         "host.", self.instance_uuid)

        return result

    def _cold_migrate_instance(self, nova, destination):
        result = None
        try:
            result = nova.watcher_non_live_migrate_instance(
                instance_id=self.instance_uuid,
                dest_hostname=destination)
        except Exception as exc:
            LOG.exception(exc)
            LOG.critical("Unexpected error occurred. Migration failed for "
                         "instance %s. Leaving instance on previous "
                         "host.", self.instance_uuid)
        return result

    def migrate(self, destination):
        nova = nova_helper.NovaHelper(osc=self.osc)
        LOG.debug("Migrate instance %s to %s", self.instance_uuid,
                  destination)
        instance = nova.find_instance(self.instance_uuid)
        if instance:
            if self.migration_type == self.LIVE_MIGRATION:
                return self._live_migrate_instance(nova, destination)
            elif self.migration_type == self.COLD_MIGRATION:
                return self._cold_migrate_instance(nova, destination)
            else:
                raise exception.Invalid(
                    message=(_("Migration of type '%(migration_type)s' is not "
                               "supported.") %
                             {'migration_type': self.migration_type}))
        else:
            raise exception.InstanceNotFound(name=self.instance_uuid)

    def execute(self):
        return self.migrate(destination=self.destination_node)

    def revert(self):
        return self.migrate(destination=self.source_node)

    def abort(self):
        # TODO(adisky): implement abort for migration
        LOG.warning("Abort for migration not implemented")

    def pre_condition(self):
        # TODO(jed): check if the instance exists / check if the instance is on
        # the source_node
        pass

    def post_condition(self):
        # TODO(jed): check extra parameters (network response, etc.)
        pass

    def get_description(self):
        """Description of the action"""
        return "Moving a VM instance from source_node to destination_node"
