import os
import json
import logging

from kafka import KafkaProducer


class TransactionProducer:
    _instance = None
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        self.broker = os.getenv(
            "KAFKA_BROKERS",
            "kafka:19092"
        )

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=[self.broker],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",
                retries=5
            )
            self.logger.info(f"Conectado ao Kafka broker em {self.broker}")
        except Exception as e:
            self.logger.error(f"Erro ao inicializar o produtor Kafka: {e}")

    @classmethod
    def get_instance(cls):
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def onsuccess(self, record_metadata):
        self.logger.info(
            f"Enviado topic={record_metadata.topic} "
            f"partition={record_metadata.partition} "
            f"offset={record_metadata.offset}"
        )

    def on_error(self, excp):
        self.logger.error(f"Erro ao enviar: {excp}")

    @staticmethod
    def send_transaction(transaction_data):
        print(f"Enviando transação para Kafka: {transaction_data}", flush=True)
        service = TransactionProducer.get_instance()

        if not service.producer:
            print("Produtor Kafka não inicializado.", flush=True)
            service.logger.error("Produtor Kafka não inicializado.")
            return
        

        try:
            print(f"Usando broker: {service.broker}", flush=True)
            future = service.producer.send(
                "transactions.created",
                value=transaction_data
            )

            future.add_callback(service.onsuccess)
            future.add_errback(service.on_error)

            service.producer.flush()

            service.logger.info(
                f"Transação enviado para o enfileirado: {transaction_data}"
            )

        except Exception as e:
            service.logger.error(e)