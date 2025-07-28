from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from .models import (
    CoffeePurchase, CoffeeSale, CoffeeInventory,
    Customer, CustomerAccount, MillingProcess, MillingTransaction
)
from decimal import Decimal


@receiver(post_save, sender=Customer)
def handle_customer_account(sender, instance, created, **kwargs):
    """
    Creates or updates a CustomerAccount when a Customer is saved.
    """
    if created:
        CustomerAccount.objects.create(customer=instance)
    else:
        # Ensure account exists even if created=False (e.g., during migrations)
        if not hasattr(instance, 'account'):
            CustomerAccount.objects.create(customer=instance)
        instance.account.save()


@receiver(post_save, sender=MillingProcess)
def update_account_after_milling(sender, instance, created, **kwargs):
    """
    Update customer account balance when a milling process is completed.
    Only processes new completions to avoid duplicate transactions.
    """
    if instance.status == MillingProcess.COMPLETED:
        # Check if this is a status change to completed
        if not created:
            old_instance = MillingProcess.objects.get(pk=instance.pk)
            if old_instance.status == instance.status:
                return  # Status didn't change to completed

        with transaction.atomic():
            account = instance.customer.account
            milling_cost = instance.milling_cost
            
            # Check if transaction already exists
            if not MillingTransaction.objects.filter(milling_process=instance).exists():
                MillingTransaction.objects.create(
                    account=account,
                    amount=milling_cost,
                    transaction_type=MillingTransaction.DEBIT,
                    reference=f"Milling #{instance.id}",
                    created_by=instance.created_by,
                    milling_process=instance
                )


@receiver(pre_save, sender=MillingTransaction)
def validate_transaction_balance(sender, instance, **kwargs):
    """
    Prevent non-milling debit transactions that would make the balance negative.
    Allow milling transactions to create negative balances (debt).
    """
    if (instance.transaction_type == MillingTransaction.DEBIT and
        not instance.milling_process and  # Only check for non-milling debits
        instance.amount > instance.account.balance):
        raise ValueError(
            f"Insufficient funds for this transaction. "
            f"Current balance: {instance.account.balance}, "
            f"Transaction amount: {instance.amount}"
        )


@receiver(post_save, sender=MillingTransaction)
def update_account_balance(sender, instance, created, **kwargs):
    """
    Update account balance when a transaction is created or updated.
    """
    if created:  # Only update for new transactions
        with transaction.atomic():
            account = instance.account
            if instance.transaction_type == MillingTransaction.DEBIT:
                account.balance -= Decimal(str(instance.amount))
            else:
                account.balance += Decimal(str(instance.amount))
            account.save()


@receiver(post_save, sender=CoffeePurchase)
def update_inventory_on_purchase(sender, instance, created, **kwargs):
    """
    Update inventory when a coffee purchase is made.
    Handles both new purchases and updates to existing ones.
    """
    if not created and not instance.assessment:
        return 

    with transaction.atomic():
        # Get or create inventory record
        inventory, created = CoffeeInventory.objects.get_or_create(
            coffee_category=instance.coffee_category,
            coffee_type=instance.coffee_type.upper(),
            defaults={
                'quantity': 0,
                'unit': 'kg',
                'average_unit_cost': 0,
                'current_value': 0
            }
        )

        # Calculate the effective price per kg
        if instance.assessment and instance.assessment.final_price not in [None, "REJECT"]:
            price_per_kg = Decimal(str(instance.assessment.final_price))
        else:
            price_per_kg = Decimal(str(instance.reference_price))

        total_cost = Decimal(str(instance.quantity)) * price_per_kg

        # Update the inventory
        inventory.update_inventory(
            quantity_change=Decimal(str(instance.quantity)),
            cost_change=total_cost
        )


@receiver(post_delete, sender=CoffeePurchase)
def revert_inventory_on_purchase_delete(sender, instance, **kwargs):
    """
    Revert inventory changes when a coffee purchase is deleted.
    """
    with transaction.atomic():
        try:
            inventory = CoffeeInventory.objects.get(
                coffee_category=instance.coffee_category,
                coffee_type=instance.coffee_type.upper()
            )
            
            # Calculate the original cost
            if instance.assessment and instance.assessment.final_price not in [None, "REJECT"]:
                price_per_kg = Decimal(str(instance.assessment.final_price))
            else:
                price_per_kg = Decimal(str(instance.reference_price))
            
            total_cost = Decimal(str(instance.quantity)) * price_per_kg
            
            inventory.update_inventory(
                quantity_change=-Decimal(str(instance.quantity)),
                cost_change=-total_cost
            )
        except CoffeeInventory.DoesNotExist:
            pass


@receiver(post_save, sender=CoffeeSale)
def update_inventory_on_sale(sender, instance, created, **kwargs):
    """
    Update inventory when a coffee sale is made.
    """
    if not created:
        return

    with transaction.atomic():
        try:
            inventory = CoffeeInventory.objects.get(
                coffee_category=instance.coffee_category,
                coffee_type=instance.coffee_type.upper()
            )

            if not inventory.has_sufficient_stock(instance.quantity):
                raise ValueError(
                    f"Insufficient stock to sell {instance.quantity}kg. "
                    f"Available: {inventory.quantity}{inventory.unit}"
                )

            # For sales, we only decrease quantity (cost_change=0)
            inventory.update_inventory(
                quantity_change=-Decimal(str(instance.quantity)),
                cost_change=0
            )
        except CoffeeInventory.DoesNotExist:
            raise ValueError(
                f"Cannot sell {instance.get_coffee_type_display()} {instance.get_coffee_category_display()} - "
                f"no inventory available"
            )


@receiver(post_delete, sender=CoffeeSale)
def revert_inventory_on_sale_delete(sender, instance, **kwargs):
    """
    Revert inventory changes when a coffee sale is deleted.
    """
    with transaction.atomic():
        try:
            inventory = CoffeeInventory.objects.get(
                coffee_category=instance.coffee_category,
                coffee_type=instance.coffee_type.upper()
            )
            inventory.update_inventory(
                quantity_change=Decimal(str(instance.quantity)),
                cost_change=0
            )
        except CoffeeInventory.DoesNotExist:
            pass