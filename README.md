# fluffy-system


prerequisite : 
> sudo apt install nfs-common -y
> sudo snap install docker

1. get kubectl
> sudo snap install kubectl --classic
and k3s :
> curl -sfL https://get.k3s.io | sh -

#### If you get an error
> curl -sfL https://get.k3s.io | sh -

Dont forget to copy the .kube config
> mkdir -p ~/.kube
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown $USER:$USER ~/.kube/config

install CSI drivers
> kubectl apply -f k3s/install-driver.yaml 

2. apply the config for the pv (if you need, create the actual directory where you need it to be)
    - mkdir -p /yourmountpointforpv
    - maybe chmod 777 it
    - then 
    > kubectl apply -f k3s/pv.yaml

3. apply the deployment
    > kubectl apply -f k3s/deployment.yaml

create a secret for creds 
> kubectl create secret generic fuzzy-system-creds --from-env-file=k3s/creds.env
kubectl delete secret --all ; kubectl create secret generic fuzzy-system-creds --from-env-file=k3s/creds.env

acces minio kubectl logs minio-deployment-_574959fd49-ld6b9_

Now the infra should work

Create the scrapper / feeder code and package it 

sudo docker build -f Dockerfile.scrapper -t my-scrapper:latest . ; sudo docker save -o my-scrapper.tar my-scrapper:latest ; sudo k3s ctr images import my-scrapper.tar ; kubectl delete -f k3s/scrapper.yaml ; kubectl apply -f k3s/scrapper.yaml ; kubectl get all

sudo docker build -f Dockerfile.processing -t my-processing:latest . ; sudo docker save -o my-processing.tar my-processing:latest ; sudo k3s ctr images import my-processing.tar ; kubectl delete -f k3s/processing.yaml ; kubectl apply -f k3s/processing.yaml ; sleep 5 ; kubectl get all


kubectl exec -it pod/minio-deployment-5bf87466c9-d5gmq -- /bin/sh
ls -l /data
touch /data/testfile