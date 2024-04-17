Big thanks to Thomas Kuther (tkuther) for initial kubernetes code snippet (https://gist.github.com/tkuther/eeb7d4c3dc536fc28250f3a91beef179)

TODO: automatize manual runs of step 2

Steps:
(pod is 'ralph-b459944dc-2xrtn' (it may change), namespace is 'ralph' (this one does not change))

Step 1: apply ymls
    kubectl create namespace ralph
    kubectl apply -f . -n ralph

Step 2: execute initialization scripts:

    kubectl exec -n ralph ralph-b459944dc-2xrtn -- /var/local/ralph/docker-entrypoint.sh init
    kubectl exec -n ralph ralph-b459944dc-2xrtn -- ralphctl collectstatic        

Step 3: if you do not have a proper ingress, expose the pod to localhost ( only for dev purposes)
    
    put entry in hosts: 127.0.0.1 ralph.ss.es
    
    kubectl port-forward ralph-b459944dc-2xrtn 8083:80  -n ralph

Step 4: Ralph is available in with user and password ralph/ralph
    http://ralph.ss.es:8083