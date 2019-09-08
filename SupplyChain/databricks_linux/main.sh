#!/bin/bash

echo "Supply_Chain";
apt-get -y install git;
pip3 install wheel;
pip3 install databricks-cli;
apt-get -y install expect;
apt-get -y install jq ;
cp /home/site/wwwroot/antenv/bin/databricks /opt/python/3.7.4/bin/;
expect /home/site/wwwroot/SupplyChain/databricks_linux/creds.sh $1 $2;
git clone https://github.com/Prateekagarwal9/supplychain-new;
mkdir test;
pwd > prtk;
databricks workspace import  -f DBC -l SCALA /home/site/wwwroot/supplychain-new/Supply-Chain-Solution.dbc /Supply-Chain-Solution;
databricks fs mkdirs dbfs:/databricks/init/SupplyChain/;
scripts=(
    arima_installation.sh
    prophet_installation.sh
    holtwinter_installation.sh
    lstm_installation.sh
    xgboost_installation.sh
    or_installation.sh
)
for i in "${scripts[@]}"; do
    databricks fs cp $3/SupplyChain/databricks_linux/$i dbfs:/databricks/init/SupplyChain/;
done

jsons=(
    arima.json
    prophet.json
    holtwinter.json
    lstm.json
    xgboost.json
    or.json
    os.json
    timefence.json
)
for i in "${jsons[@]}"; do
    runid=$(databricks jobs create --json-file $3/SupplyChain/databricks_linux/$i);
    echo $runid;
    runidnew=$(echo $runid | jq -r '.job_id');
    echo $runidnew;
    databricks jobs run-now --job-id $runidnew;
done
