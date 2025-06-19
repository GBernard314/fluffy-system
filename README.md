# fluffy-system


prerequisite : 
> sudo apt install nfs-common -y

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


acces minio kubectl logs minio-deployment-_574959fd49-ld6b9_