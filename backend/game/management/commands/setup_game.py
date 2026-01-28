from django.core.management.base import BaseCommand
from game.models import Round

class Command(BaseCommand):
    help = 'Setup initial game rounds'
    
    def handle(self, *args, **kwargs):
        rounds_data = [
            (1, 'Round 1 - Stranger Things'),
            (2, 'Round 2 - One Piece'),
            (3, 'Round 3 - Squid Game'),
        ]
        
        for number, name in rounds_data:
            round_obj, created = Round.objects.get_or_create(
                round_number=number,
                defaults={'duration_minutes': 60, 'is_open': False}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'✅ Created {name}'))
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ {name} already exists'))
        
        self.stdout.write(self.style.SUCCESS('✅ Game setup complete!'))