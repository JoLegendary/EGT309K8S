# How to Run:
## Pre-requisite:
- minikube
- wsl/linux
  
Clone repo
> git clone https://github.com/JoLegendary/EGT309K8S.git

> cd EGT309KS

> kubectl apply -f Streamlit.yml

or

> kubectl apply -f Flask.yml

> minikube service gui-service --url
Copy the URL and paste into Web Browser

## Streamlit
Main Function is at Pipeline Shopfloor

Press Input node and wait until it allows you to upload a file

Press Prediction node and wait until it allows you to upload a file (Right side is the file to upload test.csv)

After uploading, press Run Pipeline and wait

Progress Status is on the left of the screen

After pipeline is finished, press Output @ Save and wait, then press Download to download the csv file

## Flask
There's 2 upload function, upload train and test csv to their indicated one

Afterwards press Run Pipeline & Download

You can see the progress status, after pipeline is finished it will download the csv file automatically
