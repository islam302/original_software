# from django.db.models.signals import m2m_changed
# from django.dispatch import receiver

# from products.models import Product


# @receiver(m2m_changed, sender=Product.options_products.through)
# def options_products_changed(
#     sender, instance, action, reverse, model, pk_set, **kwargs
# ):
#     print("Action:", action)
#     print("Reverse:", reverse)
#     print("Instance:", instance)
#     print("Instance id:", instance.id)
#     print("PK set:", pk_set)

#     if action == "post_add" or action == "post_remove":
#         has_options = Product.options_products.through.objects.filter(
#             from_product=instance
#         ).exists()
#         for pk in pk_set:
#             product = Product.objects.get(pk=pk)
#             product.is_option_product = Product.options_products.through.objects.filter(
#                 from_product=instance, to_product=pk
#             ).exists()
#             product.save()

#         instance.has_options = has_options
#         instance.save()
