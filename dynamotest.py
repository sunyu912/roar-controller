import boto
import time
from boto.dynamodb2.items import Item
from boto.dynamodb2.table import Table



def save_benchmark_test_record(containerId, instanceType, testId):
	BenchmarkTable = Table('BenchmarkRecord')

	BenchmarkTable.put_item(data={
		'containerId': containerId,
		'timestamp': int(time.time()),
		'instanceType' : instanceType,
		'testId': testId,
	})


save_benchmark_test_record("newtest", "t1.micro", "tete")