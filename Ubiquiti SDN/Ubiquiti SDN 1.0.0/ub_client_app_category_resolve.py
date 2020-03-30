"""
Copyright © 2020 Forescout Technologies, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import logging

credentials = {}
controller_details = {}
response = {}

credentials["username"] = params["connect_ubiquitisdn_username"]
credentials["password"] = params["connect_ubiquitisdn_password"]

controller_details["address"] = params["connect_ubiquitisdn_controller_address"]
controller_details["port"] = params["connect_ubiquitisdn_controller_port"]
controller_details["site"] = params["connect_ubiquitisdn_site_name"]

code, client = UB_API_NONOO.UB_HTTP_CLIENT(credentials, controller_details)

ubiquiti_category_map = {
    "0": "Instant messengers",
    "1": "Peer-to-peer networks",
    "3": "File sharing services and tools",
    "4": "Media streaming services",
    "5": "Email messaging services",
    "6": "VoIP services",
    "7": "Database tools",
    "8": "Online games",
    "9": "Management tools and protocols",
    "10": "Remote access terminals",
    "11": "Tunneling and proxy services",
    "12": "Investment platforms",
    "13": "Web services",
    "14": "Security update tools",
    "15": "Web instant messengers",
    "17": "Business tools",
    "18": "Network protocols",
    "19": "Network protocols",
    "20": "Network protocols",
    "23": "Private protocols",
    "24": "Social networks",
    "255": "Unknown"
}


def human_bytes(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
        nbytes /= 1024.
        i += 1
        f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])


logging.debug("Login to Ubiquiti Controller [{}] returned code [{}]".format(controller_details["address"], code))

if code == 200:
    logging.debug("Login Successful")
    properties = {}
    if "mac" in params:
        if "connect_ubiquitisdn_role" in params:
            if params["connect_ubiquitisdn_role"] == "Client":
                composite_list = []
                mac = ':'.join(params["mac"][i:i + 2] for i in range(0, 12, 2))
                logging.debug("Attempting API Query for MAC [{}]".format(mac))
                query_code, query_results = UB_API_NONOO.UB_QUERY_CLIENT_APPS(client, controller_details, mac)
                app_details = query_results["data"][0]['by_cat']
                logging.debug("API Query returned code [{}] and response [{}]".format(query_code, query_results))

                cat_by_traffic = {}
                # We need to first iterate through the API result and consolidate duplicate entries
                for entry in app_details:
                    cat_id = entry['cat']
                    if str(cat_id) in ubiquiti_category_map:
                        category_name = ubiquiti_category_map[str(cat_id)]
                    else:
                        category_name = "Unknown"

                    traffic = entry['rx_bytes'] + entry['tx_bytes']
                    logging.debug(category_name + " " + str(traffic))

                    if category_name in cat_by_traffic:
                        recorded_traffic = cat_by_traffic[category_name]
                        combined_traffic = recorded_traffic + traffic
                        cat_by_traffic[category_name] = combined_traffic
                    else:
                        cat_by_traffic[category_name] = traffic
                # Form the composite property response object from our de-duped dict
                for category in cat_by_traffic:
                    composite_entry = {}
                    composite_entry["application_category"] = category
                    composite_entry["application_traffic"] = human_bytes(cat_by_traffic[category])
                    composite_list.append(composite_entry)
                properties["connect_ubiquitisdn_client_application_usage"] = composite_list
                response["properties"] = properties

            else:
                response["error"] = "This property only applies to Ubiquiti SDN Discovered Clients."
        else:
            response["error"] = "Ubiquiti SDN Role determination is required to resolve this property."
    else:
        response["error"] = "No mac address to query the endpoint."
else:
    response["error"] = "API Connection Failed, check configuration."

logging.debug("Returning response object to infrastructure. response=[{}]".format(response))
