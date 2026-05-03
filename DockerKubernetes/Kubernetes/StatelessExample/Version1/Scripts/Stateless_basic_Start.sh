# create the PVs
kubectl apply -f Volumes/MainPath_PV.yaml

# create the PVCs
kubectl apply -f Volumes/MainPath_PVC.yaml


## Create the Deployments which also hold and create the Pods
# create and expose the selenium server
kubectl apply -f Deployments/Selenium.yaml
kubectl apply -f Services/SeleniumServer.yaml

# kubectl wait --for=condition=Running pod/selenium-chrome-server
# The selenium chrome server is no longer an independant deployment/pod/container, but a sidecar container of the scrapper deployment/pod/container
kubectl apply -f Deployments/Scraper.yaml
kubectl apply -f Deployments/ETL.yaml
kubectl apply -f Deployments/Dashboard.yaml

# create the service
kubectl apply -f Services/Dashboard.yaml # apply this specific service