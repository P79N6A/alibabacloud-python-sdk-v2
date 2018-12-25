import sys
import time
import unittest
import json
import os

import alibabacloud
from aliyunsdkcore.acs_exception.exceptions import ClientException, ServerException
from alibabacloud.services.ecs import ECSInstancesResource, ResourceCollection, ResourceCollection, ECSResource

if sys.version_info[0] == 2:
    from collections import Iterable
else:
    from collections.abc import Iterable


class TestGetResource(unittest.TestCase):

    def setUp(self):
        sdk_config_path = os.path.join(
            os.path.expanduser("~"),
            "aliyun_sdk_config.json")
        with open(sdk_config_path) as fp:
            config = json.loads(fp.read())
            self.access_key_id = config["access_key_id"]
            self.access_key_secret = config["access_key_secret"]
            self.region_id = config["region_id"]

    def test_get_resource_without_ecs(self):
        try:
            resource = alibabacloud.get_resource(
                "rds",
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                region_id=self.region_id)
            assert False
        except ClientException as e:
            self.assertEqual(e.error_code, "SDK.ServiceNameNotFound")
            self.assertEqual(e.get_error_msg(), "You provide is not ECS Service")

    def test_get_resource_with_ecs(self):
        resource = alibabacloud.get_resource(
            "ECS",
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=self.region_id)
        self.assertIsInstance(resource, ECSResource)


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.temp_instances = []
        sdk_config_path = os.path.join(
            os.path.expanduser("~"),
            "aliyun_sdk_config.json")
        with open(sdk_config_path) as fp:
            config = json.loads(fp.read())
            self.access_key_id = config["access_key_id"]
            self.access_key_secret = config["access_key_secret"]
            self.region_id = config["region_id"]

        self.init_resource()

    def init_resource(self):
        self.resource = alibabacloud.get_resource(
            "ecs",
            access_key_id=self.access_key_id,
            access_key_secret=self.access_key_secret,
            region_id=self.region_id)

    def tearDown(self):
        for instance_id in self.temp_instances:
            item_list = self.resource.instances.filter(instance_id)
            for item in item_list:
                # Stopped
                while True:
                    if item.status in ("Stopping", "Starting"):
                        item.stop()
                        continue
                    if item.status == "Running":
                        item.stop()
                        continue
                    if item.status == "Stopped":
                        item.delete()
                        self.temp_instances.remove(instance_id)
                        break


class TestECSResource(BaseTest):
    def test_ecs_resource(self):
        pass

    # def test_create_instance(self):
    #     response = self.resource.create_instance(
    #         ImageId="coreos_1745_7_0_64_30G_alibase_20180705.vhd",
    #         InstanceType="ecs.n2.small")
    #     response_obj = json.loads(response)
    #     self.assertTrue(response_obj.get("InstanceId"))
    #     self.temp_instances.append(response_obj.get("InstanceId'))

    # def test_run_instances(self):
    #     response = self.resource.run_instances(
    #         ImageId='coreos_1745_7_0_64_30G_alibase_20180705.vhd', Amount=10, InstanceType='ecs.n2.small', SecurityGroupId="sg-bp12zdiq3r9dqbaaq717")
    #     response_obj = json.loads(response.decode("utf-8"))
    #     instances_sets = response_obj.get("InstanceIdSets").get("InstanceIdSet")
    #     self.assertEqual(len(instances_sets), 10)
    #     self.temp_instances.extend(instances_sets)


