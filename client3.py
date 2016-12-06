#!/bin/env python

import os,sys,select,pprint,urllib2,json
from slackclient import SlackClient
from logbook import FileHandler, Logger
from subprocess import call,Popen,PIPE,STDOUT

user_slack_token = "mytoken"
slack_channel = "#platforms-ngen-status"

logger = Logger('[Slack Call]')
log_handler = FileHandler('/tmp/slack-call3.log')
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

#call_params = "/api/v1/namespaces/amspod-prod/secrets"
#call_params = "/api/v1/nodes"
#call_params = "/api/v1/nodes/ip-172-50-0-226.us-west-2.compute.internal"
#call_params = "/api/v1/namespaces/amspod-prod/pods"

#Namespaces
call_params = "/api/v1/namespaces"
kube_api_url = "http://localhost:8001"
resj = json.loads(call_kube_api(kube_api_url,call_params))

for item in resj["items"]:
    res = json.loads(call_kube_api("%s/%s/pods" % (kube_api_url,item["metadata"]["selfLink"])))
    
    #print json.dumps(res,indent=4,sort_keys=True)
    #sys.exit()
    #continue
    for pod_item in res["items"]:
        service_name = json.loads(pod_item["metadata"]["annotations"]["kubernetes.io/created-by"])["reference"]["name"]
        for cs in pod_item["status"]["containerStatuses"]:
            print "Service Name: %s, Pod Name: %s, Restart: %s, Ready: %s Started at: %s" \
                % (
                    service_name,
                    cs["name"],
                    cs["restartCount"],
                    cs["ready"],
                    cs["state"]["running"]["startedAt"]
                )
            
    sys.exit()

"""
    #if item["status"]["phase"] == "Active":
    get_params = "/api/v1/namespaces"
    item_res = json.loads(call_kube_api(kube_api_url,get_params))
    for i  in item_res["items"]:
        base_get_params = "/api/v1/namespaces"
        get_params = "%s/%s/pods" % (base_get_params,item["metadata"]["name"])
        res = json.loads(call_kube_api(kube_api_url,get_params))
        for pod_item in res["items"]:
            for cs in pod_item["status"]["containerStatuses"]:
                print "Service Name: %s, Restart: %s, Ready: %s Started at: %s" \
                    % (
                        cs["name"],
                        cs["restartCount"],
                        cs["ready"],
                        cs["state"]["running"]["startedAt"]
                    )
            
"""
sys.exit()



