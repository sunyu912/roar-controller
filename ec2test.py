from sodascale import *

conn = EC2Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)






print find_matched_running_test_instance("ami-c9889ca0", "m1.small")
