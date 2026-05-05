import os
import json
import logging
from django.core.management.base import BaseCommand
from kafka import KafkaConsumer
from django.db import transaction

from accounts.models import Account
from transactions.models import Transaction

class Command(BaseCommand):
    help = 'Inicia o consumidor Kafka para processar transações'

    def handle(self, *args, **options):
        
        self.broker = os.getenv(
            "KAFKA_BROKERS",
            "kafka:9092"
        )


        consumer = KafkaConsumer(
            'transactions.created',
            bootstrap_servers=[self.broker],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            group_id='transaction-consumers'
        )

        for message in consumer:
            try:
                payload = message.value
                self.process_transaction(payload)
                consumer.commit()
            except Exception as e:  
                logging.error(f"Erro ao processar mensagem: {e}")
                
    
    def process_transaction(self, payload):
        tx_type = str(payload.get('transfer_type')).upper()

        if tx_type == 'DEPOSIT':
            self._handle_deposit(payload)
        else:
            self._handle_transfer(payload)

    def _handle_deposit(self, payload):
        transaction_id = payload.get('transaction_id')
        with transaction.atomic():
            tx = Transaction.objects.select_for_update().get(id=transaction_id)
            
            dest_acc = tx.to_account
            dest_acc.balance += tx.amount 
            dest_acc.save()

            tx.transfer_status = 'SETTLED'
            tx.save()

    def _handle_transfer(self, payload):
        transaction_id = payload.get('transaction_id')
        payload_key = str(payload.get('idempotency_key')) 

        try:
            with transaction.atomic():
                tx = Transaction.objects.select_for_update().get(id=transaction_id)

                if tx.transfer_status in ['SETTLED', 'REJECTED']:
                    logging.info(f"Transação {transaction_id} já finalizada anteriormente.")
                    return

                if str(tx.idempotency_key) != payload_key:
                    logging.error(f"Divergência de Idempotência: Banco({tx.idempotency_key}) vs Payload({payload_key})")
                    raise Exception("Idempotency mismatch")

                source_acc = tx.from_account
                dest_acc = tx.to_account

                if source_acc.balance < tx.amount:
                    tx.transfer_status = 'REJECTED'
                    logging.warning(f"Saldo insuficiente na conta {source_acc.id}")
                else:
                    if tx.amount <= 1000:
                        tx.transfer_status = 'SETTLED'
                        
                        source_acc.balance -= tx.amount
                        dest_acc.balance += tx.amount
                        
                        source_acc.save()
                        dest_acc.save()
                        logging.info(f"Saldos atualizados: Origem({source_acc.balance}), Destino({dest_acc.balance})")
                    else:
                        tx.transfer_status = 'REVIEW'

                tx.save()
                logging.info(f"Transação {transaction_id} processada. Novo status: {tx.transfer_status}")

        except Transaction.DoesNotExist:
            logging.error(f"Transação {transaction_id} não encontrada no banco de dados.")
        except Exception as e:
            logging.error(f"Erro crítico no processamento: {e}")
            raise e