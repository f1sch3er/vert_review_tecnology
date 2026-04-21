
import os
import logging
from kafka import KafkaProducer


class TransactionProducer:
    def __init__(self, producer):
        self.logger = logging.getLogger(__name__)

        self.broker = os.getenv('KAFKA_BROKER', 'localhost:9092')

        self.producer = KafkaProducer(
            bootstrap_servers=[self.broker],
            value_serializer=lambda v: str(v).encode('utf-8'),
            acks='all',
            retries=5
        )

    def send_transaction(self, transaction_data):
        try:
            future = self.producer.send('transactions', value=transaction_data)
            result = future.get(timeout=10)
            self.logger.info(f"Transação enviada para Kafka: {transaction_data}")
            return result
        
        except Exception as e:
            self.logger.error(f"Erro ao enviar transação para Kafka: {e}")
            return None