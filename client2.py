#!/bin/env python

import os,sys,select,pprint
from slackclient import SlackClient
from logbook import FileHandler, Logger
from subprocess import call,Popen,PIPE,STDOUT

user_slack_token = "mytoken"
slack_channel = "#platforms-ngen-status"

logger = Logger('[Slack Call]')
log_handler = FileHandler('/tmp/slack-call2.log')
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
    #kube_call = Popen([cmd_str],stdout=PIPE,stderr=PIPE,shell=True)
    kube_call = Popen([cmd_str],stdout=PIPE,stderr=STDOUT,shell=True)
    kube_call_output = kube_call.communicate()[0]
    kube_call.stdout.close()
    
    return kube_call_output

    
calls_list = ["describe nodes","get nodes","get pods"]
kubemongodir = "/home/folpindo/projects/go/src/github.com/folpindo/myaws/prod/kube-aws/kube-ams-mongo-production"
kubeamsdir = "/home/folpindo/projects/go/src/github.com/folpindo/myaws/prod/kube-aws/kube-ams-production"
kube_pod_details = [
    {'dir':kubemongodir,'cluster':'mongo-single'},
    {'dir':kubeamsdir,'cluster':'amspod-prod'}
]

for pod_details in kube_pod_details:
    result=None
    for cmd in calls_list:
        result = kube_cmd(pod_details["dir"],"kubeconfig",pod_details["cluster"],cmd)
        if result is not None:
            logger.info(result)
            post_on_slack(slack_channel,result)
                
            
env = Popen(["env"],stdout=PIPE,stderr=STDOUT,shell=True)
env_out = env.communicate()[0]
env.stdout.close()
logger.info(env_out)
