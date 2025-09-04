from pathlib import Path

PATH_PRJ = Path(__file__).resolve().parents[2]
PATH_CFG = PATH_PRJ / 'config'
PATH_LOG = PATH_PRJ / 'log'
PATH_RES = PATH_PRJ / 'res'

URL_LOGIN = 'https://lumesia.onelogin.com/oidc/2/token'
URL_TOLL_GROUPS = 'https://my.lumesia.com/fai/api/api/public/ext/getTollGroups'
URL_INVOICE_TOLLS = 'https://my.lumesia.com/fai/api/api/public/ext/searchTolls'
URL_DAILY_TOLLS = 'https://my.lumesia.com/fai/api/api/public/ext/searchDailyTolls'
URL_DOCUMENTS = 'https://my.lumesia.com/fai/api/api/public/ext/findDocuments'
URL_DOWNLOAD_DOCUMENT = 'https://my.lumesia.com/fai/api/api/public/ext/downloadDocumentByUuid'

QUERY_GET_TOLL_GROUPS = """\
    SELECT code
    FROM feenox.toll_group
    ;
"""
QUERY_INSERT_TOLL_GROUPS = """\
    INSERT INTO feenox.toll_group (code, description)
    VALUES (?, ?)
    ;
"""

QUERY_GET_LAST_TOLL_DATE = """\
    SELECT MAX(exit_date) AS max_date
    FROM feenox.toll
    WHERE toll_genre = ?
    ;
"""

QUERY_CHECK_DUPLICATE = """\
    SELECT COUNT(DISTINCT id) AS nr_id,
        COUNT(DISTINCT global_identifier) AS nr_global_identifier
    FROM feenox.toll
    WHERE id = ?
        OR global_identifier = ?
    ;
"""

QUERY_INSERT_TOLL = """\
    INSERT INTO feenox.toll (
        id,
        toll_country,
        toll_group,
        toll_genre,
        toll_source,
        acquisition_date,
        customer_code,
        contract_code,
        sign_of_transaction,
        net_amount,
        gross_amount,
        vat_rate,
        currency_code,
        exchange_rate,
        network_code,
        entry_gate_code,
        entry_gate_description,
        entry_date,
        exit_gate_code,
        exit_gate_description,
        exit_date,
        distance,
        device_type,
        device_serial_number,
        device_service_pan,
        vehicle_plate,
        vehicle_country,
        vehicle_euro_class,
        tariff_class,
        invoice_article,
        invoice_number,
        invoice_date,
        global_identifier,
        recording_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ;
"""

QUERY_GET_DOCUMENTS = """\
    SELECT id 
    FROM feenox.document
    ;
"""
QUERY_INSERT_DOCUMENT = """\
    INSERT INTO feenox.document (
        id,
        customer_code,
        company_name,
        filename,
        document_date,
        publication_date,
        document_type,
        document_category,
        recording_date
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ;
"""
