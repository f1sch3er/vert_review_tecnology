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
        consumer = KafkaConsumer(
            'transactions',
            bootstrap_servers=['localhost:9092'],
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
            except Transaction.DoesNotExist:
                    logging.exception(e)
                
    
    def process_transaction(self, payload):
        transaction_id = payload.get('transaction_id')

        if payload.get('status') == 'SETTLED':
            return
        
        if payload.get('idempotency_key') is None:
            raise Exception("Idempotency key is missing")

        with transaction.atomic():
            transaction_selected = Transaction.objects.select_for_update().get(id=transaction_id)
            
            account_related = Account.objects.select_for_update().get(account_number=transaction_selected.to_account.account_number)

            if account_related is None:
                raise Exception("Account not found")

            if transaction_selected.idempotency_key != payload.get('idempotency_key'):
                raise Exception("Idempotency mismatch")
            
            if account_related.status == 'FROZEN':
                transaction_selected.status = 'REJECTED'

            if account_related.balance < transaction_selected.amount:
                transaction_selected.status = 'REJECTED'
                

            if account_related.status == 'ACTIVE':  
                if transaction_selected.amount <= 1000:
                    transaction_selected.status = 'SETTLED'
                elif transaction_selected.amount > 1000:
                    transaction_selected.status = 'REVIEW'
                

                
                transaction_selected.save()