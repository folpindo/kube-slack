#!/bin/env python


import os,sys,select,pprint,urllib2,json,boto3
from slackclient import SlackClient
from logbook import FileHandler, Logger
from subprocess import call,Popen,PIPE,STDOUT
from datetime import datetime as dt


user_slack_token = "mytoken"
slack_channel = "#platforms-ngen-status"


logger = Logger('[Slack Call]')
log_handler = FileHandler('/tmp/kube-nodes-status.log')
log_handler.push_application()


def post_on_slack(slack_channel,message):
    sc = SlackClient(user_slack_token)
    sc.api_call(
        "chat.postMessage",
        channel=slack_channel,
        text=message
    )


def kube_cmd (kube_work_dir=None,config="kubeconfig",namespace="default",kube_cmd=None):
    
    if kube_work_dir is None or kube_cmd is None:
        return False
    
    os.chdir(kube_work_dir)
    cmd_str = "kubectl --kubeconfig=%s --namespace=%s %s" % (config,namespace,kube_cmd)
    kube_call = Popen([cmd_str],stdout=PIPE,stderr=STDOUT,shell=True)
    kube_call_output = kube_call.communicate()[0]
    kube_call.stdout.close()
    
    return kube_call_output


def call_kube_api(base_url="http://localhost:8001",get_params=""):
    try:
        req = None
        url = "%s%s" % (base_url,get_params)
        #req = urllib2.Request(url,urllib.urlencode(data))
        req = urllib2.Request(url)
        #req.add_header(token_key,token)
        resp = urllib2.urlopen(req)

        return resp.read()
        
    except urllib2.HTTPError as e:
        logger.error("%s: %s" % (call_params,e))


def get_cpu_utilization(ec2InstanceId):
    client = boto3.client('cloudwatch')
    response = client.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        StartTime=dt(2016,12,1),
        EndTime=dt.utcnow(),
        Period=3600,
        Statistics=["Average","SampleCount","Minimum","Maximum"],
        Dimensions=[{"Name":"InstanceId","Value":ec2InstanceId}]
    
    )
    return response["Datapoints"]




#Nodes

call_params = "/api/v1/nodes"
kube_api_url = "http://localhost:8001"
resj = json.loads(call_kube_api(kube_api_url,call_params))
node_problems = []
cpuStatProblem = []
for status in resj["items"]:

    instanceId = status["spec"]["externalID"]
    cpuUtilStatus = get_cpu_utilization(instanceId)
    for metric in cpuUtilStatus:
        if metric["Average"] > 61:
            metric["Timestamp"] = str(metric["Timestamp"])
            cpuStatProblem.append({"instanceId":instanceId,"metric":"CPUUtilization","details":metric})

    if len(cpuStatProblem) > 0:
        post_on_slack(slack_channel, json.dumps(cpuStatProblem,indent=4))

    problems = []
    
    for cond in status["status"]["conditions"]:
        if cond["type"] == "OutOfDisk" and cond["status"]=="True":
                problems.append(json.dumps(cond,indent=4))
        if cond["type"] == "MemoryPressure" and cond["status"]=="True":
            problems.append(json.dumps(cond,indent=4))
        if cond["type"] == "DiskPressure" and cond["status"]=="True":
            problems.append(json.dumps(cond,indent=4))
        if cond["type"] == "Ready" and cond["status"]=="False":
            problems.append(json.dumps(cond,indent=4))

    if len(problems) > 0:
        node_problems.append({"instanceId":instanceId,"problems":problems,"details":status})
        
if len(node_problems) > 0:
        details = json.dumps(node_problems,indent=4)
        post_on_slack(slack_channel, details)
        print details





