import os
import json
import logging

from kafka import KafkaProducer


class TransactionProducer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.broker = os.getenv(
            "KAFKA_BROKERS",
            "localhost:19092"
        )

        self.producer = KafkaProducer(
            bootstrap_servers=[self.broker],
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
            acks="all",
            retries=5
        )

    def onsuccess(self, record_metadata):
        self.logger.info(
            f"Enviado topic={record_metadata.topic} "
            f"partition={record_metadata.partition} "
            f"offset={record_metadata.offset}"
        )

    def on_error(self, excp):
        self.logger.error(f"Erro ao enviar: {excp}")

    def send_transaction(self, transaction_data):
        try:
            future = self.producer.send(
                "transactions.created",
                value=transaction_data
            )

            future.add_callback(self.onsuccess)
            future.add_errback(self.on_error)

            self.logger.info(
                f"Transação enviado para o enfileirado: {transaction_data}"
            )

        except Exception as e:
            self.logger.error(e)