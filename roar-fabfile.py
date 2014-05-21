from sodascale import *

load_server = "http://driver.roar.zii.io"
roar_instances = []
growl_file = "/Users/yusun/workspace/roar-controller/bm-test.jmx"
container_id = 'sunyu912/bm-1-jetty-servlet'
health_check_url = "http://%s:8080/json"
notes = "Final Experiment Data - 30000"

@experiment("peformance measurement")
def performance_measurement():
    #types = ["m1.small", "m1.medium", "m1.large", "m1.xlarge", "m3.medium", "m3.large", "m3.xlarge", "c1.medium"]
    #types = ["c1.medium", "c1.xlarge", "c3.large", "c3.xlarge"]
    #types = ["c1.medium", "c1.xlarge"]
    #types = ["m1.small", "m1.medium", "m1.large", "m1.xlarge"]
    types = ["c3.large"]
    for type in types:
        test_node.node_config['type'] = type
        run_experiment("Benchmark-%s" % type)


@app_node(ami="ami-310f1158",
          instances=1,
          type="t1.micro",
          security_group="ROAR-Test-Server",
          user='ubuntu',
          ssh_key='/Users/yusun/.ssh/magnum.pem',
          terminate_when_done=False,
          key_pair="magnum")
def test_node(node_state):
    hostname = node_state["host"];
    
    target_throughput = 30000        # 341  1418  2809
    port = 8080

    #run('docker stop $(docker ps -a -q)')
    #run('run-docker-app ' + container_id + ' 8080')
    
    print "Checking to ensure that the container application is running..."
    wait_for_http([health_check_url % hostname])
        
    secondRun = False

    while True:
        generated_test_file = ""    
        f = open(growl_file, 'r')
        for line in f:
            newline = line.replace('{host}', hostname)
            newline = newline.replace('{port}', str(port))
            newline = newline.replace('{throughput}', str(target_throughput))
            generated_test_file += newline
        
        print "Submitting updated load test plan"
        url = load_server + '/v1/roar/test/run'
        files = {'testPlan': ('test_plan.jmx', generated_test_file)}
        payload = {'containerId': container_id, 'instanceType': test_node.node_config['type']}
        r = requests.post(url, files=files, data=payload)
        if r.status_code == 200:
            print "Test plan submitted:"
            print r.text
            data = json.loads(r.text) 
            testId = data['testId']
            print "Status checker: "
            print load_server + "/v1/roar/test/run/" + testId + "/checker"
            save_benchmark_test_record(container_id, test_node.node_config['type'], testId, notes)
            wait_for_load_test_to_complete(testId)
            status = check_load_test_status(testId)
            results = get_load_test_results(status['processedResultModelUrl'])
            peak = results['peakThroughput']
            print 'peak throughptu: ' + str(peak)
            if secondRun:
                break
            if peak < target_throughput * 0.9:
                target_throughput = peak
            else:
                break
        else:
            print "Startup of load generator failed, response code:" + str(r.status_code) + " reason: " + r.text
        secondRun = True
        

def get_load_test_results(resultUrl):
    result = requests.get(resultUrl)
    if result.status_code == 200:
        return json.loads(result.text)
    else:
        raise RuntimeError("invalid test result URL")
   
def check_load_test_status(testId):
    print "Checking status of load test: " + testId
    url = load_server + "/v1/roar/test/run/" + testId
    r = requests.get(url)
    if r.status_code == 200:
        return json.loads(r.text)
    else:
        return null

def wait_for_load_test_to_complete(testId):
    max = 50
    curr = 0
    while curr < max:
        status = check_load_test_status(testId)
        if status['status'] == 'COMPLETED':
            return
        elif status['status'] == 'FAILED':
            raise RuntimeError("the load test failed for an unknown reason")
        time.sleep(10)
        curr += 1
    raise RuntimeError("timed out waiting for the load test to complete")
    