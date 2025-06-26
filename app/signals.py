# signals.py
from django.db import transaction
from django.db.models.signals import post_save, post_delete
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import CoffeePurchase, CoffeeSale, CoffeeInventory
from .models import Customer, CustomerAccount, MillingProcess, MillingTransaction


@receiver(post_save, sender=Customer)
def create_customer_account(sender, instance, created, **kwargs):
    """
    Creates a CustomerAccount automatically when a new Customer is created.
    """
    if created:
        CustomerAccount.objects.create(customer=instance)

@receiver(post_save, sender=Customer)
def save_customer_account(sender, instance, **kwargs):
    """
    Saves the CustomerAccount when the Customer is saved.
    """
    instance.account.save()


@receiver(post_save, sender=MillingProcess)
def update_account_after_milling(sender, instance, created, **kwargs):
    """
    Update customer account balance when a milling process is completed.
    """
    if instance.status == MillingProcess.COMPLETED:
        with transaction.atomic():
            account = instance.customer.account
            milling_cost = instance.milling_cost
            # Create a transaction record for the milling cost
            MillingTransaction.objects.create(
                account=account,
                amount=milling_cost,
                transaction_type=MillingTransaction.DEBIT,
                reference=f"Milling #{instance.id}",
                created_by=instance.customer.created_by,
                milling_process=instance
            )
            # The Transaction's save() will update the account balance

@receiver(pre_save, sender=MillingTransaction)
@receiver(pre_save, sender=MillingTransaction)
def validate_transaction_balance(sender, instance, **kwargs):
    """
    Prevent non-milling debit transactions that would make the balance negative.
    Allow milling transactions to create negative balances (debt).
    """
    if (instance.transaction_type == MillingTransaction.DEBIT and
        instance.milling_process is None and  # Only check for non-milling debits
        instance.amount > instance.account.balance):
        raise ValueError("Insufficient funds for this transaction")
    

@receiver(post_save, sender=MillingTransaction)
def update_account_balance(sender, instance, created, **kwargs):
    """
    Update account balance when a transaction is created.
    """
    if created:  # Only update for new transactions
        with transaction.atomic():
            account = instance.account
            if instance.transaction_type == MillingTransaction.DEBIT:
                account.balance -= instance.amount
            else:
                account.balance += instance.amount
            account.save()


@receiver(post_save, sender=CoffeePurchase)
def update_inventory_on_purchase(sender, instance, created, **kwargs):
    """
    Update inventory when a coffee purchase is made
    """
    with transaction.atomic():
        # Get or create inventory record for this coffee type and category
        inventory, created = CoffeeInventory.objects.get_or_create(
            coffee_category=instance.coffee_category,
            coffee_type=instance.coffee_type.upper(),  # Ensure case matches
            defaults={
                'quantity': 0,
                'average_unit_cost': 0,
                'current_value': 0
            }
        )

        if created:
            # New inventory item - just add the full purchase
            quantity_change = instance.quantity
            cost_change = instance.total_cost
        else:
            # Existing inventory - calculate changes
            quantity_change = instance.quantity
            cost_change = instance.total_cost

        # Update the inventory
        inventory.update_inventory(
            quantity_change=quantity_change,
            cost_change=cost_change
        )


@receiver(post_delete, sender=CoffeePurchase)
def revert_inventory_on_purchase_delete(sender, instance, **kwargs):
    """
    Revert inventory changes when a coffee purchase is deleted
    """
    with transaction.atomic():
        try:
            inventory = CoffeeInventory.objects.get(
                coffee_category=instance.coffee_category,
                coffee_type=instance.coffee_type.upper()
            )
            inventory.update_inventory(
                quantity_change=-instance.quantity,
                cost_change=-instance.total_cost
            )
        except CoffeeInventory.DoesNotExist:
            pass  # No inventory to update


@receiver(post_save, sender=CoffeeSale)
def update_inventory_on_sale(sender, instance, created, **kwargs):
    """
    Update inventory when a coffee sale is made
    """
    with transaction.atomic():
        try:
            inventory = CoffeeInventory.objects.get(
                coffee_category=instance.coffee_category,
                coffee_type=instance.coffee_type.upper()
            )

            # For sales, we only decrease quantity (cost_change=0)
            inventory.update_inventory(
                quantity_change=-instance.quantity,
                cost_change=0
            )
        except CoffeeInventory.DoesNotExist:
            raise ValueError(
                f"Cannot sell {instance.get_coffee_type_display()} {instance.get_coffee_category_display()} - "
                f"no inventory available for this type and category"
            )


@receiver(post_delete, sender=CoffeeSale)
def revert_inventory_on_sale_delete(sender, instance, **kwargs):
    """
    Revert inventory changes when a coffee sale is deleted
    """
    with transaction.atomic():
        try:
            inventory = CoffeeInventory.objects.get(
                coffee_category=instance.coffee_category,
                coffee_type=instance.coffee_type.upper()
            )
            inventory.update_inventory(
                quantity_change=instance.quantity,
                cost_change=0
            )
        except CoffeeInventory.DoesNotExist:
            pass  # No inventory to update