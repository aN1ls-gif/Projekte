kubectl apply -f Yaml_files/ConfigMap.yaml
kubectl apply -f Yaml_files/Secrets.yaml
kubectl delete deployments --all
kubectl apply -f Yaml_files/Dashboard.yaml