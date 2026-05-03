POD_NAME=selenium-scraper-deployment
FULL_NAME=`kubectl get pods | grep "$POD_NAME"  | cut -d " " -f1`
# kubectl get pods selenium-chrome-server-deployment-686744bc7d-vjwln --no-headers -o custom-columns=":status.phase"
until false; do
  echo "Waiting for pod $FULL_NAME to be ready..."
  CURRENT_STATUS=`kubectl get pods "$FULL_NAME" --no-headers | cut -d " " -f7`
  echo "$CURRENT_STATUS"
  if [ "$CURRENT_STATUS" = Running ]; then
    break
  else
    sleep 5
  fi
done
echo "Pod $POD_NAME is ready!"