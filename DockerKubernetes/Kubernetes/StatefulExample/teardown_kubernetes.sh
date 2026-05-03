kubectl delete storageclass/simple-storage-class
kubectl scale --replicas=0 statefulset/mysql
kubectl delete statefulset/mysql
kubectl delete service/sql-service
kubectl delete service/dashboard-service
kubectl delete deployments --all
kubectl delete pods --all
kubectl delete configmaps/sql-configmap
kubectl delete secrets --all
kubectl delete pvc --all
kubectl delete pv --all
