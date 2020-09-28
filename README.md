# dyna-api-test
DynaTrace Config API test

This is a Python based solution for automatically updating Dynatrace [Management Zones](https://www.dynatrace.com/support/help/how-to-use-dynatrace/management-zones/ "Management Zones").

This repository contains the following:
1. a YAML file which holds descriptions for Management Zones Names & Rules 
2. a basic Python script to:
   ⋅⋅⋅Accept as Input and read above YAML file
   ⋅⋅⋅Get Current Lists of Management Zones IDs/Names
   ⋅⋅⋅Compare Current List against YAML included updates/new definitions
   ⋅⋅⋅Modifies Management Zone structure by updating existing management Zones or creating new ones by interacting with Dynatrace [Config API](https://www.dynatrace.com/support/help/dynatrace-api/configuration-api/) based on a [ReadWrite API TOKEN](https://www.dynatrace.com/support/help/dynatrace-api/environment-api/tokens/post-new-token/ "ReadWrite API TOKEN)