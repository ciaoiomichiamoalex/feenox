from dataclasses import astuple, dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal

from core import Querier, get_logger
from .constants import (PATH_CFG, PATH_LOG, PATH_RES, QUERY_CHECK_DUPLICATE, QUERY_GET_DOCUMENTS,
                        QUERY_GET_LAST_TOLL_DATE, QUERY_GET_TOLL_GROUPS, QUERY_INSERT_DOCUMENT,
                        QUERY_INSERT_TOLL, QUERY_INSERT_TOLL_GROUPS)
from .feenox import Feenox

feenox: Feenox = Feenox(PATH_CFG)
logger = get_logger(PATH_LOG, __name__)


@dataclass
class Toll:
    """
    The Toll object represents all the information retrieved from daily and invoice tolling search.
    """
    id: str
    toll_country: str
    toll_group: str
    toll_genre: str
    toll_source: str | None
    acquisition_date: datetime
    customer_code: str
    contract_code: str
    sign_of_transaction: str
    net_amount: Decimal
    gross_amount: Decimal
    vat_rate: Decimal
    currency_code: str
    exchange_rate: Decimal | None
    network_code: str | None
    entry_gate_code: str | None
    entry_gate_description: str | None
    entry_date: datetime | None
    exit_gate_code: str
    exit_gate_description: str
    exit_date: datetime
    distance: Decimal | None
    device_type: str
    device_serial_number: str
    device_service_pan: str | None
    vehicle_plate: str
    vehicle_country: str
    vehicle_euro_class: str | None
    tariff_class: str | None
    invoice_article: str | None
    invoice_number: str | None
    invoice_date: datetime | None
    global_identifier: str = field(init=False)
    recording_date: datetime

    def __post_init__(self) -> None:
        """
        Generate the global identifier from the stored toll information passed to the class constructor.
        """
        self.global_identifier = '#'.join(
            var.strftime('%Y%m%d%H%M%S')
            if isinstance(var, datetime)
            else str(var.quantize(Decimal('1e-5'))).replace('.', '').rjust(11, '0')
            if isinstance(var, Decimal)
            else str(var)
            for var in (
                self.toll_group,
                self.toll_genre,
                self.acquisition_date,
                self.customer_code,
                self.contract_code,
                self.sign_of_transaction,
                self.net_amount,
                self.gross_amount,
                self.vat_rate,
                self.exchange_rate,
                self.network_code,
                self.entry_gate_code,
                self.entry_date,
                self.exit_gate_code,
                self.exit_date,
                self.device_serial_number,
                self.device_service_pan,
                self.invoice_number,
                self.invoice_date
            ) if var is not None
        )


@dataclass
class Document:
    """
    The Document object represents all the information retrieved from document search.
    """
    id: str
    customer_code: str
    company_name: str
    filename: str
    document_date: date
    publication_date: date
    document_type: str
    document_category: str | None
    recording_date: datetime


def save_toll_groups() -> None:
    """
    Saves all new toll groups retrieved from API call and not yet saved on database.
    """
    querier: Querier = Querier(PATH_CFG, save_changes=True)
    response = feenox.get_toll_groups()
    toll_groups = [var.code for var in querier.run(QUERY_GET_TOLL_GROUPS)]

    items = [item for item in response if item['tollsGroup'] not in toll_groups]
    if items: logger.info('found %d new toll groups %s', len(items), [item['tollsGroup'] for item in items])
    else: logger.info('no new toll group found... %d records already saved on database', len(toll_groups))

    for item in items:
        querier.run(QUERY_INSERT_TOLL_GROUPS, item['tollsGroup'], item['tollsGroupDescription'].strip().upper())
    del querier


