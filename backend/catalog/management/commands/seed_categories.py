from django.core.management.base import BaseCommand
from django.utils.text import slugify

from catalog.category_data import CATEGORY_DATA
from catalog.models import Category, SubCategory


class Command(BaseCommand):
    help = "Create the FreshBasket main categories and their subcategories."

    def handle(self, *args, **options):
        created_categories = 0
        existing_categories = 0
        created_subcategories = 0
        existing_subcategories = 0

        for item in CATEGORY_DATA:
            category, created = Category.objects.get_or_create(
                name=item["name"],
                defaults={
                    "slug": slugify(item["name"]),
                    "description": item["description"],
                    "image_url": item["image_url"],
                },
            )
            if created:
                created_categories += 1
            else:
                existing_categories += 1

            for name in item["subcategories"]:
                _, created = SubCategory.objects.get_or_create(
                    category=category,
                    name=name,
                    defaults={
                        "slug": slugify(name),
                        "description": f"{name} in {category.name}.",
                        "image_url": category.image_url,
                    },
                )
                if created:
                    created_subcategories += 1
                else:
                    existing_subcategories += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Category seeding complete: "
                f"{created_categories} categories created, "
                f"{existing_categories} already present; "
                f"{created_subcategories} subcategories created, "
                f"{existing_subcategories} already present."
            )
        )
