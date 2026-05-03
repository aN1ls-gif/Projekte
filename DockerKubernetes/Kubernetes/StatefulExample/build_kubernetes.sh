# create CongifMap
kubectl apply -f Yaml_files/ConfigMap.yaml
# create Secrets
kubectl apply -f Yaml_files/Secrets.yaml
# create storage class and pvc for dynamic provisioning
kubectl apply -f Yaml_files/PersistentStorage.yaml
# create Stateful MySQL Server
kubectl apply -f Yaml_files/MySQL.yaml
# create Stateless Dashboard
kubectl apply -f Yaml_files/Dashboard.yaml
