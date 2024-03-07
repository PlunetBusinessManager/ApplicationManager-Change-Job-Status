from zeep import Client
import sys
import logging, logging.config
import xmltodict


def initiate_logging():
    try: # Trying storing with job
        work_path = sys.argv[1]
        logging.basicConfig(filename=work_path+'\job_change.log', level=logging.DEBUG, format='%(asctime)s %(levelname)-8s %(message)s', )
    except: # otherwise store with application
        work_path = sys.argv[4]
        logging.basicConfig(filename=work_path + '\job_change.log', level=logging.DEBUG,
                            format='%(asctime)s %(levelname)-8s %(message)s', )
    # Settings for ZEEP
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'verbose': {
                'format': '%(name)s: %(message)s'
            }
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'verbose',
            },
        },
        'loggers': {
            'zeep.transports': {
                'level': 'WARNING',  # CHANGE THIS TO DEBUG IF PROBLEMS WITH API CALLS IN SPECIFIC
                'propagate': True,
                'handlers': ['console'],
            },
        }
    })
    logging.info("New Try...")
    logging.debug("This is our work path: "+work_path)


def configuration_retrieval():
    global config_xml
    global order_ep, item_ep, job_ep, customfields_ep

    config_path = sys.argv[4]
    with open(config_path+'\configuration.xml') as fd:
        config_xml = xmltodict.parse(fd.read())

    # API ENDPOINTS
    order_ep = Client(config_xml['configuration']['base_url'] + "DataOrder30?wsdl").service
    item_ep = Client(config_xml['configuration']['base_url'] + "DataItem30?wsdl").service
    job_ep = Client(config_xml['configuration']['base_url'] + "DataJob30?wsdl").service
    customfields_ep = Client(config_xml['configuration']['base_url'] + "DataCustomFields30?wsdl").service


def API_Login():
    global uuid
    logging.info("Logging into Plunet")
    plunetapi = Client(config_xml['configuration']['base_url']+"PlunetAPI?wsdl").service
    try:
        uuid = plunetapi.login(config_xml['configuration']['username'], config_xml['configuration']['password'])
    except:
        logging.error("An error occured while connecting to the API")
        sys.exit()
    if uuid == "refused":
        logging.error("The Login credentials are incorrect")
        sys.exit()
    else:
        logging.debug("Logged in and received uuid: " + str(uuid))


def Retrieve_Sys_Args():
    logging.info("Retrieving System arguments")
    parsed_options = {}
    logging.debug('The following arguments have been received:' + str(sys.argv))

    try:
        parsed_options["infolder"] = sys.argv[1]
        parsed_options["orderno"] = sys.argv[2]
        lang_comb = sys.argv[3]
        logging.debug("Transfer to variables successful")
    except:  # just for testing
        logging.error("No proper parameters received. Aborting...")
        sys.exit()

    # Prettify IN_Folder
    pos_a = parsed_options["infolder"].find("order")
    if pos_a != -1:
        parsed_options["infolder"] = "..\\" + parsed_options["infolder"][pos_a:]
    else:
        parsed_options["infolder"] = "It was not possible to analyse the IN folder"

    langparts = lang_comb.split("/")
    parsed_options["srclanguage"] = langparts[0]
    parsed_options["trglanguage"] = langparts[1]
    logging.debug("Final parsed_options values: " + str(parsed_options))
    return parsed_options


def analyse_jobs(jobs):
    if not jobs.data:
        logging.error("There are no jobs. Aborting...")
        sys.exit()

    acceptable_status_list = [int(item) for item in config_xml['configuration']['actionStatus']['jobStatus']]
    for foundjob in jobs.data:
        if foundjob.status in acceptable_status_list:
            logging.debug("Found actionable job: " + str(foundjob.jobID))
            if foundjob.resourceID == 0:
                logging.debug("No resource has been assigned to job")
                response = job_ep.setJobStatus(uuid, 3, foundjob.jobID, int(config_xml['configuration']['changeStatus']))
                if response.statusCode == 0:
                    logging.info("The following job has been set to WITHOUT INVOICE:" + str(foundjob.jobID))
                if response.statusCode == -45 and "locked by another user" in response.statusMessage:
                    logging.error("The following job was locked by another user: " + str(foundjob.jobID))
                    continue
                    # In version >8.5 you can activate an API Super User that allows you to override any lock
                elif response.statusCode != 0:
                    logging.error("Error (" + str(response.statusMessage) + ") occured for job: " + str(foundjob.jobID))
                    continue
            else:
                logging.debug("Resource found. Checking engagement type")
                response = customfields_ep.getTextmodule(uuid, config_xml['configuration']['typeName'], 2, foundjob.resourceID, "EN")

                if response.statusCode != 0:
                    logging.error(("Error (" + str(response.statusMessage) + ") occured for retrieving resource type"))
                    continue

                resource_type = response.data.selectedValues
                if resource_type[0] in config_xml['configuration']['actionTypes']['actionType']:
                    logging.debug("Found actionable engagement type")
                    response = job_ep.setJobStatus(uuid, 3, foundjob.jobID, int(config_xml['configuration']['changeStatus']))
                    if response.statusCode == 0:
                        logging.info("The following job has been set to WITHOUT INVOICE:" + str(foundjob.jobID))
                    if response.statusCode == -45 and "locked by another user" in response.statusMessage:
                        logging.error("The following job was locked by another user: " + str(foundjob.jobID))
                        continue
                        # In version >8.5 you can activate an API Super User that allows you to override any lock
                    elif response.statusCode != 0:
                        logging.error(
                            "Error (" + str(response.statusMessage) + ") occured for job: " + str(foundjob.jobID))
                        continue
                else:
                    logging.debug("Resource engagement type not actionable, job not updated")
    logging.info("All jobs reviewed")


def get_corresponding_jobs(parsed_options):
    order_id = order_ep.getOrderID(uuid, parsed_options["orderno"]).data
    if order_id == 0:
        logging.warning("No order found. Aborting...")
        sys.exit()
    else:
        logging.debug("Order found: " + str(order_id))

    # Getting the corresponding items for the order
    item_id_resp = item_ep.get_ByLanguage(uuid, 3, order_id, parsed_options["srclanguage"], parsed_options["trglanguage"])
    if item_id_resp.statusCode == 0:
        logging.debug("Respective item found: " + str(item_id_resp.data))
    else:
        logging.error("No item found. Aborting...")
        sys.exit()

    # now retrieving the job objects
    job_objects = job_ep.getJobListOfItem_ForView(uuid, item_id_resp.data, 3)
    analyse_jobs(job_objects)


def main():
    initiate_logging()
    try:
        configuration_retrieval()
        passed_arguments = Retrieve_Sys_Args()
        API_Login()
        get_corresponding_jobs(passed_arguments)
    except:
        logging.debug("Something bad happened and I don't know what it is")


main()
