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
        

#Namespaces
call_params = "/api/v1/namespaces"
kube_api_url = "http://localhost:8001"
resj = json.loads(call_kube_api(kube_api_url,call_params))
msgs = "PODS STATUS:\n"
pod_msgs = []


for item in resj["items"]:

    res = json.loads(call_kube_api("%s/%s/pods" % (kube_api_url,item["metadata"]["selfLink"])))
    container_msg = []
    
    for pod_item in res["items"]:
        
        if "kubernetes.io/created-by" in pod_item["metadata"]["annotations"]:
            
            service_name = json.loads(pod_item["metadata"]["annotations"]["kubernetes.io/created-by"])["reference"]["name"]
            cont_msgs = []
            
            for cs in pod_item["status"]["containerStatuses"]:

                cs_details = None

                if cs["restartCount"]==0 and cs["ready"]==True:
                    pass
                elif cs["restartCount"]>0 and cs["ready"]==True:
                    cs_details = json.dumps(cs,indent=4)
                else:
                    cs_details = json.dumps(cs,indent=4)

                if cs_details is not None:
                    cont_msgs.append({cs_details})
                
        container_msg.append({service_name:cont_msgs})

    pod_msgs.append(container_msg)

for pod_msg in pod_msgs:
    for msg_ar in pod_msg:
        for pod_name,v in msg_ar.items():
            pod_set = False
            pod = "POD NAME:\t%s\n" % pod_name
            for msg in v:
                if len(msg) > 0:
                    if pod_set == False:
                        lmsg = "%s\t%s\n" % (pod,msg.pop())
                        msgs = msgs + lmsg
                        pod_set = True
                    else:
                        lmsg = "\t%s\n" % msg.pop()
                        msgs = msgs + lmsg
verbose = True

if verbose == True:
    print msgs

set_post_on_slack = True

if set_post_on_slack == True:
    post_on_slack(slack_channel,msgs)