class TestECSInstanceResource(BaseTest):

    def get_test_obj(self, instance_id):
        ecs_instance_list = self.resource.instances.filter(InstanceId = instance_id)
        if len(list(ecs_instance_list)) > 0:
            obj = list(ecs_instance_list)[0]
            return obj

    def test_ecs_instances(self):
        self.assertTrue(self.get_test_obj("i-bp162a07bhoj5skna4zj").InstanceName)

    def test_status(self):
        obj = self.get_test_obj("i-bp162a07bhoj5skna4zj")
        self.assertEqual(obj.status, "Stopping")

    # def test_delete(self):
    #     obj = self.get_test_obj("i-bp1igpepkvn9onj9o42e")
    #     obj.delete()

    def test_start(self):
        obj = self.get_test_obj("i-bp162a07bhoj5skna4zj")
        try:
            obj.start()
            assert False
        except ServerException as e:
            self.assertEqual(e.error_code, "IncorrectInstanceStatus")
            self.assertTrue(e.get_error_msg().startswith(
                "The specified instance is in an incorrect status for the requested action;"))

    def test_stop(self):
        obj = self.get_test_obj("i-bp1f3b73z92zsm6ay7ce")
        try:
            obj.stop()
            assert False
        except ServerException as e:
            self.assertEqual(e.error_code, "IncorrectInstanceStatus")
            self.assertTrue(e.get_error_msg().startswith(
                "The specified instance is in an incorrect status for the requested action;"))

    def test_reboot(self):
        obj = self.get_test_obj("i-bp162a07bhoj5skna4zj")
        obj.reboot()
        self.assertEqual(obj.status, "Stopping")

    def test_renew_without_period(self):
        obj = self.get_test_obj("i-bp162a07bhoj5skna4zj")
        try:
            obj.renew()
            assert False
        except ServerException as e:
            self.assertEqual(e.error_code, "MissingParameter")
            self.assertEqual(
                e.get_error_msg(),
                'The input parameter "Period" that is mandatory for processing this request is not supplied.')

    def test_renew(self):
        obj = self.get_test_obj("i-bp162a07bhoj5skna4zj")
        try:
            obj.renew(Period=1)
            assert False
        except ServerException as e:
            self.assertEqual(e.error_code, "ChargeTypeViolation")
            self.assertEqual(
                e.get_error_msg(),
                "The operation is not permitted due to charge type of the instance.")

    def test_reactivate(self):
        obj = self.get_test_obj("i-bp162a07bhoj5skna4zj")
        try:
            obj.reactivate(Period=1)
            assert False
        except ServerException as e:
            self.assertEqual(e.error_code, "ChargeTypeViolation")
            self.assertEqual(
                e.get_error_msg(),
                "The operation is not permitted due to charge type of the instance.")


class TestECSInstancesResource(BaseTest):
    def test_ecs_instances(self):
        self.assertIsInstance(self.resource.instances, ECSInstancesResource)

    def test_iterator(self):
        self.assertIsInstance(self.resource.instances._iterator(), ResourceCollection)

    def test_all(self):
        response = self.resource.instances.all()
        self.assertEqual(len(list(response)), 3)

    def test_filter_with_error_instance_id(self):
        response = self.resource.instances.filter(InstanceId="11111111111")  # <ResourceCollection []>
        self.assertEqual(len(list(response)), 0)
        response = self.resource.instances.filter(Status="Stopped")  # <ResourceCollection [...]>
        self.assertEqual(len(list(response)), 2)

    def test_filter_with_instance_id(self):
        response = self.resource.instances.filter(InstanceId="i-bp162a07bhoj5skna4zj")
        self.assertEqual(len(list(response)), 1)

    def test_limit_with_error_data(self):
        try:
            response = self.resource.instances.limit("hi")
            assert False
        except ValueError as e:
            self.assertEqual(
                e.args[0],
                "The params of limit must be positive integers")

        try:
            response = self.resource.instances.limit(-10.5)
            assert False
        except ValueError as e:
            self.assertEqual(
                e.args[0],
                "The params of limit must be positive integers")

    def test_limit(self):
        response = self.resource.instances.limit(1)
        self.assertEqual(len(list(response)), 1)

    def test_page_size_with_error_data(self):
        try:
            response = self.resource.instances.page_size("hi")
            assert False
        except ValueError as e:
            self.assertEqual(
                e.args[0],
                "The params of page_size must be positive integers")

        try:
            response = self.resource.instances.page_size("-10.5")
            assert False
        except ValueError as e:
            self.assertEqual(
                e.args[0],
                "The params of page_size must be positive integers")

    def test_page_size(self):
        response = self.resource.instances.page_size(1)
        self.assertEqual(len(list(response)), 3)

    def test_pages(self):
        response = self.resource.instances.pages()
        self.assertEqual(len(list(response)), 1)


class TestResourceCollection(BaseTest):

    def test_handler(self):
        client = self.resource._raw_client
        resource_collections = ResourceCollection(client)
        response = resource_collections.handler_desc_instance_request()
        self.assertEqual(response.get("PageNumber"), 1)

    def test_pages(self):
        client = self.resource._raw_client
        resource_collections = ResourceCollection(client)
        response = resource_collections.pages()
        self.assertEqual(len(list(response)), 1)

    def test_repr(self):
        client = self.resource._raw_client
        resource_collections = ResourceCollection(client)
        self.assertTrue(
            str(resource_collections).startswith("<ResourceCollection"))

    def test_iter(self):
        client = self.resource._raw_client
        resource_collections = ResourceCollection(client)
        self.assertIsInstance(resource_collections, Iterable)


if __name__ == '__main__':
    unittest.main()