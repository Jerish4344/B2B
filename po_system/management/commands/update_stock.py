from django.core.management.base import BaseCommand
from po_system.models import Stock, Product, Shop
import random

class Command(BaseCommand):
    help = 'Update stock levels for all products (simulate end-of-day closing)'
    
    def handle(self, *args, **options):
        products = Product.objects.all()
        shops = Shop.objects.all()
        
        for product in products:
            for shop in shops:
                stock, created = Stock.objects.get_or_create(
                    product=product,
                    shop=shop,
                    defaults={'quantity': random.randint(10, 200)}
                )
                if not created:
                    # Simulate sales reduction
                    stock.quantity = max(0, stock.quantity - random.randint(0, 20))
                    stock.save()
        
        self.stdout.write(
            self.style.SUCCESS('Successfully updated stock levels')
        )