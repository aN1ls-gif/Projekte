# create CongifMaps
kubectl apply -f ConfigMaps/Selenium.yaml
kubectl apply -f ConfigMaps/Scraper.yaml

# create the Storage Class
kubectl apply -f StorageClasses/Custom_Storageclass.yaml

# create the PVCs
kubectl apply -f Volumes/MainPath_PVC.yaml


## Create the Deployments which also hold and create the Pods
# create and expose the selenium server
kubectl apply -f Deployments/Selenium.yaml
kubectl apply -f Services/SeleniumServer.yaml
# kubectl apply -f StatefulSets/Selenium.yaml

# kubectl wait --for=condition=Running pod/selenium-chrome-server
# The selenium chrome server is no longer an independant deployment/pod/container, but a sidecar container of the scrapper deployment/pod/container
kubectl apply -f Deployments/Scraper.yaml
kubectl apply -f Deployments/ETL.yaml
kubectl apply -f Deployments/Dashboard.yaml

# create the service
kubectl apply -f Services/Dashboard.yaml # apply this specific service

# behaviour I can not yet explain:
# I know that in order for the non-root user to write to the PV, I need to change the permissions.
# I do so using initContainers.
# However, when the PVs are created with dynamic provisioning, I am denied permision despite the initContainer permission configs.
# Howeber, after a restart the deployments the permission error disappears.
# I assume that the PV is created after(?) the initContainer is run, rendering the permission change useless.
# Therefore, I restart the deployments after everything the scraper and etl pods are running for the first time. this way, the proper PVs should be created
bash Scripts/waiting1.sh # wait for pyspark-etl-deployment to be created
bash Scripts/waiting2.sh # wait for selenium-scraper-deployment to be created
kubectl rollout restart deployments
