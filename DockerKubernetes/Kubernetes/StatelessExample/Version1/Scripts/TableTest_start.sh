# create the PVs
kubectl apply -f Volumes/MainPath_PV.yaml

# create the PVCs
kubectl apply -f Volumes/MainPath_PVC.yaml


## Create the Deployments which also hold and create the Pods
# create and expose the selenium server
kubectl apply -f Deployments/TableCheck.yaml
kubectl apply -f Services/TableCheck.yaml