def save_tolls(toll_genre: str,
               job_begin: datetime = datetime.now()) -> None:
    """
    Saves all tolls retrieved from API call by filtering on toll genre and by checking duplicates.

    :param toll_genre: The toll genre that indicates daily (P) or invoice (D) tolls.
    :type toll_genre: str
    :param job_begin: The timestamp of the job starting.
    :type job_begin: datetime
    """
    querier: Querier = Querier(PATH_CFG, save_changes=True)

    date_from, current_date = querier.run(QUERY_GET_LAST_TOLL_DATE, toll_genre).fetch(Querier.FETCH_VAL), date.today()
    if not date_from or date_from.date() > current_date:
        date_from = current_date - timedelta(days=90)
        logger.info('invalid or empty latest saved toll date... starting search from last 90 days (%s)', date_from)
    else:
        date_from = date_from.date()
        logger.info('starting toll search from latest saved toll date... (%s)', date_from)

    while date_from < current_date:
        date_to = min(date_from + timedelta(days=7), current_date)

        items = (feenox.get_invoice_tolls(tolls_date=(date_from, date_to))
                if toll_genre == 'D'
                else feenox.get_daily_tolls(tolls_date=(date_from, date_to)))
        logger.info('searching toll of genre %s from date %s to %s... found %d records.',
                    toll_genre, date_from, date_to, len(items))
        # convert date field in datetime object and amount field in decimal object
        for item in items:
            toll: Toll = Toll(
                id=item['id'],
                toll_country=item['nation'],
                toll_group=item['toll_group_code'],
                toll_genre=item['type'],
                toll_source=item['filename'] if toll_genre == 'P' else None,
                acquisition_date=datetime.fromisoformat(item['acquisition_date']),
                customer_code=item['customer_code'],
                contract_code=item['contract_code'],
                sign_of_transaction=item['sign_of_transaction'],
                net_amount=Decimal(str(item['amount_no_vat'])),
                gross_amount=Decimal(str(item['amount_including_vat'])),
                vat_rate=Decimal(str(item['vat'])),
                currency_code=item['currency_code'],
                exchange_rate=Decimal(str(item['exchange_rate'])) if item['exchange_rate'] else None,
                network_code=item['network_code'],
                entry_gate_code=item['entry_global_gate_identifier'],
                entry_gate_description=item['entry_global_gate_identifier_description'],
                entry_date=datetime.fromisoformat(item['entry_timestamp']) if item['entry_timestamp'] else None,
                exit_gate_code=item['exit_global_gate_identifier'],
                exit_gate_description=item['exit_global_gate_identifier_description'],
                exit_date=datetime.fromisoformat(item['exit_timestamp']),
                distance=Decimal(str(item['km'])) if item['km'] else None,
                device_type=item['device_type'],
                device_serial_number=item['obu'],
                device_service_pan=item['pan_number'],
                vehicle_plate=item['vehicle_plate'],
                vehicle_country=item['vehicle_country'],
                vehicle_euro_class=item['vehicle_euro_class'],
                tariff_class=item['vehicle_tariff_class'],
                invoice_article=item['invoice_article'] if toll_genre == 'D' else None,
                invoice_number=item['invoice_nr'] if toll_genre == 'D' else None,
                invoice_date=datetime.fromisoformat(item['invoice_date']) if toll_genre == 'D' else None,
                recording_date=job_begin
            )

            is_duplicate = querier.run(QUERY_CHECK_DUPLICATE, toll.id, toll.global_identifier).fetch(Querier.FETCH_ONE)
            if is_duplicate.nr_id:
                # duplicate on id field is ok, means that row is already saved
                logger.warning('discarding toll for error on CHECK_DUPLICATE... id already saved! (%s)', toll.id)
            elif is_duplicate.nr_global_identifier:
                # duplicate on global identifier means that row is really a duplicate
                logger.error('discarding toll for error on CHECK_DUPLICATE... global identifier already saved! (%s)', toll.global_identifier)
            elif querier.run(QUERY_INSERT_TOLL, *astuple(toll)).rows != 1:
                logger.critical('error on saving toll record with id %s... check the database connection!', toll.id)

        date_from = date_to
    del querier


def save_documents(document_type: str,
                   document_category: str = None,
                   job_begin: datetime = datetime.now()) -> None:
    """
    Saves and download all documents information from API call by filtering on document type and category.

    :param document_type: The document type to be searched.
    :type document_type: str
    :param document_category: The document category to be searched.
    :type document_category: str
    :param job_begin: The timestamp of the job starting.
    :type job_begin: datetime
    """
    querier: Querier = Querier(PATH_CFG, save_changes=True)
    logger.info('starting search documents with type %s%s', document_type,
                f' and category {document_category}' if document_category else '')
    response = feenox.get_documents(document_type, document_category)['documents']
    documents = [var.id for var in querier.run(QUERY_GET_DOCUMENTS)]

    # saving only document not yet in database, by filtering on document id
    items = [item for item in response if item['documentId'] not in documents]
    if items: logger.info('found %d new documents %s', len(items), [item['documentId'] for item in items])
    else: logger.info('no new document found... %d records already saved on database', len(documents))
    for item in items:
        # convert date field in date object
        document: Document = Document(
            id=item['documentId'],
            customer_code=item['customer'],
            company_name=item['companyName'],
            filename=item['fineName'],
            document_date=date.fromisoformat(item['documentDate']),
            publication_date=date.fromisoformat(item['documentPublicationDate']),
            document_type=item['documentType']['name'],
            document_category=item['documentCategory']['name'] if item['documentCategory'] else None,
            recording_date=job_begin
        )

        if querier.run(QUERY_INSERT_DOCUMENT, *astuple(document)).rows != 1:
            logger.critical('error on saving document record with id %s... check the database connection!', document.id)
        else:
            fou = feenox.download_document(document.id, PATH_RES)
            logger.info('downloaded document locally (%s)', fou.as_posix())
    del querier
