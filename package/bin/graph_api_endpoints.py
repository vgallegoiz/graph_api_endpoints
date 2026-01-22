from datetime import datetime
import json
import logging
import sys

import import_declare_test
from solnlib import conf_manager, log
from splunklib import modularinput as smi

from GraphAPI import GraphAPI  # Asegúrate de que el archivo se llame GraphAPI.py

ADDON_NAME = "graph_api_endpoints"


def logger_for_input(input_name: str) -> logging.Logger:
    return log.Logs().get_logger(f"{ADDON_NAME.lower()}_{input_name}")


def get_account_info(session_key: str, account_name: str):
    cfm = conf_manager.ConfManager(
        session_key,
        ADDON_NAME,
        realm=f"__REST_CREDENTIAL__#{ADDON_NAME}#configs/conf-graph_api_endpoints_account",
    )
    account_conf_file = cfm.get_conf("graph_api_endpoints_account")  # Nombre coherente con el addon
    credentials = account_conf_file.get(account_name)
    if not credentials:
        raise ValueError(f"Account '{account_name}' not found")
    return credentials.get("client_secret"), credentials.get("client_id")


class Input(smi.Script):
    def __init__(self):
        super().__init__()

    def get_scheme(self):
        scheme = smi.Scheme("graph_api_endpoints")
        scheme.description = "Generic Microsoft Graph API endpoint input"
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False
        return scheme

    def validate_input(self, definition: smi.ValidationDefinition):
        pass

    def stream_events(self, inputs: smi.InputDefinition, event_writer: smi.EventWriter):
        for input_name, input_item in inputs.inputs.items():
            normalized_input_name = input_name.split("/")[-1]
            logger = logger_for_input(normalized_input_name)

            try:
                session_key = inputs.metadata["session_key"]
                log_level = conf_manager.get_log_level(
                    logger=logger,
                    session_key=session_key,
                    app_name=ADDON_NAME,
                    conf_name="graph_api_endpoints_settings",
                )
                logger.setLevel(log_level)
                log.modular_input_start(logger, normalized_input_name)

                # Parámetros del input
                account_name = input_item.get("account")
                tenant_id = input_item.get("tenant_id")
                endpoint = input_item.get("endpoint")
                index = input_item.get("index")
                sourcetype = input_item.get("sourcetype") if input_item.get("sourcetype") else "msgraph:generic"

                if not all([account_name, tenant_id, endpoint, index]):
                    logger.error("Missing required parameters: account, tenant_id, endpoint or index")
                    continue

                # Obtener credenciales
                try:
                    client_secret, client_id = get_account_info(session_key, account_name)
                except Exception as e:
                    logger.error(f"Failed to retrieve credentials for account {account_name}: {e}")
                    continue

                if not all([client_id, client_secret]):
                    logger.error("Client ID or Secret is empty")
                    continue

                logger.info(f"Initializing GraphAPI for input: {normalized_input_name} | Endpoint: {endpoint}")

                # Autenticación y llamada
                graph = GraphAPI(client_id, client_secret, tenant_id)

                try:
                    graph.getAuthToken()
                    logger.info("Access token obtained successfully")
                except Exception as e:
                    logger.error("Failed to authenticate with Microsoft Entra ID")
                    log.log_exception(logger, e, msg_before="Authentication failure")
                    continue

                try:
                    records = graph.getInfo(endpoint)  # ¡Aquí usamos listInfo!
                    logger.info(f"Retrieved {len(records)} records from {endpoint}")
                except Exception as e:
                    logger.error(f"Failed to fetch data from endpoint {endpoint}")
                    log.log_exception(logger, e, msg_before="Graph API request failure")
                    continue

                # Ingestión en Splunk
                if records:
                    current_time = datetime.utcnow().isoformat()

                    for record in records:
                        # Añadimos metadatos útiles
                        record.update({
                            "input_name": normalized_input_name,
                            "graph_endpoint": endpoint
                        })

                        event = smi.Event()
                        event.stanza = input_name
                        event.index = index
                        event.sourcetype = sourcetype
                        event.source = f"msgraph:{normalized_input_name}"
                        event.time = current_time
                        event.data = json.dumps(record, ensure_ascii=False, default=str)

                        event_writer.write_event(event)

                    logger.info(f"Ingested {len(records)} events into Splunk")
                else:
                    logger.warning("No records returned from the endpoint")

                log.modular_input_end(logger, normalized_input_name)

            except Exception as e:
                logger.error("Unexpected error in modular input execution")
                log.log_exception(logger, e, msg_before=f"Critical error in input {normalized_input_name}")

if __name__ == "__main__":
    exit_code = Input().run(sys.argv)
    sys.exit(exit_code)