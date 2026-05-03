kubectl delete service streamlit-dashboard-service
kubectl delete svc/selenium-web-service

kubectl delete deployment --all
kubectl delete pods --all
kubectl delete sc/simple-storage-class
kubectl delete pvc --all
# kubectl delete pv --all # due to the setting in the storage class, the pv will be automatically deleted

kubectl delete configmaps/selenium-server-configs
kubectl delete configmaps/selenium-scraper-configs